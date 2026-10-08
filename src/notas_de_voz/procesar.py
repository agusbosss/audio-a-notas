"""El recorrido completo: audio (o varias partes) → transcripción → nota en Markdown."""

import fcntl
import re
import shutil
import subprocess
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from mutagen.mp4 import MP4

from . import audio as audio_, motores, nota
from .config import TIPOS, VOCABULARIO, Config
from .resumen import resumir
from .transcripcion import Transcripcion

EXTENSIONES_AUDIO = {".m4a", ".mp3", ".wav", ".aac", ".mp4", ".caf", ".ogg", ".flac"}
SEGUNDOS_SIN_CAMBIOS = 30  # para no agarrar un archivo que iCloud todavía está bajando
ENVIO = re.compile(r"^\d{4}-\d{2}-\d{2}")  # carpeta que crea el Atajo por cada vez que se comparte


def procesar(
    audios: list[Path],
    *,
    tipo: str,
    config: Config,
    materia: str | None = None,
    hablantes: int | None = None,
    brief: str | None = None,
    latex: bool = False,
) -> Path:
    """Procesa una grabación, que puede venir en varias partes, en el orden dado. Devuelve la ruta de la nota.

    Si ya hay una transcripción guardada de esa grabación, la reusa y no vuelve a pagarla.
    """
    fecha = fecha_grabacion(audios[0])
    nombre = audios[0].stem if len(audios) == 1 else f"{audios[0].stem} (+{len(audios) - 1} partes)"
    base = f"{fecha:%Y-%m-%d %H%M} {nombre}"
    json_ = config.carpeta_salida / "transcripciones" / f"{base}.json"
    vocabulario = cargar_vocabulario(materia)

    if json_.exists():
        print(f"  Reuso la transcripción guardada: {json_.name}")
        transcripcion = Transcripcion.cargar(json_)
    else:
        if len(audios) == 1:
            a_transcribir, partes = audios[0], [audio_.Parte(archivo=audios[0].name, inicio_ms=0)]
        else:
            # El audio unido se guarda: los minutos de la nota se refieren a él.
            a_transcribir = config.carpeta_salida / "audios" / f"{base}.m4a"
            print(f"  Uniendo {len(audios)} partes: {', '.join(a.name for a in audios)}")
            partes = audio_.unir(audios, a_transcribir)
        print(f"  Transcribiendo con {config.motor}…")
        transcripcion = motores.transcribir(a_transcribir, config=config, hablantes=hablantes, vocabulario=vocabulario)
        for parte, audio in zip(partes, audios):
            hora = audio_.hora_de_grabacion(audio)
            parte.hora_inicio = hora.isoformat() if hora else None
        transcripcion.origen["partes"] = [asdict(p) for p in partes]
        json_.parent.mkdir(parents=True, exist_ok=True)

    # Se pisa siempre: si se reprocesa con otro tipo, materia o brief, la nota nueva lo respeta.
    transcripcion.origen.update(archivo=nombre, fecha=fecha.isoformat(), tipo=tipo, materia=materia, brief=brief,
                                latex=latex)
    transcripcion.guardar(json_)
    return generar_nota(transcripcion, config=config)


def generar_nota(transcripcion: Transcripcion, *, config: Config) -> Path:
    """Arma la nota a partir de una transcripción ya hecha. No vuelve a pagar la transcripción."""
    origen = transcripcion.origen
    if not transcripcion.intervenciones:
        raise RuntimeError("La transcripción está vacía: el audio no tiene voz reconocible.")

    print("  Armando la nota con Claude…")
    resumen = resumir(
        transcripcion,
        tipo=origen["tipo"],
        config=config,
        materia=origen.get("materia"),
        vocabulario=cargar_vocabulario(origen.get("materia")),
        brief=origen.get("brief"),
        latex=origen.get("latex", False),
    )

    fecha = datetime.fromisoformat(origen["fecha"])
    ruta = config.carpeta_salida / f"{fecha:%Y-%m-%d %H%M} {_nombre_archivo(resumen.titulo)}.md"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(nota.armar(transcripcion, resumen))
    return ruta


@dataclass
class Grabacion:
    """Lo que hay que mover a procesados/ o errores/ y lo que hay que procesar."""
    ruta: Path  # el audio suelto o la carpeta del envío
    audios: list[Path]
    tipo: str
    materia: str | None
    brief: str | None


