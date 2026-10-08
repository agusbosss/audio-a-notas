# audio-a-notas

Convierte las grabaciones de Notas de Voz del iPhone (clases, charlas, conversaciones, notas
sueltas) en una nota en Markdown para consultar después: índice con minutos, lo que se dijo con
citas textuales y la transcripción completa por hablante. La transcripción la hace AssemblyAI y
la nota, Claude Code (`claude -p`). Es una alternativa casi gratis a la función de Notion AI que
hace lo mismo: unos USD 0,23 por hora de audio, y AssemblyAI da crédito gratis al empezar.

## Empezar sin saber programar

Necesitás una **Mac**, un **iPhone** y una suscripción de **Claude** (Pro o superior).

1. Instalá [Claude Code](https://claude.com/claude-code) y bajá este repositorio (botón verde
   *Code* → *Download ZIP*, y descomprimilo donde quieras).
2. Abrí Claude Code en esa carpeta y escribile: **«Leé AGENTS.md y ayudame a configurar esto»**.
3. Te va a guiar: crear una cuenta gratis en AssemblyAI, contarle qué vas a grabar y para qué,
   y probar con un audio.

Después, para cada grabación: la mandás a la Mac por AirDrop (con **Opciones → Editable**) y le
decís a Claude de qué se trata. Sirve cualquier otra IA que pueda correr comandos en tu Mac
(Codex, Cursor): todas leen [AGENTS.md](AGENTS.md), aunque igual hace falta tener Claude Code.

```
iPhone: Notas de Voz → Compartir → Atajo "Transcribir" → iCloud Drive/Transcribir/<tipo>/<envío>/
Mac:    uv run notas pendientes → salida/<fecha> <título>.md
```

Cómo se arma la nota y por qué: [docs/notas-resumen.md](docs/notas-resumen.md).

## Puesta en marcha a mano

