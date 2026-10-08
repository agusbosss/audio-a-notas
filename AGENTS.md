# audio-a-notas: guía para asistentes de IA

Este archivo es para la IA (Claude Code, Codex, Cursor o la que sea) que alguien abrió en esta
carpeta. Tiene todo lo necesario para instalar el proyecto, usarlo día a día y adaptarlo a la
persona. El [README.md](README.md) es la versión para humanos.

## Qué es

Convierte grabaciones de Notas de Voz del iPhone (clases, charlas, reuniones, conversaciones,
notas sueltas) en una nota en Markdown para consultar después:

- un índice con la hora y el minuto de cada tema;
- lo que se dijo, con citas textuales y su marca de tiempo;
- la transcripción completa, separada por hablante.

Es una alternativa casi gratis a la función de Notion AI que hace lo mismo.

```
audio(s) .m4a ──► AssemblyAI (transcripción + quién habla) ──► Claude Code `claude -p` ──► nota .md
                   ~USD 0,23 por hora, con crédito gratis       con la suscripción de Claude
```

## Cómo trabajar con el usuario

**Suponé que no sabe programar.** Muchos llegan acá porque un amigo les pasó el link.

- Corré vos los comandos y editá vos los archivos. No le pidas que abra una terminal ni que
  edite un `.env` si lo podés hacer vos.
- Explicá en palabras simples qué estás haciendo y por qué, sin jerga.
- Las únicas cosas que tiene que hacer el usuario: crear la cuenta de AssemblyAI y pasarte la
  clave, iniciar sesión en Claude Code, y lo que pase en el iPhone.
- Antes de algo que no se puede deshacer (borrar audios, pisar notas), preguntá.
- Respondé en el idioma del usuario. Todo lo que escribas en castellano, con ortografía perfecta.

## Primera vez: puesta en marcha

Hacelo en este orden. Si ya hay `.env` y `perfil.md`, el proyecto ya está configurado: corré
`uv run notas diagnostico` y seguí desde lo que falte.

### 1. Requisitos

- **Una Mac.** Es lo único probado. Unir grabaciones en partes usa `afconvert` y la carpeta de
  entrada usa iCloud Drive, ambos de macOS. En Windows o Linux quizá funcione `notas procesar`
  con un audio suelto, pero no está probado: avisale al usuario.
- **Claude Code** instalado y con sesión iniciada (`claude` en la terminal). Arma las notas con
  la suscripción de Claude (Pro o superior), sin pagar API. Hace falta aunque el asistente que
  esté leyendo esto sea otro. Instalación: https://claude.com/claude-code
- **uv**, el gestor de Python. Si `uv --version` falla:
  `curl -LsSf https://astral.sh/uv/install.sh | sh` y abrir una terminal nueva. No hace falta
  instalar Python: uv baja el que corresponde (3.12).

### 2. Instalar

```sh
uv sync
```

### 3. AssemblyAI

1. El usuario crea una cuenta en https://www.assemblyai.com (al armar esto, daba USD 50 de
   crédito gratis sin tarjeta, unas 200 horas de audio: verificalo, cambia).
2. Copia la clave desde el panel (*API Keys*) y te la pasa.
3. Vos copiás `.env.example` como `.env` y completás `ASSEMBLYAI_API_KEY`.

La clave es un secreto: no la muestres entera, no la escribas en otro archivo y nunca la subas
a git (`.env` ya está ignorado).

### 4. Perfil: la parte que más mejora las notas

Hacele una entrevista corta y escribí `perfil.md` a partir de [perfil.example.md](perfil.example.md).
Preguntas que sirven:

- ¿Qué vas a grabar? ¿Clases, charlas, reuniones de trabajo, conversaciones, ideas sueltas?
- ¿Qué estudiás o de qué trabajás? ¿Qué materias, con qué profesores?
- ¿Para qué vas a usar las notas? ¿Repasar para un examen, recordar qué se acordó, tener un
  archivo para dentro de años?
- ¿Cómo te gustan: cortas o detalladas? ¿Con preguntas para repasar?
- ¿Dónde querés guardarlas? (una carpeta, Obsidian, Notion copiando el `.md`)
- ¿Usás fórmulas? ¿Las leés en un programa que muestra LaTeX (Obsidian, Notion) o en texto plano?