def pendientes(config: Config) -> None:
    """Procesa todo lo que haya en la carpeta de entrada.

    Estructura esperada (la crea `notas preparar`; ver el README):

        Transcribir/<tipo>/[<materia>/]<envío>/   ← carpeta que crea el Atajo: todas las partes
                                                     de una grabación + brief.txt opcional
        Transcribir/<tipo>/[<materia>/]audio.m4a  ← audio suelto: una grabación de una parte,
                                                     con audio.txt opcional como brief
        Transcribir/procesados/  Transcribir/errores/

    Una carpeta es un envío si su nombre empieza con una fecha (AAAA-MM-DD); si no, es una materia.
    """
    entrada = config.carpeta_entrada
    if not entrada.exists():
        raise SystemExit(f"No existe la carpeta de entrada {entrada}. Corré `notas preparar`.")
    # Sin esto, cada audio terminaría en errores/ por un problema que no es del audio.
    if config.motor == "assemblyai" and not config.assemblyai_api_key:
        raise SystemExit("Falta ASSEMBLYAI_API_KEY en el archivo .env")

    config.carpeta_salida.mkdir(parents=True, exist_ok=True)
    with (config.carpeta_salida / ".lock").open("w") as candado:
        try:
            fcntl.flock(candado, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Ya hay otro procesamiento en curso.")
            return

        grabaciones = [g for tipo in TIPOS for g in _buscar(entrada / tipo, tipo, None)]
        if not grabaciones:
            print("No hay audios pendientes.")
        for g in grabaciones:
            relativa = g.ruta.relative_to(entrada)
            print(f"→ {relativa}" + (f" ({len(g.audios)} partes)" if len(g.audios) > 1 else ""))
            try:
                ruta = procesar(g.audios, tipo=g.tipo, materia=g.materia, brief=g.brief, config=config)
            except Exception:
                destino = _mover(g, entrada / "errores" / relativa)
                Path(f"{destino}.error.txt").write_text(traceback.format_exc())
                print(f"  ✗ Falló. Movido a errores/ con el detalle.\n{traceback.format_exc()}")
            else:
                _mover(g, entrada / "procesados" / relativa)
                print(f"  ✓ {ruta}")


def preparar(config: Config) -> None:
    for nombre in (*TIPOS, "procesados", "errores"):
        (config.carpeta_entrada / nombre).mkdir(parents=True, exist_ok=True)
    print(f"Carpetas listas en {config.carpeta_entrada}")


def fecha_grabacion(audio: Path) -> datetime:
    """La hora real de grabación si el archivo la trae (original de Notas de Voz, compartido como
    «Editable»); si no, la fecha guardada en las etiquetas o, en último caso, la de creación del
    archivo, que al compartir desde Notas de Voz es la de exportación.
    """
    if hora := audio_.hora_de_grabacion(audio):
        return hora
    try:
        dia = (MP4(audio).tags or {}).get("©day")
        if dia:
            return datetime.fromisoformat(dia[0]).astimezone().replace(tzinfo=None)
    except Exception:
        pass
    stat = audio.stat()
    return datetime.fromtimestamp(getattr(stat, "st_birthtime", stat.st_mtime))


def cargar_vocabulario(materia: str | None) -> list[str]:
    if not materia:
        return []
    archivo = VOCABULARIO / f"{materia}.txt"
    if not archivo.exists():
        return []
    return [t.strip() for t in archivo.read_text().splitlines() if t.strip() and not t.startswith("#")]


def leer_brief(valor: str | None) -> str | None:
    """`--brief` acepta el texto directo o la ruta a un archivo."""
    if not valor:
        return None
    try:
        ruta = Path(valor).expanduser()
        es_archivo = ruta.is_file()
    except OSError:  # un texto largo no puede ser una ruta
        es_archivo = False
    return (ruta.read_text() if es_archivo else valor).strip() or None


def _buscar(carpeta: Path, tipo: str, materia: str | None):
    if not carpeta.exists():
        return
    for item in sorted(carpeta.iterdir()):
        if item.is_dir() and ENVIO.match(item.name):
            audios = [a for a in item.iterdir() if _es_audio(a)]
            if audios and _listos(item.iterdir()):
                textos = sorted(item.glob("*.txt"))
                yield Grabacion(item, audio_.ordenar(audios), tipo, materia, _texto(textos[0]) if textos else None)
        elif item.is_dir() and materia is None:
            yield from _buscar(item, tipo, item.name)
        elif _es_audio(item) and _listos([item]):
            yield Grabacion(item, [item], tipo, materia, _texto(item.with_suffix(".txt")))


def _es_audio(ruta: Path) -> bool:
    return ruta.is_file() and ruta.suffix.lower() in EXTENSIONES_AUDIO


def _listos(archivos) -> bool:
    """Falso si algo todavía se está bajando de iCloud o se modificó hace muy poco."""
    listos = True
    for a in archivos:
        if a.name.startswith(".") and a.name.endswith(".icloud"):
            # Archivo que iCloud todavía no bajó: se pide la descarga y se procesa en la próxima pasada.
            subprocess.run(["brctl", "download", str(a.with_name(a.name[1:-7]))], capture_output=True)
            listos = False
        elif a.is_file() and time.time() - a.stat().st_mtime < SEGUNDOS_SIN_CAMBIOS:
            listos = False
    return listos


def _texto(ruta: Path) -> str | None:
    return (ruta.read_text().strip() or None) if ruta.is_file() else None


def _mover(g: Grabacion, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        destino = destino.with_name(f"{destino.stem} {datetime.now():%Y%m%d-%H%M%S}{destino.suffix}")
    brief_suelto = g.ruta.with_suffix(".txt") if g.ruta.is_file() else None
    shutil.move(g.ruta, destino)
    if brief_suelto and brief_suelto.exists():
        shutil.move(brief_suelto, destino.with_suffix(".txt"))
    return destino


def _nombre_archivo(titulo: str) -> str:
    return re.sub(r'[/\\:*?"<>|]', "-", titulo).strip()[:100]