Requisitos: macOS, [uv](https://docs.astral.sh/uv/) y Claude Code con sesión iniciada.

1. Copiar `.env.example` a `.env` y completar `ASSEMBLYAI_API_KEY`.
2. Copiar `perfil.example.md` a `perfil.md` y completarlo (opcional, pero mejora mucho las notas).
3. `uv run notas diagnostico` revisa que esté todo.
4. Si vas a usar el Atajo: `uv run notas preparar` crea las carpetas en iCloud Drive y después
   se arma el Atajo en el iPhone (ver abajo).

## Tipos de grabación

| Tipo | Para qué | Qué arma la nota |
|---|---|---|
| `clase` | Clases de la facultad | Índice con minutos; por tema, lo que explicó el profesor con citas textuales; lo que marcó como importante; preguntas de alumnos; avisos |
| `charla` | Charlas, seminarios, paneles | Contexto, oradores, ideas por tema con citas, coincidencias y diferencias, preguntas del público, información práctica, etiquetas |
| `conversacion` | Conversaciones | Cómo fue la conversación, acuerdos, pendientes |
| `nota` | Notas sueltas | Ideas y tareas |

Las plantillas están en `plantillas/<tipo>.md` y se pueden editar.

## Grabaciones en varias partes

Si una clase o charla se grabó en varios audios (por un recreo, porque hubo que usar el
teléfono, etc.), se procesan como **una sola grabación**: se unen en un único audio antes de
transcribir, así el profesor queda con la misma etiqueta en todas las partes y los minutos
corren de corrido. La nota lista dónde empieza cada parte y el audio unido queda en
`salida/audios/`.

Las partes se ordenan por la hora en que se grabaron, si los archivos la traen (ver «Editable»
abajo). Si no, en la carpeta de entrada se ordenan por nombre en orden natural («Facultad 3»
antes que «Facultad 10»), y con `notas procesar` se respeta el orden en que se pasan.

## Compartir como «Editable»: la hora real

Al compartir desde Notas de Voz (por AirDrop, al Atajo o a donde sea), tocar **Opciones →
Editable** antes de elegir el destino. Así se manda el archivo original, que trae la hora en que
empezó la grabación. Sin eso, Notas de Voz genera un archivo nuevo con la hora de exportación.

Con la hora real, cada marca de la nota lleva la hora del reloj y el minuto del audio:
`[09:47 · 12:13]`. Si durante la clase anotás en papel «09:47, no entendí», buscás esa hora en la
nota. En grabaciones en partes, cada parte usa su propia hora de inicio, así que la hora sigue
siendo exacta después de un recreo. Las partes también se ordenan por esa hora.

## Brief: contexto previo

Unas líneas sobre la grabación antes de procesarla: de qué se trata, quién habla, qué te
interesa. Por ejemplo: «Clase 6 de Macro II con García, IS-LM con expectativas. Me interesa la
intuición». Es opcional y mejora la nota. Se pasa con `--brief`, o como un `.txt` en la carpeta
del envío (el Atajo lo pide al compartir).

## Carpeta de entrada

```
Transcribir/
  <tipo>/<envío>/              ← una carpeta por cada vez que se comparte: todas las partes
                                 de una grabación + brief.txt opcional
  clase/<materia>/<envío>/     ← en clases, con la materia: usa vocabulario/<materia>.txt
  <tipo>/audio.m4a             ← también vale un audio suelto (con audio.txt como brief)
  procesados/                  ← adonde se mueve lo procesado
  errores/                     ← lo que falló, con un .error.txt que explica por qué
```

Una carpeta es un **envío** si su nombre empieza con una fecha (`2026-10-07 1530`); si no, es
una **materia**.

## Uso

```sh
uv run notas diagnostico                                  # revisa la instalación, sin gastar nada
uv run notas pendientes                                   # procesa todo lo que haya en Transcribir/

# Una grabación suelta o en partes (en el orden en que se grabaron)
uv run notas procesar parte1.m4a parte2.m4a parte3.m4a --tipo clase --materia "Macro II" \
    --brief "Clase de IS-LM; me interesa la intuición de las pendientes"
uv run notas procesar charla.m4a --tipo charla --brief brief.txt

# Rehacer la nota sin volver a transcribir (gratis), por ejemplo con otro tipo o brief
uv run notas resumir salida/transcripciones/<archivo>.json --tipo charla --brief "…"
```

Cada grabación deja en `salida/`:

- `<fecha> <título>.md`: la nota, con la transcripción completa en un desplegable al final.
- `transcripciones/<fecha> <audio>.json`: la transcripción cruda. Si se reprocesa la misma
  grabación, se reusa y no se vuelve a pagar.
- `audios/<fecha> <audio>.m4a`: solo si vino en partes, el audio unido al que se refieren los minutos.

## Personalizar

- **Quién sos y para qué usás las notas:** `perfil.md`. Claude lo lee cada vez que arma una nota.
- **Qué va en cada nota:** `plantillas/<tipo>.md`. Para sumar un tipo nuevo, ver [AGENTS.md](AGENTS.md).
- **Vocabulario por materia:** `vocabulario/<materia>.txt` (ver `vocabulario/README.md`).
- **Modelo de Claude:** `CLAUDE_MODELO` en `.env`.

## El Atajo del iPhone

En la app Atajos, crear un atajo nuevo llamado **Transcribir**:

1. En los detalles del atajo, activar **Mostrar en la hoja de compartir** y dejar que reciba
   **Archivos** y **Multimedia**.
2. **Elegir del menú** con cuatro opciones: *Clase*, *Charla*, *Conversación* y *Nota*. En cada
   una, **Texto** con el nombre de la carpeta (`clase`, `charla`, `conversacion`, `nota`).
   - Opcional, dentro de *Clase*: otro **Elegir del menú** con las materias, que dé
     `clase/Macro II`, `clase/Econometría`, etc.
3. **Fecha actual** → **Formatear fecha** con formato personalizado `yyyy-MM-dd HHmm`.
4. **Texto**: `Transcribir/<resultado del menú>/<fecha formateada>`.
5. **Crear carpeta** en iCloud Drive con esa ruta.
6. **Guardar archivo**: la *Entrada del atajo* en esa carpeta, con *Preguntar dónde guardar*
   desactivado.
7. **Pedir entrada** de texto: «Contexto (opcional)». **Si** tiene algún valor: **Guardar
   archivo** con ese texto como `brief.txt` en la misma carpeta.

Para usarlo: en Notas de Voz, elegir la grabación (o todas las partes de una misma clase) →
Compartir → **Opciones → Editable** → **Transcribir** → elegir el tipo → dictar el contexto o
dejarlo vacío.

También sirve mandarlas por **AirDrop** (también como Editable) y pedirle a Claude que las procese
desde Descargas. Ojo: si llega un archivo con un nombre que ya existe en Descargas, macOS lo
renombra (por ejemplo, «New Recording 5» pasa a «New Recording 6»).

## Privacidad

El audio se sube a AssemblyAI y la transcripción pasa por Claude. Tus archivos personales
(`.env`, `perfil.md`, vocabularios, notas y audios) no se suben a git.

## Agregar otro motor de transcripción

Escribir `src/notas_de_voz/motores/<motor>.py` con una función `transcribir()` igual a la de
`assemblyai.py`, registrarla en `motores/__init__.py` y poner `MOTOR=<motor>` en `.env`.

## Licencia

MIT.
