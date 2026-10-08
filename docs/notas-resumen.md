# Cómo armar las notas a partir de la transcripción

Fecha: 2026-10-07. Investigación sobre técnicas para pasar de la transcripción a una nota que muestre puntos clave, contexto y dinámica, y no solo un resumen. Complementa [investigacion.md](investigacion.md), que cubre la transcripción.

Etiquetas: **[E]** evidencia (papers, benchmarks), **[P]** práctica de la industria o guía de un proveedor, **[R]** recomendación propia para este proyecto.

## Ajuste tras aclarar el propósito (2026-10-07)

Las notas se pensaron como un **archivo de consulta**, no como material de estudio que reemplace los apuntes (ver [idea.md](idea.md)). Con eso cambian algunas conclusiones de este documento:

- **Lo que pasa a importar más:**
  - fidelidad;
  - citas textuales del profesor o el orador, con el minuto;
  - un índice de temas que permita encontrar un momento rápido;
  - notas que se entiendan solas dentro de dos años: con contexto del evento, quién habló y por qué importa;
  - poder buscar y preguntar sobre todas las notas juntas.
- **Lo que pasa a importar menos:** las preguntas de autoevaluación y los huecos para completar (secciones 1 y 3.1). La evidencia sobre aprendizaje sigue siendo válida, pero acá no aplica, porque las notas no reemplazan el estudio. Quedan como opcionales.
- **Lo que sigue igual:** extraer antes de redactar (2.2), los capítulos con timestamps (2.3), el formato por tipo, el brief y la base de conocimiento.

## Veredicto

1. **Extraer primero y redactar después.** En vez de pedir la nota de una, el modelo primero lista los momentos importantes de la transcripción, cada uno con su tipo, quién habló y su timestamp: afirmaciones, preguntas y respuestas, énfasis del profesor, desacuerdos, ejemplos. Recién después arma la nota a partir de esa lista. Es la técnica con mejor relación costo/beneficio, reduce omisiones y alucinaciones, y es la que más ayuda a capturar la dinámica.
2. **Un formato por tipo de grabación, pensado para estudiar.** En las clases de economía, un bloque fijo por modelo (supuestos, ecuaciones, gráfico descripto, intuición) con anclas para sumar después las slides y los apuntes en papel. En las charlas, una ficha de oradores, tesis, argumentos, citas textuales y la ronda de preguntas.
3. **La nota no debería hacer todo el trabajo.** La evidencia muestra que recibir notas hechas por un LLM, sin trabajarlas, rinde menos que tomarlas uno. Conviene que la nota traiga preguntas de autoevaluación y algunos huecos para completar a mano.
4. **Un brief antes de procesar y una base de conocimiento chica, curada a mano.** Con un glosario, el temario y los perfiles de profesores alcanza para meter todo en el prompt: no hace falta RAG. Las reglas nuevas se aprueban a mano antes de entrar, para que la memoria no se llene de basura.

## 1. Qué hace útil a una nota para estudiar

- **[E] Lo que más funciona es autoevaluarse y estudiar espaciado.** Resumir, subrayar y releer quedaron en utilidad baja (Dunlosky et al. 2013). A la semana, quien practicó recordar retuvo 61 % y quien releyó, 40 % (Roediger y Karpicke 2006).
- **[E] Repasar notas sirve aunque las haya hecho otro.** En el metaanálisis de Kobayashi, el efecto de repasar notas (d≈0,45) es mayor que el de solo tomarlas (d≈0,22). Recibir las notas del docente también suma. Una nota generada por IA es buen material de repaso. Las cifras salen de citas secundarias.
- **[E] Generar el contenido uno mismo rinde más que leerlo hecho.** Un mapa conceptual armado por el alumno tiene g = 0,82 y uno ya hecho, g = 0,37 (Nesbit y Adesope 2006).
- **[E] Riesgo concreto con la IA.** En un ensayo con 405 estudiantes (Kreijkes et al. 2025), tomar notas, sola o combinado con un LLM, rindió más que usar solo el LLM. Los alumnos igual preferían el LLM y creían que les servía más.
- **[E débil] Cornell.** No encontré un metaanálisis sólido. Su valor probable está en la columna de preguntas, porque obliga a autoevaluarse.
- **[P] Zettelkasten, notas evergreen, resumen progresivo.** Son marcos de práctica sin ensayos controlados. La idea útil para este proyecto es organizar por **concepto** y no solo por clase.

