# Investigación — notas de voz → transcripción + resumen

Fecha: 2026-10-06. Los precios y las versiones cambian rápido: verificarlos antes de construir.

## Veredicto

**No hay una herramienta gratuita que haga todo el recorrido (iPhone → transcripción con hablantes → resumen → nota). Construirla es fácil:** unos pocos scripts que pegan servicios existentes, uno o dos días de trabajo.

La parte difícil no es el código, sino **elegir el motor de transcripción** que mejor funcione con tus audios. Eso se decide probando con grabaciones reales, no leyendo benchmarks.

El costo es prácticamente cero: las APIs en la nube cuestan alrededor de USD 0,23 por hora de audio, y los créditos gratuitos alcanzan para cientos de horas.

## 1. Lo que ya existe

### Lo que trae el iPhone

- **Notas de Voz** transcribe en el dispositivo desde iOS 18. iOS 26 usa un motor más rápido (SpeechAnalyzer).
- **No separa hablantes** y no exporta el texto.
- Los resúmenes con Apple Intelligence (Writing Tools, o grabando dentro de la app Notas) solo funcionan en iPhones compatibles, y son genéricos.
- **Conclusión:** sirve para buscar dentro de las grabaciones, no para lo que buscás.

### Apps open source

| Herramienta | Qué hace | Encaje |
|---|---|---|
| **Scriberr** | Self-hosted. Whisper/Parakeet + diarización + resúmenes con LLM + API REST + **carpeta vigilada**. Corre en Mac (Homebrew). MIT. | **La más cercana.** Retomó el desarrollo después de un parate: dudas sobre su mantenimiento. Habría que probar su calidad en castellano. |
| **noScribe** | App de escritorio: Whisper + pyannote, local, con separación de hablantes. | Buena transcripción, pero **no resume** y es manual (archivo por archivo). |
| **Meetily** | Asistente de reuniones local (Rust), resumen con Ollama/Claude. Importa audios en beta. | Pensada para reuniones en vivo. **La diarización no está en la versión gratuita.** |
| **Hyprnote (ahora anarlog)** | Notas de reuniones locales en Markdown, solo macOS. | Pensada para grabar reuniones en la Mac, no para procesar audios del iPhone. |

Ninguna resuelve el paso iPhone → herramienta → nota sin intervención manual. Scriberr es la única que se le acerca, gracias a la carpeta vigilada.

## 2. Motores de transcripción + diarización

Es la pieza que define la calidad.

### En la nube

| Servicio | Precio aprox. | Diarización | Notas |
|---|---|---|---|
| **AssemblyAI** Universal-3.5 Pro | USD 0,21/h + 0,02/h por diarización | Sí. **Mejor en el benchmark de diarización** (cpWER 30,17) | **USD 50 gratis sin tarjeta ≈ 200+ horas.** Admite *keyterms* (vocabulario de la materia). |
| **ElevenLabs** Scribe v2 | No encontré el precio por hora del modo batch | Sí, hasta 48 hablantes. Segundo en el benchmark (35,26) | Promete funcionar bien con ruido de fondo. Archivos de hasta 10 h. |
| **Deepgram** Nova-3 | ~USD 0,35/h + diarización | Sí. Cuarto en el benchmark (37,92) | USD 200 gratis (vencen al año). |
| **Gemini 3.5 Transcribe** | Tiene free tier | Sí, hasta 8 hablantes | **Con diarización, máximo 30 minutos por archivo**: una clase de 2 h habría que partirla, y entre partes se pierde la consistencia de quién es quién. Tiene `es-419`. |
| **OpenAI** gpt-4o-transcribe-diarize | ~USD 0,36/h | Sí. Acepta muestras de voz de hasta 4 hablantes conocidos | Hay reportes de que **traduce el castellano al inglés** a mitad del audio. Descartar por ahora. |

El benchmark (cpWER) es de AssemblyAI y mayormente en inglés: hay que tomarlo con pinzas.

### Local, en tu Mac (gratis y privado)

- **Whisper large-v3 / turbo** con aceleración Metal: 10 a 18 veces más rápido que el tiempo real en un Apple Silicon reciente. Buen castellano.
- **Parakeet v3** (NVIDIA): mucho más rápido y admite 25 idiomas, castellano incluido. Su calidad con audio ruidoso en castellano está por verificar.
- **pyannote community-1** para la diarización: corre en Apple Silicon unas 24 veces más rápido que el tiempo real. Gratis.
- **WhisperX** combina Whisper con pyannote. Es lo que usan Scriberr y noScribe por debajo.

**Expectativa:** en audio limpio, local y nube andan parecido. **En ruido y en diarización con voces superpuestas, las APIs comerciales suelen ganar.** Como la nube cuesta centavos, conviene que la opción local sea la línea de base contra la que comparar, no la apuesta principal.

## 3. Los dos casos difíciles

### Conversación entre dos personas

