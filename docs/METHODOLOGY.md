# Metodología de trabajo

Notas personales de Alexis Zapico Fernández. No es un checklist rígido ni un estándar externo:
es el punto de partida para cualquier desarrollo (paper, código, lo que sea), y se espera que
varíe con el tiempo. Este documento describe el bucle en general; cómo se instancia en este
repo concreto va al final.

## El bucle

**0. Problema** — una frase: qué se resuelve, qué queda fuera explícitamente. Sin esto no hay
con qué medir el resto.

**1. Hipótesis + refutadores** — una frase falsable, más la lista de qué observación la
tumbaría. Si no hay un refutador nombrado, es intuición, no hipótesis, y no pasa al siguiente
paso.

**2. Atacar** — en dos partes, en este orden:
   - **Auditar el instrumento**, antes de correrlo. Tres preguntas fijas: ¿mide lo mismo en
     todos los brazos que comparo (mismo alcance, mismas unidades)? ¿alguna "verdad" que uso
     para juzgar es también una entrada de lo que juzgo (fuga)? ¿baseline y tratamiento son
     comparables de verdad? Este paso es el que más falla si se salta — ver la nota más abajo.
   - **Correr el ataque** intentando romper la hipótesis, no confirmarla.

**3. Reformular o no — gate explícito** — solo si un refutador se sostuvo, midiendo. Se declara
por escrito y se vuelve al paso 1. Nunca reformular a media corrida por una corazonada nueva o
porque algo "parece más interesante": eso es lo que atascó este proyecto varias veces antes de
adoptar el bucle.

**4. Registrar** — solo entra a lo que "aguanta" lo que sobrevivió el paso 2 completo
(instrumento auditado + ataque superado). Todo lo demás queda fuera del registro, sin excepción
por prisa o porque el número es bonito.

**Rama aparte, siempre etiquetada: investigar** — exploración libre, sin gate. Nunca se mezcla
con el paso 4 sin pasar primero por 1–2 ella misma.

## Por qué el paso 2 (auditar el instrumento) es el que importa

El resto del bucle (0, 1, 3, 4) ya estaba validado por este mismo proyecto: congelar alcance, una
pregunta con refutadores, y escribir una vez sacaron al paper de una racha de reencuadres. Lo que
falló, y pasó varias auditorías con CI en verde, fue confiar en un resultado sin comprobar que el
propio experimento medía lo que decía medir: una columna de coste que mezclaba operaciones
distintas por fila, y una regla de comparación que usaba la misma etiqueta como entrada y como
verdad de referencia. Ningún chequeo de consistencia genérico atrapa esto — hace falta juicio
sobre qué mide el instrumento, aplicado antes de fiarse del número, no después.

## Cómo se instancia aquí

Dos ejemplos ya en este repo, con nombres distintos pero la misma forma:

- **Para el paper** (`paper/claims.md`): problema = la pregunta registrada en la cabecera del
  archivo; hipótesis+refutadores = las filas "F1/F2/Bound"; atacar = escribir el script en
  `bench/` o `tools/`; registrar = el estado `checked` verificado por
  `tools/verify_paper_tables.py`; investigar = cifras de scratchpad, nunca citadas como
  resultado.
- **Para el código** (`tests/`): problema = el contrato de una función; hipótesis+refutadores =
  el test, escrito antes, en rojo; atacar(a) = comprobar que el test falla por la razón correcta,
  no por accidente; atacar(b) = correr en rojo, implementar lo mínimo, pasar a verde; registrar =
  el test entra a la suite como regresión permanente.

Ninguno de los dos instrumenta el paso 2(a) de forma automática todavía — es juicio manual en
ambos casos. Si en algún proyecto futuro se automatiza parte de esa auditoría (por ejemplo, un
chequeo de fuga de etiquetas), documentarlo aquí como un tercer ejemplo.