Claude recibe `perfil.md` entero cada vez que arma una nota. No lo llenes de más: con lo que
contestó alcanza. La tabla «Dónde guardar las notas» es para vos, el asistente.

### 5. Vocabulario (opcional)

Si tiene materias o temas con términos técnicos o nombres propios, armá
`vocabulario/<Materia>.txt` con un término por línea (ver [vocabulario/README.md](vocabulario/README.md)).
Empezá con 20 o 30: nombres de profesores y autores, y los términos que seguro salgan mal.
Demasiados términos empeoran la transcripción.

### 6. Cómo van a llegar los audios a la Mac

Explicale las dos formas y que elija:

- **AirDrop a Descargas (la más simple).** Desde Notas de Voz: Compartir → **Opciones →
  Editable** → AirDrop a su Mac. Después te avisa («te pasé la clase de Historia») y vos la
  procesás (ver «Uso diario»).
- **Atajo de iOS + iCloud Drive.** Comparte al Atajo, que guarda el audio en una carpeta de
  iCloud según el tipo; después corre `uv run notas pendientes` (o se lo pide a la IA). Hay que
  armar el Atajo a mano: guialo con la sección «El Atajo del iPhone» del README y corré
  `uv run notas preparar` para crear las carpetas.

**«Editable» importa:** así llega el archivo original, con la hora real de la grabación. Sin
eso, la nota solo tiene minutos del audio y no la hora del reloj.

### 7. Probar

1. `uv run notas diagnostico`: tiene que terminar en «Listo para procesar».
2. Pedile una grabación corta (1 a 5 minutos) y procesala. Si no tiene ninguna, puede grabarse
   hablando un minuto.
3. Mostrale la nota y preguntale qué cambiaría. Ajustá el perfil o la plantilla.

## Uso diario

Cuando el usuario te pasa audios:

1. **Ubicalos.** Por AirDrop caen en `~/Downloads`. Si un nombre ya existía, macOS lo renombra
   («New Recording 5» pasa a «New Recording 6»): confirmá cuál es cuál si hay dudas.
2. **Preguntá lo que falte:** de qué se trata, qué tipo es y qué audios son partes de una misma
   grabación (por ejemplo, una clase cortada por un recreo).
3. **Armá un brief** de 3 a 6 líneas con lo que contó: de qué es, quién habla, qué le interesa.
   Sumá contexto de la carpeta de destino si lo hay (programa de la materia, notas anteriores).
4. **Procesá:**
   ```sh
   uv run notas procesar parte1.m4a parte2.m4a --tipo clase --materia "Historia" \
       --brief "Clase 4: la Revolución de Mayo. Me interesan las causas."
   ```
   Opciones: `--hablantes N` si se sabe cuántos hablan; `--latex` si el destino muestra LaTeX.
   Una clase de 2 horas tarda unos minutos en transcribirse y otros tantos en armar la nota.
5. **Mové la nota** de `salida/` a la carpeta que diga `perfil.md`. Si no dice, preguntá y
   anotalo ahí para la próxima.
6. **Archivá los audios** en `audios/` (dentro del proyecto, fuera de git) con un nombre que diga
   qué son: `audios/<categoría>/[<materia>/]<AAAA-MM-DD HHMM> <descripción>[ (parte N de M)].m4a`.
   Si vino en partes, archivá también el audio unido de `salida/audios/` como
   `<AAAA-MM-DD> <descripción> (completa, minutos de la nota).m4a`, porque los minutos de la nota
   se refieren a ese audio. Después actualizá los nombres de las partes en la nota y en el `.json`.
   No borres audios sin preguntar.
7. **Dejá Descargas limpio**, sin tocar nada que no sea de este flujo.

Para rehacer una nota (otro tipo, otro brief, o después de cambiar la plantilla o el perfil) no
hace falta volver a transcribir ni pagar:

```sh
uv run notas resumir salida/transcripciones/<archivo>.json --tipo charla --brief "…"
```

## Comandos

