"""Configuración: lee `.env` de la raíz del proyecto y expone las rutas y claves."""

import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PLANTILLAS = RAIZ / "plantillas"
VOCABULARIO = RAIZ / "vocabulario"
PERFIL = RAIZ / "perfil.md"  # quién es el usuario y para qué usa las notas; no se versiona

ICLOUD = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs"

TIPOS = ("clase", "charla", "conversacion", "nota")


def _leer_env(ruta: Path) -> dict[str, str]:
    """Parser mínimo de `.env`: líneas CLAVE=valor, ignora comentarios y comillas."""
    if not ruta.exists():
        return {}
    valores = {}
    for linea in ruta.read_text().splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        valores[clave.strip()] = valor.strip().strip("'\"")
    return valores


@dataclass(frozen=True)
class Config:
    motor: str
    assemblyai_api_key: str
    carpeta_entrada: Path
    carpeta_salida: Path
    claude_modelo: str


def cargar() -> Config:
    env = {**_leer_env(RAIZ / ".env"), **os.environ}
    return Config(
        motor=env.get("MOTOR", "assemblyai"),
        assemblyai_api_key=env.get("ASSEMBLYAI_API_KEY", ""),
        carpeta_entrada=_ruta(env.get("CARPETA_ENTRADA", ICLOUD / "Transcribir")),
        carpeta_salida=_ruta(env.get("CARPETA_SALIDA", RAIZ / "salida")),
        claude_modelo=env.get("CLAUDE_MODELO", ""),
    )


def _ruta(valor: str | Path) -> Path:
    """Las rutas relativas del `.env` se toman desde la raíz del proyecto, no desde donde se corre."""
    ruta = Path(valor).expanduser()
    return ruta if ruta.is_absolute() else RAIZ / ruta
