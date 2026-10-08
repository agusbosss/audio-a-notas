"""AssemblyAI: sube el audio, pide la transcripción con diarización y espera el resultado.

Referencia: https://www.assemblyai.com/docs/api-reference/transcripts/submit
"""

import time
from pathlib import Path

import httpx

from ..config import Config
from ..transcripcion import Intervencion, Transcripcion

BASE = "https://api.assemblyai.com/v2"
ESPERA_ENTRE_CONSULTAS_S = 5
ESPERA_MAXIMA_S = 60 * 60
BLOQUE_MAXIMO_MS = 40_000


def transcribir(
    audio: Path,
    *,
    config: Config,
    hablantes: int | None,
    vocabulario: list[str],
) -> Transcripcion:
    if not config.assemblyai_api_key:
        raise RuntimeError("Falta ASSEMBLYAI_API_KEY en el archivo .env")

    with httpx.Client(base_url=BASE, headers={"authorization": config.assemblyai_api_key}, timeout=120) as cliente:
        with audio.open("rb") as f:
            subida = cliente.post("/upload", content=f)
        subida.raise_for_status()

        pedido = {
            "audio_url": subida.json()["upload_url"],
            "language_code": "es",
            "speaker_labels": True,
        }
        if hablantes:
            pedido["speakers_expected"] = hablantes
        if vocabulario:
            pedido["keyterms_prompt"] = vocabulario[:1000]

        envio = cliente.post("/transcript", json=pedido)
        envio.raise_for_status()
        id_ = envio.json()["id"]

        limite = time.monotonic() + ESPERA_MAXIMA_S
        while True:
            respuesta = cliente.get(f"/transcript/{id_}")
            respuesta.raise_for_status()
            datos = respuesta.json()
            if datos["status"] == "completed":
                break
            if datos["status"] == "error":
                raise RuntimeError(f"AssemblyAI devolvió un error: {datos.get('error')}")
            if time.monotonic() > limite:
                raise TimeoutError(f"AssemblyAI no terminó en {ESPERA_MAXIMA_S // 60} minutos (id {id_})")
            time.sleep(ESPERA_ENTRE_CONSULTAS_S)

        return _armar(cliente, datos)


def recuperar(id_: str, *, config: Config) -> Transcripcion:
    """Vuelve a armar una transcripción ya hecha a partir de su id, sin volver a pagarla."""
    with httpx.Client(base_url=BASE, headers={"authorization": config.assemblyai_api_key}, timeout=120) as cliente:
        respuesta = cliente.get(f"/transcript/{id_}")
        respuesta.raise_for_status()
        return _armar(cliente, respuesta.json())


def _armar(cliente: httpx.Client, datos: dict) -> Transcripcion:
    # Se arma por oraciones y no con los `utterances` (turnos de habla): si el motor detecta un solo
    # hablante, un turno es la clase entera, con una única marca de tiempo al principio.
    respuesta = cliente.get(f"/transcript/{datos['id']}/sentences")
    respuesta.raise_for_status()
    return Transcripcion(
        motor="assemblyai",
        duracion_s=float(datos.get("audio_duration") or 0),
        intervenciones=_agrupar(respuesta.json()["sentences"]),
        # Sin `words` ni `utterances`: ya están en `intervenciones` y en una clase larga pesan varios MB.
        crudo={k: v for k, v in datos.items() if k not in ("words", "utterances")},
    )


def _agrupar(oraciones: list[dict]) -> list[Intervencion]:
    """Junta oraciones seguidas del mismo hablante en bloques de hasta BLOQUE_MAXIMO_MS, para que haya
    una marca de tiempo cada medio minuto más o menos y se pueda ubicar cualquier momento."""
    bloques: list[Intervencion] = []
    for o in oraciones:
        hablante = o.get("speaker") or next((w["speaker"] for w in o.get("words", []) if w.get("speaker")), "A")
        ultimo = bloques[-1] if bloques else None
        if ultimo and ultimo.hablante == hablante and o["end"] - ultimo.inicio_ms <= BLOQUE_MAXIMO_MS:
            ultimo.texto += " " + o["text"]
            ultimo.fin_ms = o["end"]
        else:
            bloques.append(Intervencion(hablante=hablante, inicio_ms=o["start"], fin_ms=o["end"], texto=o["text"]))
    return bloques