| Comando | Qué hace |
|---|---|
| `uv run notas diagnostico` | Revisa la instalación y la clave, sin gastar nada |
| `uv run notas procesar <audios…> --tipo T [--materia M] [--brief B] [--hablantes N] [--latex]` | Procesa una grabación; varios audios son partes de la misma |
| `uv run notas resumir <json> [--tipo] [--materia] [--brief] [--latex/--no-latex]` | Rehace la nota desde la transcripción guardada (gratis) |
| `uv run notas pendientes` | Procesa todo lo que haya en la carpeta de iCloud del Atajo |
| `uv run notas preparar` | Crea las carpetas de entrada en iCloud Drive |

`--brief` acepta el texto o la ruta a un `.txt`. Tipos: `clase`, `charla`, `conversacion`, `nota`.

## Adaptarlo a cada persona

Ideas según quién lo use. Proponé las que encajen, no todas.

- **Tipos nuevos de grabación** (reunión de trabajo, entrevista, consulta médica, podcast,
  sesión de terapia, ensayo de banda). Hay que tocar tres lugares:
  1. `plantillas/<tipo>.md`: una línea que describa la grabación y después las secciones `##`
     de la nota, con lo que va en cada una. Copiá el estilo de las existentes.
  2. `TIPOS` en [src/notas_de_voz/config.py](src/notas_de_voz/config.py).
  3. `NOMBRE_TIPO` en [src/notas_de_voz/nota.py](src/notas_de_voz/nota.py) (el nombre con tildes).
- **Cambiar qué trae cada nota:** editar `plantillas/<tipo>.md`. Por ejemplo, sumar «Preguntas
  para repasar» a `clase.md`, o «Próximos pasos con fecha» a `conversacion.md`.
- **Estudiantes:** vocabulario por materia; `--latex` si leen en Obsidian o Notion; una sección
  de preguntas de autoevaluación con las respuestas plegadas.
- **Trabajo:** un tipo `reunion` con decisiones, responsables y fechas; las notas a la carpeta
  del proyecto o del cliente.
- **Otro idioma:** cambiar `language_code` en
  [src/notas_de_voz/motores/assemblyai.py](src/notas_de_voz/motores/assemblyai.py) (por ejemplo
  `en`) y el idioma del prompt en [src/notas_de_voz/resumen.py](src/notas_de_voz/resumen.py).
- **Modelo de Claude:** `CLAUDE_MODELO` en `.env` (por ejemplo `sonnet`, más rápido; vacío usa
  el de Claude Code).
- **Notion u Obsidian:** la nota es Markdown común. Obsidian: apuntar el destino a una carpeta
  del vault. Notion: importar el `.md`, o sumar la API (ver «Pendientes»).
- **Otro motor de transcripción** (ElevenLabs, Deepgram, uno local con Whisper): escribir
  `src/notas_de_voz/motores/<motor>.py` con una función `transcribir()` como la de
  `assemblyai.py`, registrarla en `motores/__init__.py` y poner `MOTOR=<motor>` en `.env`.
  Comparativa de motores en [docs/investigacion.md](docs/investigacion.md).

Al adaptar, no cambies el formato de las marcas de tiempo ni la estructura de bloques que pide
`resumen.py` (`<hablantes>`, `<extraccion>`, `<titulo>`, `<nota>`): el código los lee.

## Costos y privacidad

- **AssemblyAI:** ~USD 0,23 por hora de audio; el crédito inicial alcanza para mucho. Una
  transcripción se paga una sola vez: queda guardada en `salida/transcripciones/` y se reusa.
- **Claude:** usa la suscripción de Claude Code; no hay costo extra por nota, pero consume del
  límite de uso. Una clase de 2 horas son unos 30 a 40 mil tokens.
- **Privacidad:** el audio pasa por AssemblyAI y el texto, por Claude. Para conversaciones
  privadas, que el usuario lo sepa y decida.

## Qué es personal y no se sube a git

Ya está en `.gitignore`. No lo saques ni lo agregues a un commit:

| Archivo | Qué es |
|---|---|
| `.env` | La clave de AssemblyAI |
| `perfil.md` | Quién es el usuario y dónde van sus notas |
| `CLAUDE.local.md` | Notas privadas para Claude Code |
| `vocabulario/*.txt` | Vocabularios propios (menos `ejemplo.txt`) |
| `salida/` | Notas, transcripciones y audios unidos |
| `audios/` | El archivo de grabaciones originales |

## Cómo está hecho