- La diarización asigna etiquetas genéricas (Hablante A / B), no nombres. **El LLM del resumen puede inferir quién es quién** por el contexto ("A pregunta, B responde como médico"), o se le puede indicar al subir el audio.
- El problema típico son las interrupciones y las voces superpuestas: ahí es donde más se separan los proveedores.

### Clase con ruido de fondo

- **No conviene filtrar el ruido antes de transcribir.** Los modelos modernos están entrenados con ruido, y un filtro agresivo suele empeorar el resultado. Hay que probarlo, no asumirlo.
- Lo que más ayuda:
  - Pasarle al motor **vocabulario de la materia** (*keyterms* en AssemblyAI).
  - Que el **resumen se concentre en el profesor**: la diarización identifica a quien más habla y el LLM le da menos peso a lo demás.
- Grabar con el iPhone cerca del profesor mejora más que cualquier software.

## 4. El resumen

- Lo hace un LLM, con **una plantilla por tipo de audio**:
  - **Conversación:** quién dijo qué, acuerdos y pendientes.
  - **Clase:** temas, definiciones, fórmulas, lo que "entra en el parcial".
  - **Nota suelta:** ideas y tareas.
- **Opción de costo cero:** usar tu suscripción de Claude con Claude Code (`claude -p`) en la Mac, sin pagar API.
- **Alternativa:** la API de Claude con Haiku, a centavos por audio.

## 5. Arquitectura propuesta

```
iPhone (Notas de Voz)
  └─ Compartir → Atajo de iOS → carpeta de iCloud Drive "Transcribir/"
                 (opcional: preguntar el tipo: conversación / clase / nota)
Mac
  └─ script (vigila la carpeta o se corre a mano)
       1. sube el audio a AssemblyAI (o el motor ganador) con diarización y idioma es
       2. arma la transcripción ordenada por hablante, con marcas de tiempo
       3. resumen con Claude según la plantilla del tipo
       4. guarda la nota → Markdown local y/o una página de Notion (la API de Notion es gratis)
```

Detalles a tener en cuenta:

- Las notas de voz se sincronizan con la Mac, pero la carpeta interna de la app está protegida por macOS (verificado: "Operation not permitted"). Leerla requiere darle **Acceso total al disco** a la terminal. El Atajo de iOS que comparte el audio a iCloud Drive es más limpio y además permite elegir qué se procesa.
- Lo que no se automatiza fácil en iPhone es el procesamiento sin la Mac. Si eso importa, habría que poner el script en un servidor (Railway, por ejemplo). Arrancaría con la Mac.

## 6. Próximo paso

**Spike de comparación** con 3 o 4 audios reales: una conversación de dos personas, una clase con ruido y una nota suelta.

- Pasarlos por AssemblyAI, ElevenLabs Scribe v2, Gemini 3.5 Transcribe y WhisperX local.
- Comparar lado a lado: errores de transcripción, asignación de hablantes y comportamiento con ruido.
- Las APIs aceptan `.m4a` directo. Para la opción local hace falta ffmpeg (no está instalado; tampoco hay Homebrew).

## Privacidad

El audio pasa por AssemblyAI y la transcripción, por Claude. Para clases y charlas importa poco; para conversaciones privadas conviene pensarlo. La alternativa es un motor local (sección 2), que se puede sumar como motor nuevo.

## Fuentes

- [Scriberr](https://github.com/rishikanthc/Scriberr) · [Meetily](https://github.com/Zackriya-Solutions/meetily) · [noScribe](https://www.wares.gg/apps/noscribe) · [Comparativa self-hosted 2026](https://meetily.ai/blog/best-self-hosted-meeting-transcription-tools-2026)
- [Precios de AssemblyAI](https://www.assemblyai.com/pricing.md) · [Benchmark de diarización](https://www.assemblyai.com/blog/top-speaker-diarization-libraries-and-apis)
- [ElevenLabs STT](https://elevenlabs.io/speech-to-text-api) · [Precios de Deepgram](https://www.costbench.com/software/ai-transcription-apis/deepgram/)
- [Gemini: transcripción](https://ai.google.dev/gemini-api/docs/generate-content/transcribe)
- [gpt-4o-transcribe-diarize](https://gate.ai/blog/gpt-4o-transcribe-diarize-openai-specs-pricing-api-use-cases) · [Reporte de traducción espontánea](https://community.openai.com/t/gpt-4o-transcribe-diarize/1371826)
- [Notas de Voz en iOS 26: límites](https://klu.so/blog/apple-voice-memos-transcription-limits)
- [Parakeet vs Whisper](https://spokenly.app/blog/parakeet-vs-whisper) · [Whisper en Apple Silicon](https://www.promptquorum.com/local-llms/apple-silicon-whisper-metal-benchmark) · [pyannote en Apple Silicon](https://docs.fluidinference.com/reference/benchmarks)
