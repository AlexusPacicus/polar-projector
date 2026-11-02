# Arquitectura de ingeniería

Notas personales de Alexis Zapico Fernández sobre cómo está construido este repo, no solo qué
hace. Compañero de [`docs/METHODOLOGY.md`](METHODOLOGY.md): aquí se describe el pipeline
concreto que ya instancia el bucle general en este proyecto.

## El pipeline de evidencia

No es "código + paper al lado". Es un pipeline de cinco etapas, cada una verificando la
anterior, con el manuscrito como salida, no como fuente:

```
polar_projector/  →  tests/         →  bench/ (+_harness.py) →  paper/claims.md      →  tools/verify_paper_tables.py  →  manuscrito
  (operador,          (correctness,      (medición, protocolo      (registro: cada          (gate de CI: recomputa,          (única fuente,
   533 líneas)         1.389 líneas,      compartido, 3.135         afirmación → script       compara cifra a cifra,           1.222 líneas)
                        800 tests CI)     líneas)                   → artefacto → chequeo,     exige presencia,
                                                                     138 líneas)                falla si el registro miente)
```

## Por qué está así, etapa por etapa

- **`bench/_harness.py` no es un helper de timing, es la especificación metodológica
  ejecutable**: por qué se mide por llamada y no amortizado, por qué mediana de repeticiones y
  no media, por qué interleaving de brazos (deriva térmica del M1 — throttling térmico, una
  pasada de cada cuatro se infla 20%). Documenta también qué NO controla (afinidad de CPU
  descartada por no existir en macOS/arm64). Cualquier script nuevo en `bench/` hereda esto
  gratis con solo llamarlo.

- **`paper/claims.md` es un registro tipado**: siete estados (`checked`, `not-in-ci`,
  `mismatch`, `unbacked`, `pending`, `construction`, `remove`) y tres niveles de pre-registro
  (`yes (commit)`, `no`, `post hoc`). Eso separa explícitamente "medido" de "medido y declarado
  por adelantado", que es la distinción que evita que una cifra exploratoria se cuele como
  resultado.

- **`tools/verify_paper_tables.py` (735 líneas) es más grande que el propio operador.**
  Recomputa los apéndices B/C, compara cada tabla del manuscrito celda a celda contra
  `bench/results/*.json`, exige que todo claim `checked` nombre un chequeo real (con fallo si
  una fila del registro es demasiado amplia o está mal escapada), y exige que cada cifra
  comprobada aparezca impresa en el manuscrito salvo `AWAITING_TEXT`. No son "tests para el
  paper": es un verificador de consistencia entre tres artefactos independientes (código, JSON
  congelado, prosa).

## El límite declarado

El propio README lo dice con una honestidad poco común:

> It checks consistency between the manuscript and its artifacts. It cannot catch a benchmark
> that measures something other than what the paper says it measures.

Esa frase es la arquitectura completa resumida en una línea, y también el límite exacto que
causó los problemas reales del proceso (ver la retrospectiva de metodología): el verificador
atrapa que una cifra no cuadre, no que un experimento mida algo distinto de lo que dice medir.
Eso es juicio humano — el paso 2(a) de `docs/METHODOLOGY.md` — y no se automatiza aquí todavía.

## Qué es reutilizable tal cual en el siguiente proyecto

- El protocolo de `_harness.py` (warmup, mediana de repeticiones, interleaving, disclosure de
  host/threading) — es independiente del operador que mida.
- El vocabulario de estados de `claims.md` — sirve para cualquier registro de afirmaciones, no
  solo para este paper.
- El patrón del verificador: recomputar en vez de confiar, comparar celda a celda en vez de por
  bloque, exigir presencia en el texto con una única excepción explícita (`AWAITING_TEXT`), y
  fallar duro ante una fila del registro mal formada en vez de saltársela en silencio.

## Relación con `docs/METHODOLOGY.md`

Ese documento describe el bucle general de trabajo (problema → hipótesis+refutadores → atacar →
reformular-o-no → registrar). Este documento es la instancia concreta que ya existe en este
repo: `claims.md` + el verificador cubren los pasos 0, 1 y 4 para el paper; `tests/` los cubre,
en forma de TDD, para el código. Ninguno de los dos automatiza el paso 2(a) — auditar que el
instrumento mide lo que dice medir — sigue siendo criterio humano en ambos casos.