**[R] Conclusión de diseño:** la IA prepara el material para repasar y deja la parte generativa para vos. Eso implica:
- separar lo que se dijo de lo que infirió el modelo;
- terminar cada nota con preguntas de autoevaluación;
- dejar huecos explícitos para completar con las slides y el papel.

## 2. Técnicas para generar la nota

### 2.1 Estructura del prompt [P]

Guía de Anthropic para documentos largos:
- **La transcripción arriba y las instrucciones al final.** Anthropic informa hasta 30 % de mejora con documentos complejos, según una medición interna.
- **Cada parte en una etiqueta XML:** `<brief>`, `<glosario>`, `<transcripcion>`, `<plantilla>`.
- **Pedir citas textuales antes de redactar.**

El pipeline ya lo hace así (ver `src/notas_de_voz/resumen.py`).

### 2.2 Extraer primero, redactar después [E]

FRAME (EMNLP 2025) extrae los hechos salientes, los puntúa, los agrupa por tema y recién después redacta. Reduce alucinaciones y omisiones frente a pedir la nota directo.

**[R] Extracción tipada** para este caso, cada ítem con `[mm:ss]` y hablante:

| Tipo | Ejemplo |
|---|---|
| afirmación + evidencia o ejemplo | "La incidencia depende de las elasticidades relativas" + el ejemplo del cigarrillo |
| pregunta → respuesta | quién preguntó, quién respondió y qué dijo |
| énfasis | lo que se repite o se marca: "esto entra", "siempre se equivocan" |
| desacuerdo | la postura A frente a la B |
| anécdota o analogía | "el arquero es el último defensor" |
| dato | cifras, fechas, nombres, bibliografía |
| tarea o aviso | ejercicios, fechas de entrega o de examen |

Puede ir en la misma llamada: primero un bloque `<extraccion>` que el script descarta y después la nota. También puede ir en dos llamadas, que es más fiel pero cuesta el doble de tiempo.

**Esto resuelve directamente "mostrar la dinámica":**
- los pares pregunta → respuesta y los desacuerdos reconstruyen cómo fue la conversación;
- los énfasis muestran qué le importa al profesor.

### 2.3 Capítulos por tema [P/E débil]

Pedir primero un índice de bloques con tiempo de inicio y fin, y después completar cada uno. Es lo que hacen los sistemas de clases como BOOM (KIT) y resumidores como Snipd o tl;dv. El resultado es una nota que sigue el orden real de la clase y permite volver al minuto exacto del audio.

### 2.4 Fidelidad y verificación [E]

**Los problemas de contexto largo existen aun cuando todo entra en el prompt:**
- "Lost in the middle": se usa peor la información ubicada en el medio del contexto.
- "Context rot": el rendimiento baja a medida que crece el input, en 18 modelos, Claude 4 incluido.
- SummHay: con unos 93 mil tokens, la cobertura con cita correcta quedó por debajo de 20 %.

Una clase de dos horas son unos 30 a 40 mil tokens.

**Mitigaciones:**
- Exigir un timestamp por cada afirmación. Obliga al modelo a recorrer toda la transcripción.
- Agregar un paso de verificación separado, al estilo Chain-of-Verification. Por cada afirmación de la nota se busca su cita en la transcripción; si no aparece, se marca `[sin respaldo]` o se borra. Cuesta una llamada más.
- Permitirle decir "no está claro en el audio" en vez de completar.

La API de Citations de Anthropic mejora el recall hasta 15 % según su evaluación interna, pero `claude -p` no la expone.

### 2.5 Hablantes y errores de reconocimiento

- **[E]** Un LLM puede corregir la atribución de hablantes a partir del contexto. DiarizationLM redujo el error un 55 %, aunque con un modelo entrenado para eso.
- **[R] Paso 0: mapear hablantes antes de extraer.** Usar el brief y las presentaciones ("soy Ana, del equipo de análisis") para asignar nombres, y marcar los turnos dudosos. Ya lo hacemos en parte. En charlas con público, las preguntas suelen quedar con la etiqueta de un orador.
- **[E] Riesgo de corregir términos con un LLM:** puede inventar entidades que nadie dijo.
- **[R] Corregir solo contra el glosario** y marcar `[¿?]` lo dudoso.

### 2.6 Lo que no conviene

