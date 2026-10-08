# Vocabulario por materia

Un archivo `<materia>.txt` por materia, con un término por línea (hasta seis palabras cada uno).
El nombre del archivo tiene que coincidir con la subcarpeta de la materia en
`Transcribir/clase/<materia>/`, o con lo que se pase en `--materia`.

Se usa en dos lugares:

- AssemblyAI lo recibe como `keyterms_prompt` y reconoce mejor esos términos.
- Claude lo recibe como contexto para corregir los que igual queden mal transcriptos.

Hay un ejemplo en [ejemplo.txt](ejemplo.txt). Las líneas que empiezan con `#` se ignoran.

Conviene empezar con pocos términos (20 o 30) y sumar los que salgan mal: demasiados empeoran
la transcripción.

Los vocabularios son personales y no se suben a git (salvo `ejemplo.txt`).