| Archivo | Qué hace |
|---|---|
| [src/notas_de_voz/cli.py](src/notas_de_voz/cli.py) | Los comandos |
| [src/notas_de_voz/procesar.py](src/notas_de_voz/procesar.py) | El recorrido completo, la carpeta de entrada, `procesados/` y `errores/` |
| [src/notas_de_voz/audio.py](src/notas_de_voz/audio.py) | Hora real de grabación y unión de partes con `afconvert` |
| [src/notas_de_voz/motores/](src/notas_de_voz/motores/) | Motores de transcripción intercambiables (hoy, AssemblyAI) |
| [src/notas_de_voz/transcripcion.py](src/notas_de_voz/transcripcion.py) | Formato común de la transcripción y marcas `[hora · minuto]` |
| [src/notas_de_voz/resumen.py](src/notas_de_voz/resumen.py) | El prompt y la llamada a `claude -p` |
| [src/notas_de_voz/nota.py](src/notas_de_voz/nota.py) | El Markdown final |
| [src/notas_de_voz/diagnostico.py](src/notas_de_voz/diagnostico.py) | `notas diagnostico` |
| [plantillas/](plantillas/) | Qué secciones lleva la nota de cada tipo |
| [docs/](docs/) | Investigación: [idea](docs/idea.md), [motores y arquitectura](docs/investigacion.md), [cómo armar las notas](docs/notas-resumen.md) |

Entorno: Python 3.12 con `uv`. Dependencias: `httpx` y `mutagen`. No hace falta ffmpeg ni
Homebrew mientras el motor sea una API, que acepta `.m4a` directo.

## Decisiones técnicas y lo aprendido

Leelo antes de cambiar algo de esto:

- **Nube y no local.** Con ruido y con varias voces, las APIs comerciales diarizan mejor que
  Whisper + pyannote local, y cuestan centavos. Un motor local se puede sumar como alternativa.
- **El prompt** sigue [docs/notas-resumen.md](docs/notas-resumen.md): transcripción arriba en
  XML, instrucciones al final, y una extracción tipada de momentos importantes antes de redactar
  (reduce omisiones e invenciones). La nota prioriza fidelidad, marcas de tiempo y citas textuales.
- **`claude -p` se corre desde una carpeta temporal**, para que no cargue el `CLAUDE.md` de este
  proyecto como contexto, y sin herramientas.
- **La hora real de grabación:** al compartir desde Notas de Voz sin más, el `.m4a` es una
  exportación nueva y su átomo `mvhd` tiene la hora de exportación. Compartiendo como
  **Editable** llega el original: trae la etiqueta `voice-memo-uuid` y su `mvhd` es la hora de
  inicio. Con eso cada marca es `[hora del reloj · minuto del audio]` y las partes se ordenan por hora.
- **Grabaciones en partes:** se unen en un solo audio antes de transcribir. Así la diarización es
  consistente (el profesor tiene la misma etiqueta en todas las partes) y los minutos corren de
  corrido. Cada parte conserva su hora de inicio, así que la hora sigue siendo exacta después de
  un recreo.
- **Oraciones, no turnos:** si AssemblyAI detecta un solo hablante, devuelve un único turno
  (`utterance`) con una sola marca de tiempo para toda la clase. Por eso la transcripción se arma
  con `/transcript/{id}/sentences`, agrupando oraciones del mismo hablante en bloques de hasta 40 s.
  `motores.assemblyai.recuperar(id)` rearma una transcripción vieja sin volver a pagar.
- **Problemas conocidos:** en charlas, las preguntas del público a veces quedan con la etiqueta de
  un orador; los nombres propios salen mal transcriptos (el vocabulario y el resumen lo corrigen
  en parte).

## Pendientes e ideas

- Sin verificar: si Notas de Voz deja compartir varias grabaciones juntas al Atajo. Si no, las
  partes se pasan por `notas procesar a b c`.
- Mandar la nota a Notion por API (funciona en el plan gratis; `POST /v1/pages` acepta Markdown).
- Correr `notas pendientes` solo, con `launchd`.
- Etapas 2 a 4 de [docs/notas-resumen.md](docs/notas-resumen.md): base de conocimiento por
  materia, paso de verificación de citas y aprender de las correcciones del usuario.