- **Map-reduce** (resumir por partes y fusionar): pierde detalle y amplifica las alucinaciones al fusionar. Solo tiene sentido por encima de 4 horas de audio.
- **Chain-of-Density**: sirve para un TL;DR denso arriba de la nota, no para la nota entera.
- **Razonamiento extendido** ("pensar más"): en resumen de diálogos, los modelos con razonamiento extendido salieron más largos y con más inconsistencias (2025). No asumir que mejora: medirlo.

## 3. Formato por tipo de grabación

### 3.1 Clase teórica de economía [R]

Un bloque fijo por modelo o concepto:

```
## Modelo: incidencia de un impuesto unitario {#impuesto-unitario}
- Supuestos: competencia perfecta; impuesto t por unidad.
- Ecuaciones: Qd = a − bP · Qs = c + dP · Ps = Pd − t
- Resultado: paga más el lado menos elástico.
- Intuición: …
- Gráfico (descripto): ejes P y Q → la oferta se desplaza ↑ en t → Pd↑, Ps↓, Q↓ → pérdida de eficiencia: triángulo entre Q1 y Q0.
- Derivación: pasos numerados; [VERIFICAR] donde el audio fue ambiguo.
- Lo que marcó el profesor: "esto entra" ⏱ 34:10
- Fuentes: ⏱ 34:10–41:55 · Slide [COMPLETAR] · Cuaderno [COMPLETAR]
- Para pensar: ¿qué pasa si la oferta es perfectamente inelástica?
```

- **Anclas estables** (`{#impuesto-unitario}`): permiten que después un script sume bajo el mismo título el texto de las slides y los apuntes en papel. Los apuntes en papel se pueden digitalizar con fotos y un LLM.
- **Fórmulas dictadas:** marcarlas como de baja confianza, porque el audio pierde subíndices y signos. Las slides las corrigen.
- **Gráficos:** describirlos siempre en el mismo orden (ejes → curvas → shock → desplazamiento → nuevo equilibrio → áreas).
- **Al final de la nota:**
  - un mapa de la clase con los capítulos y sus timestamps;
  - de 5 a 10 preguntas de autoevaluación con las respuestas plegadas, algunas de tipo "¿por qué…?";
  - una sección "Dudas y huecos".

### 3.2 Charla, seminario o panel [R]

- **Ficha de oradores:** nombre, cargo y desde dónde habla.
- **Tesis o mensaje central de cada orador,** en una oración.
- **Argumentos e ideas,** marcando si se apoyan en un dato, una anécdota o una opinión.
- **Citas textuales con timestamp.** Copiadas literalmente de la transcripción, nunca parafraseadas como si fueran citas.
- **Dinámica:** en qué coincidieron y en qué difirieron. En un panel conviene una matriz de orador × tema.
- **Preguntas del público:** la pregunta, quién respondió y qué dijo.
- **Datos útiles:** fechas, procesos, recursos.
- **Ideas para mí:** hueco para completar a mano.

### 3.3 Conversación y nota suelta

Siguen como están, más la extracción tipada y los timestamps.

## 4. El brief previo

- **[E]** Darle al modelo el objetivo y el perfil del lector antes de elegir qué incluir mejora el ajuste de la nota (SCOPE, 2025; QMSum para reuniones).
- **[P]** Granola, Notion AI y Fathom combinan instrucciones por tipo con un contexto por sesión.

**[R] Contenido del brief:** de 3 a 6 líneas.
- de qué es la grabación;
- quién habla;
- qué te interesa;
- qué ya sabés;
- si después vas a sumar slides.

Ejemplo: "Clase 6 de Macro II con García. Tema: IS-LM con expectativas. Me interesa entender la intuición, las derivaciones las tengo en las slides."

**[R] Cómo cargarlo:**
- **Desde el iPhone:** el Atajo, después de elegir el tipo, pide un texto, que se puede dictar. Lo guarda como `.txt` con el mismo nombre que el audio, y el pipeline lo lee si existe.
- **Desde la Mac:** con `--brief "…"` o con un archivo.
- **Si no hay brief:** el pipeline funciona igual que ahora.

## 5. Base de conocimiento que crece

**[P] Patrón que conviene seguir.**
- La memoria se guarda en archivos Markdown que se meten enteros en el prompt; no hace falta una base vectorial. Anthropic sugiere directamente meter todo en el contexto si la base pesa menos de unos 200 mil tokens.
- Se separan tres tipos:
  - **hechos:** glosario, temario, perfiles;
  - **reglas:** cómo querés las notas;
  - **historial:** qué se vio en cada clase.

