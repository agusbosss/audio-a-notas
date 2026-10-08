"""Línea de comandos: `uv run notas <comando>`."""

import argparse
import sys
from pathlib import Path

from . import audio as audio_
from . import config as config_
from .diagnostico import diagnosticar
from .procesar import generar_nota, leer_brief, pendientes, preparar, procesar
from .transcripcion import Transcripcion


def main() -> None:
    parser = argparse.ArgumentParser(prog="notas", description="Notas de voz → transcripción por hablante + nota.")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("procesar", help="procesa una grabación; si se pasan varios audios, son partes de la misma")
    p.add_argument("audios", type=Path, nargs="+", help="uno o más audios, en el orden en que se grabaron")
    p.add_argument("--tipo", choices=config_.TIPOS, required=True)
    p.add_argument("--materia", help="nombre de la materia; usa vocabulario/<materia>.txt si existe")
    p.add_argument("--brief", help="contexto previo sobre la grabación: el texto directo o la ruta a un archivo")
    p.add_argument("--hablantes", type=int, help="cantidad de hablantes, si se sabe (mejora la diarización)")
    p.add_argument("--latex", action="store_true", help="matemática en LaTeX en vez de Unicode")

    sub.add_parser("pendientes", help="procesa todo lo que haya en la carpeta de entrada de iCloud")
    sub.add_parser("preparar", help="crea las carpetas de entrada en iCloud Drive")
    sub.add_parser("diagnostico", help="revisa que esté todo instalado y configurado, sin gastar nada")

    r = sub.add_parser("resumir", help="rehace la nota desde una transcripción guardada, sin volver a transcribir")
    r.add_argument("transcripcion", type=Path, help="el .json de salida/transcripciones/")
    r.add_argument("--tipo", choices=config_.TIPOS, help="cambia el tipo de grabación")
    r.add_argument("--materia", help="cambia la materia")
    r.add_argument("--brief", help="cambia el contexto previo: el texto directo o la ruta a un archivo")
    r.add_argument("--latex", action=argparse.BooleanOptionalAction, help="matemática en LaTeX (--no-latex: Unicode)")

    args = parser.parse_args()
    config = config_.cargar()

    if args.comando == "procesar":
        # Con la hora de grabación de todas las partes, se ordenan por hora; si no, en el orden dado.
        horas = [audio_.hora_de_grabacion(a) for a in args.audios]
        audios = [a for _, a in sorted(zip(horas, args.audios))] if all(horas) else args.audios
        print("→ " + ", ".join(a.name for a in audios))
        ruta = procesar(audios, tipo=args.tipo, materia=args.materia, hablantes=args.hablantes,
                        brief=leer_brief(args.brief), latex=args.latex, config=config)
        print(f"  ✓ {ruta}")
    elif args.comando == "pendientes":
        pendientes(config)
    elif args.comando == "preparar":
        preparar(config)
    elif args.comando == "diagnostico":
        sys.exit(0 if diagnosticar(config) else 1)
    elif args.comando == "resumir":
        transcripcion = Transcripcion.cargar(args.transcripcion)
        if args.tipo:
            transcripcion.origen["tipo"] = args.tipo
        if args.materia:
            transcripcion.origen["materia"] = args.materia
        if args.brief:
            transcripcion.origen["brief"] = leer_brief(args.brief)
        if args.latex is not None:
            transcripcion.origen["latex"] = args.latex
        transcripcion.guardar(args.transcripcion)
        print(f"  ✓ {generar_nota(transcripcion, config=config)}")
