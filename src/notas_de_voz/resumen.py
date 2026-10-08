"""Nota con Claude Code (`claude -p`), usando la suscripción en vez de la API.

Estructura del pedido (ver docs/notas-resumen.md):
- la transcripción arriba y las instrucciones al final, cada parte en su etiqueta XML;
- antes de redactar, el modelo extrae los momentos importantes con su minuto (extraer primero,
  redactar después), y la nota se arma a partir de esa extracción.
"""

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass

from .config import PERFIL, PLANTILLAS, Config
from .transcripcion import Transcripcion, formatear_tiempo

SISTEMA = """\
Convertís la transcripción automática de una grabación hecha con un celular (clases, charlas, \
seminarios, reuniones, conversaciones, notas de voz sueltas), en castellano, en una nota en \
Markdown.

Para qué sirve la nota, salvo que el perfil del usuario diga otra cosa: es un archivo para \
consultar meses o años después: recuperar un detalle que se escapó, ver cómo lo dijo \
exactamente el profesor o el orador, o recordar qué se dijo en una charla. Por eso importan, en \
este orden:
1. Fidelidad: nada que no esté en el audio. Si algo no se entiende, decilo.
2. Precisión para ubicar: cada idea con su marca de tiempo, copiada tal cual de la \
transcripción. Puede ser [hora · minuto] (por ejemplo [09:47 · 12:13]: la hora del reloj en \
que se dijo y el minuto del audio) o solo [minuto] si no se conoce la hora. Siempre incluí la \
hora cuando esté: sirve para cruzar la nota con lo que el usuario anotó a mano durante la grabación.
3. Las palabras exactas: citas textuales de las frases clave, copiadas literalmente de la \
transcripción entre comillas «», con su minuto. Nunca presentes una paráfrasis como cita.
4. Que se entienda sola dentro de años, sin recordar la grabación: contexto, quién habló y \
de qué se estaba hablando.

Sobre la transcripción:
- Los hablantes tienen etiquetas genéricas (A, B, C...) de un motor de diarización que a veces \
se equivoca: por ejemplo, preguntas del público atribuidas a un orador.
- Hay errores de reconocimiento, sobre todo en nombres propios y términos técnicos. Corregilos \
en la nota solo cuando el contexto o el vocabulario dejan claro cuál era el término; si no, \
dejalo como está y marcalo con [¿?].
- Si la grabación está en varias partes, aparecen separadores «--- Parte N ---»: es una sola \
clase o charla grabada en fragmentos. Tratala como una unidad y no menciones las partes salvo \
que sirva para ubicar algo.

Estilo: el castellano de la grabación (si es rioplatense, rioplatense), con ortografía perfecta. {matematica}"""

MATEMATICA = {
    "unicode": "Matemática en Unicode (α, ≥, √, Σ, x̄, Δ, ∂), nunca LaTeX.",
    "latex": "Matemática en LaTeX: $...$ en línea y $$...$$ en bloque, con variables y subíndices "
             "en LaTeX (la nota se lee en un visor que lo renderiza). Dentro de las citas textuales, "
             "respetá las palabras tal como se dijeron.",
}

INSTRUCCIONES = """\
Respondé con estos cuatro bloques, en este orden y sin nada fuera de ellos:

<hablantes>
Un objeto JSON que asigna a cada etiqueta un nombre si se menciona en el audio, o un rol \
inferido por el contexto. Cada valor va antes de cada línea de la transcripción, así que tiene \
que ser corto: de una a tres palabras, sin paréntesis ni aclaraciones (por ejemplo \
{"A": "Profesora", "B": "Martín, invitado"}). Dejá afuera las etiquetas de las que no se \
pueda inferir nada.
</hablantes>

<extraccion>
Recorré la transcripción completa, de principio a fin sin saltear el medio, y listá los \
momentos importantes, uno por línea, con el formato:
[marca de tiempo] tipo · quién · qué se dijo (con las palabras textuales si son relevantes)
Tipos: afirmación, ejemplo, pregunta→respuesta, énfasis (lo que se repite o se marca como \
importante), desacuerdo, anécdota, dato, referencia (autores, libros, papers, empresas), \
aviso. Este bloque es tu borrador de trabajo: no se muestra.
</extraccion>

<titulo>
Un título corto y descriptivo, sin fecha.
</titulo>

<nota>
La nota en Markdown, armada a partir de la extracción y siguiendo la plantilla. Empezá \
directamente con los encabezados ## de la plantilla. Omití las secciones que queden vacías.
</nota>"""