**[R] Estructura propuesta:**

```
conocimiento/
  usuario.md                    # preferencias generales de las notas
  materias/<materia>/
    materia.md                  # profesor, temario, bibliografía, notación
    glosario.md                 # término | variantes mal transcriptas | definición
    historial.md                # una línea por clase: fecha, tema, anclas
  personas/<persona>.md         # profesores y oradores: estilo, qué enfatizan, cómo nombran las cosas
  reglas.md                     # reglas aprendidas de tus correcciones (aprobadas por vos)
  ejemplos/                     # 1 a 3 notas que corregiste, como modelo a imitar
```

- **Orden en el prompt:**
  1. usuario
  2. materia
  3. glosario
  4. persona
  5. reglas
  6. ejemplos
  7. historial
  8. brief
  9. transcripción
  10. instrucciones al final
- **Historial:** permite que la nota nueva enlace con clases anteriores ("esto extiende {#is-lm} del 15/09").
- **Glosario:** alimenta los `keyterms` de AssemblyAI. AssemblyAI recomienda empezar con pocos y sumar solo los que fallan, porque demasiados causan sobrecorrecciones.
- **Ciclo de mejora:**
  1. Corregís una nota.
  2. Un script compara la versión original con la corregida.
  3. Claude propone reglas generales, que van a `reglas.pendientes.md`.
  4. Las aprobás y recién ahí pasan a `reglas.md`.
- **Higiene:**
  - nada se escribe en la memoria sin tu aprobación;
  - cada archivo tiene un tope de largo;
  - cada regla lleva su fecha;
  - una vez por mes se consolidan las reglas: se fusionan las duplicadas y se borran las contradictorias.

Esta parte es práctica de la industria (CoALA, la memory tool de Claude, LangMem). No hay ensayos en el dominio educativo.

## 6. Cómo saber si una nota mejoró

- **[E] Preguntas de examen.** Funcionan mejor que las métricas automáticas clásicas.
  - Escribir 10 preguntas por grabación a partir de la transcripción o las slides.
  - Contar cuántas se responden solo con la nota.
  - Mide completitud de forma directa y barata.
- **[E] Rúbrica de fidelidad, completitud y concisión** (FineSurE, ACL 2024) con un LLM como juez.
  - Los jueces LLM prefieren los textos largos y los de su propio estilo.
  - Para compensarlo: criterios binarios, invertir el orden en las comparaciones y, si se puede, usar un modelo distinto del que generó la nota.
- **[R] Set fijo de prueba.** 4 o 5 grabaciones reales, contra las que se corre cada versión nueva del prompt.

## 7. Ideas tomadas de herramientas existentes

| Idea | De dónde | Prioridad |
|---|---|---|
| Brief + instrucciones por tipo | Granola, Notion AI, Fathom | Alta |
| Puntos clave con tipo (dato, opinión, consejo), quién y timestamp | Eightify, Fireflies | Alta |
| Capítulos con timestamps | Snipd, tl;dv | Alta |
| Glosario o vocabulario que crece | Otter, Plaud | Alta |
| Citas a la fuente en cada afirmación | NotebookLM, Granola | Media |
| Marcar momentos en vivo (un atajo que guarda la hora) | Fathom, Plaud, Snipd | Media |
| Sumar slides y fotos como fuentes | NotebookLM, Plaud | Media (cuando haya slides) |
| Varias notas de una misma grabación (apunte de estudio + dinámica) | Plaud, recipes de Granola | Baja |
| Separar visualmente lo tuyo de lo de la IA | Granola | Baja (aplica cuando haya notas propias) |
| Flashcards automáticas | Apps de estudio | No por ahora: los usuarios se quejan de que salen irrelevantes |

## 8. Propuesta para el pipeline, por etapas

1. **Prompt nuevo.** Cambia el prompt, no la arquitectura.
   - Transcripción arriba con etiquetas XML.
   - Extracción tipada con timestamps en la misma llamada.
   - Plantillas nuevas de **clase** (bloque por modelo, anclas, preguntas y huecos) y **charla** (cuarto tipo).
   - Brief opcional, por archivo `.txt` o con `--brief`.
