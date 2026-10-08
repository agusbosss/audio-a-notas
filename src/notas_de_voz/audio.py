"""Unir varias partes de una misma grabación en un solo audio.

Se transcribe el audio unido, no cada parte por separado: así el motor ve la clase entera, las
etiquetas de hablante son consistentes entre partes y los minutos corren de corrido.
Usa `afconvert`, que viene con macOS: no hace falta ffmpeg.
"""

import re
import struct
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mutagen.mp4 import MP4

FRECUENCIA = 16000  # la que usan internamente los motores de transcripción
SILENCIO_ENTRE_PARTES_S = 1.0


@dataclass
class Parte:
    archivo: str
    inicio_ms: int  # dónde empieza esta parte dentro del audio unido
    hora_inicio: str | None = None  # hora real en que se empezó a grabar (ISO), si se conoce


def hora_de_grabacion(audio: Path) -> datetime | None:
    """La hora real en que empezó la grabación, o None si el archivo no la trae.

    Solo la traen los archivos originales de Notas de Voz: los que se comparten como «Editable»
    (Opciones, al compartir). Se reconocen por la etiqueta `voice-memo-uuid`, y en ellos la fecha
    de creación del átomo `mvhd` es el inicio de la grabación. Al compartir sin «Editable», Notas
    de Voz genera un archivo nuevo y esa fecha pasa a ser la de exportación, que no sirve.
    """
    try:
        etiquetas = MP4(audio).tags or {}
    except Exception:
        return None
    if not any(k.endswith("voice-memo-uuid") for k in etiquetas):
        return None
    segundos = _creacion_mvhd(audio)
    if segundos is None:
        return None
    utc = datetime(1904, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=segundos)
    return utc.astimezone().replace(tzinfo=None)


def ordenar(audios: list[Path]) -> list[Path]:
    """Por hora de grabación si todas la traen; si no, orden natural por nombre («Clase 2» antes que «Clase 10»)."""
    horas = [hora_de_grabacion(a) for a in audios]
    if all(horas):
        return [a for _, a in sorted(zip(horas, audios))]
    return sorted(audios, key=lambda p: [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.stem)])


def unir(audios: list[Path], destino: Path) -> list[Parte]:
    """Une los audios en `destino` (m4a, mono, 16 kHz) en el orden dado y devuelve dónde empieza cada parte."""
    partes = []
    with tempfile.TemporaryDirectory() as tmp:
        wav_unido = Path(tmp) / "unido.wav"
        with wave.open(str(wav_unido), "wb") as salida:
            salida.setnchannels(1)
            salida.setsampwidth(2)
            salida.setframerate(FRECUENCIA)
            silencio = b"\x00\x00" * int(FRECUENCIA * SILENCIO_ENTRE_PARTES_S)

            for i, audio in enumerate(audios):
                if i:
                    salida.writeframes(silencio)
                partes.append(Parte(archivo=audio.name, inicio_ms=salida.getnframes() * 1000 // FRECUENCIA))
                wav = Path(tmp) / f"{i}.wav"
                _afconvert(audio, wav, "-f", "WAVE", "-d", f"LEI16@{FRECUENCIA}", "-c", "1")
                with wave.open(str(wav), "rb") as entrada:
                    salida.writeframes(entrada.readframes(entrada.getnframes()))
                wav.unlink()

        destino.parent.mkdir(parents=True, exist_ok=True)
        _afconvert(wav_unido, destino, "-f", "m4af", "-d", "aac", "-b", "48000")
    return partes


def _creacion_mvhd(audio: Path) -> int | None:
    """Segundos desde 1904 en el `mvhd` (dentro de `moov`), recorriendo los átomos sin leer el audio entero."""
    with audio.open("rb") as f:
        fin = audio.stat().st_size
        while f.tell() < fin:
            cabecera = f.read(8)
            if len(cabecera) < 8:
                return None
            tamano, tipo = struct.unpack(">I4s", cabecera)
            if tamano == 1:
                tamano = struct.unpack(">Q", f.read(8))[0] - 8
            if tipo == b"moov":
                datos = f.read(tamano - 8)
                i = datos.find(b"mvhd")
                if i == -1:
                    return None
                version = datos[i + 4]
                return struct.unpack(">Q" if version else ">I", datos[i + 8 : i + (16 if version else 12)])[0]
            f.seek(tamano - 8, 1)
    return None


def _afconvert(origen: Path, destino: Path, *opciones: str) -> None:
    proceso = subprocess.run(["afconvert", *opciones, str(origen), str(destino)], capture_output=True, text=True)
    if proceso.returncode != 0:
        raise RuntimeError(f"afconvert no pudo convertir {origen.name}: {proceso.stderr.strip()}")
