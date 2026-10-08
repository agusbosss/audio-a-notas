"""Motores de transcripción intercambiables.

Cada motor es una función `transcribir(audio, *, config, hablantes, vocabulario) -> Transcripcion`.
Para sumar uno (ElevenLabs, Gemini, WhisperX local) alcanza con escribir el módulo y
registrarlo en `MOTORES`.
"""

from collections.abc import Callable
from pathlib import Path

from ..config import Config
from ..transcripcion import Transcripcion
from . import assemblyai

Motor = Callable[..., Transcripcion]

MOTORES: dict[str, Motor] = {
    "assemblyai": assemblyai.transcribir,
}


def transcribir(
    audio: Path,
    *,
    config: Config,
    hablantes: int | None = None,
    vocabulario: list[str] | None = None,
) -> Transcripcion:
    if config.motor not in MOTORES:
        raise ValueError(f"Motor desconocido: {config.motor!r}. Disponibles: {', '.join(MOTORES)}")
    return MOTORES[config.motor](audio, config=config, hablantes=hablantes, vocabulario=vocabulario or [])