2. **Base de conocimiento.** La carpeta `conocimiento/` con materia, glosario, personas e historial, armada a mano al principio.
3. **Fidelidad y medición.** Paso de verificación, paso 0 de hablantes y el set de prueba con preguntas de examen, para decidir si los pasos extra valen lo que cuestan.
4. **Aprendizaje.** Ciclo de correcciones → reglas propuestas → aprobación. Integración con slides y apuntes en papel a través de las anclas.

## Preguntas abiertas

- **Dónde se leen las notas:** Notion, Obsidian o el `.md`. Define si las fórmulas van en Unicode o en LaTeX (`--latex`), y si los `<details>` y las anclas se ven bien.
- **Preguntas de autoevaluación:** en todas las clases o solo cuando se pidan en el brief.

## Fuentes

**Técnicas con LLMs**
- FRAME y SCOPE: https://arxiv.org/abs/2509.15901
- BooookScore: https://arxiv.org/abs/2310.00785
- Fusión recursiva y alucinaciones: https://arxiv.org/abs/2502.00977
- Chain-of-Density: https://arxiv.org/abs/2309.04269
- Modelos de razonamiento en resumen de diálogos: https://arxiv.org/abs/2507.02145
- Lost in the middle: https://arxiv.org/abs/2307.03172
- Context rot: https://research.trychroma.com/context-rot
- SummHay: https://arxiv.org/abs/2407.01370
- Chain-of-Verification: https://arxiv.org/abs/2309.11495
- DiarizationLM: https://arxiv.org/abs/2401.03506
- Corrección de ASR con LLMs: https://arxiv.org/abs/2512.21828
- QMSum: https://arxiv.org/abs/2104.05938
- BOOM: https://arxiv.org/abs/2512.02817
- Stan: https://arxiv.org/abs/2603.04657
- FineSurE: https://arxiv.org/abs/2407.00908
- QAGS: https://arxiv.org/abs/2004.04228
- Sesgos de LLM como juez: https://arxiv.org/abs/2410.21819

**Guías de Anthropic y de AssemblyAI**
- Prompting: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Alucinaciones: https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations
- Citations API: https://claude.com/blog/introducing-citations-api
- Context engineering: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Contextual retrieval: https://www.anthropic.com/news/contextual-retrieval
- Memory tool: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
- Keyterms de AssemblyAI: https://www.assemblyai.com/docs/keyterms-prompting

**Aprendizaje**
- Dunlosky et al. 2013: https://www.psychologicalscience.org/news/releases/which-study-strategies-make-the-grade.html
- Roediger y Karpicke 2006: https://psychology.ecu.edu/wp-content/pv-uploads/sites/216/2019/03/Roediger-Karpicke-2006.pdf
- Nesbit y Adesope 2006: https://www.sfu.ca/~jcnesbit/research/nesbitadesope2006.htm
- Kreijkes et al. 2025: https://www.microsoft.com/en-us/research/publication/effects-of-llm-use-and-note-taking-on-reading-comprehension-and-memory-a-randomised-experiment-in-secondary-schools/
- Efecto de generación: https://pmc.ncbi.nlm.nih.gov/articles/PMC6099118
- Notas evergreen: https://notes.andymatuschak.org/Evergreen_notes_should_be_concept-oriented

**Memoria**
- CoALA: https://arxiv.org/abs/2309.02427
- LangMem: https://blog.langchain.com/langmem-sdk-launch
- Memoria con reflexión guiada por ejemplos: https://arxiv.org/abs/2411.07446

**Herramientas**
- Granola: https://docs.granola.ai/help-center/taking-notes/customise-notes-with-templates · https://docs.granola.ai/help-center/getting-more-from-your-notes/recipes
- NotebookLM: https://blog.google/innovation-and-ai/models-and-research/google-labs/notebooklm-student-features/
- Notion AI: https://www.notion.com/es-es/releases/2026-03-18
- Otter: https://help.otter.ai/hc/en-us/articles/360048571373-Manage-vocabulary
- Fireflies: https://fireflies.ai/blog/fireflies-ai-apps/
- tl;dv: https://intercom.help/tldv/en/articles/7198123-ai-meeting-notes
- Fathom: https://help.fathom.video/en/articles/3239809
- Plaud: https://eu.plaud.ai/pages/plaud-intelligence
- Eightify: https://affine.pro/blog/eightify-youtube-summarizer
- Recall: https://docs.recall.it/
