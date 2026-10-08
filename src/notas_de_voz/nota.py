"""Arma el Markdown final: encabezado, cuerpo de la nota y transcripción completa."""

from datetime import datetime

from .resumen import Resumen
from .transcripcion import Transcripcion, formatear_tiempo, marca_de_tiempo

NOMBRE_TIPO = {"clase": "Clase", "charla": "Charla", "conversacion": "Conversación", "nota": "Nota"}


def armar(transcripcion: Transcripcion, resumen: Resumen) -> str:
    origen = transcripcion.origen
    fecha = datetime.fromisoformat(origen["fecha"])
    partes = origen.get("partes") or [{"archivo": origen["archivo"], "inicio_ms": 0}]

    datos = [f"**Tipo:** {NOMBRE_TIPO[origen['tipo']]}"]
    if origen.get("materia"):
        datos.append(f"**Materia:** {origen['materia']}")
    if partes[0].get("hora_inicio"):
        ultima = partes[-1]
        fin = marca_de_tiempo(int(transcripcion.duracion_s * 1000), ultima).split(" · ")[0]
        horario = f"{fecha:%d/%m/%Y}, de {fecha:%H:%M} a {fin}"
    else:
        horario = f"{fecha:%d/%m/%Y %H:%M} (hora del archivo, no la de grabación)"
    datos += [
        f"**Fecha:** {horario}",
        f"**Duración:** {formatear_tiempo(int(transcripcion.duracion_s * 1000))}",
        f"**Audio:** {partes[0]['archivo']}" if len(partes) == 1 else f"**Audio:** {len(partes)} partes",
    ]
    encabezado = [f"# {resumen.titulo}", " · ".join(datos)]

    if origen.get("brief"):
        encabezado.append(f"**Contexto previo:** {origen['brief']}")
    if len(partes) > 1:
        encabezado.append("**Partes** (los minutos de la nota corren de corrido sobre el audio unido):\n\n" + "\n".join(
            f"{i}. {p['archivo']}: empieza en {marca_de_tiempo(p['inicio_ms'], p)}" for i, p in enumerate(partes, 1)
        ))

    # Las etiquetas del motor quedan entre paréntesis para poder detectar si el LLM se equivocó al asignarlas.
    nombres = {h: f"{n} ({h})" for h, n in resumen.hablantes.items()}

    return "\n\n".join([
        *encabezado,
        resumen.cuerpo,
        "## Transcripción",
        "<details>\n<summary>Transcripción completa</summary>",
        transcripcion.como_texto(nombres),
        "</details>",
    ]) + "\n"