@dataclass
class Resumen:
    titulo: str
    hablantes: dict[str, str]
    cuerpo: str


def resumir(
    transcripcion: Transcripcion,
    *,
    tipo: str,
    config: Config,
    materia: str | None = None,
    vocabulario: list[str] | None = None,
    brief: str | None = None,
    latex: bool = False,
) -> Resumen:
    contexto = []
    if PERFIL.exists() and (perfil := PERFIL.read_text().strip()):
        contexto.append(f"<perfil>\nQuién es el usuario y para qué usa las notas:\n{perfil}\n</perfil>")
    if brief:
        contexto.append(f"<brief>\nLo que contó el usuario sobre esta grabación antes de procesarla:\n{brief}\n</brief>")
    if materia:
        contexto.append(f"<materia>{materia}</materia>")
    if vocabulario:
        contexto.append("<vocabulario>\nTérminos que pueden aparecer (sirven para corregir los mal transcriptos):\n"
                        + "\n".join(vocabulario) + "\n</vocabulario>")
    partes = transcripcion.origen.get("partes") or []
    duracion = formatear_tiempo(int(transcripcion.duracion_s * 1000))

    pedido = "\n\n".join([
        f'<transcripcion duracion="{duracion}" partes="{max(len(partes), 1)}" '
        f'hablantes_detectados="{len(transcripcion.hablantes())}">',
        transcripcion.como_texto(markdown=False),
        "</transcripcion>",
        *contexto,
        f"<plantilla tipo=\"{tipo}\">\n{(PLANTILLAS / f'{tipo}.md').read_text().strip()}\n</plantilla>",
        INSTRUCCIONES,
    ])

    comando = ["claude", "-p", "--output-format", "json", "--tools", "", "--no-session-persistence",
               "--system-prompt", SISTEMA.format(matematica=MATEMATICA["latex" if latex else "unicode"])]
    if config.claude_modelo:
        comando += ["--model", config.claude_modelo]

    # Se corre fuera del proyecto para que no cargue el CLAUDE.md de acá como contexto.
    with tempfile.TemporaryDirectory() as tmp:
        proceso = subprocess.run(comando, input=pedido, capture_output=True, text=True, cwd=tmp)
    if proceso.returncode != 0:
        raise RuntimeError(f"`claude -p` falló ({proceso.returncode}): {proceso.stderr.strip() or proceso.stdout.strip()}")

    salida = json.loads(proceso.stdout)
    if salida.get("is_error"):
        raise RuntimeError(f"`claude -p` devolvió un error: {salida.get('result')}")
    return _interpretar(salida["result"])


def _interpretar(texto: str) -> Resumen:
    def bloque(nombre: str) -> str | None:
        # La nota puede contener cualquier cosa, así que se toma hasta el último cierre.
        m = re.search(rf"<{nombre}>(.*)</{nombre}>" if nombre == "nota" else rf"<{nombre}>(.*?)</{nombre}>", texto, re.S)
        return m.group(1).strip() if m else None

    titulo, nota = bloque("titulo"), bloque("nota")
    if not titulo or not nota:
        raise ValueError(f"La respuesta de Claude no trae <titulo> y <nota>:\n{texto[:800]}")

    hablantes = {}
    if crudo := bloque("hablantes"):
        try:
            hablantes = {k: v for k, v in json.loads(crudo[crudo.find("{") : crudo.rfind("}") + 1]).items() if v}
        except ValueError:
            pass  # sin nombres la nota sirve igual: quedan las etiquetas A, B, C
    return Resumen(titulo=titulo, hablantes=hablantes, cuerpo=nota)
