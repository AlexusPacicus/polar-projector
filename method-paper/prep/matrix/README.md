# Matriz de trazabilidad: borrador v0

Instrumento para H1 del paper de método, tal como quedó en el planteamiento: **toda cifra de resultado impresa en
el manuscrito está atada a la salida del código.** Es también la base de H2: con cada cifra enlazada a sus datos, a
su código y a sus pruebas, se puede ver qué eslabón falló en cada corrección.

Fase 0 (`method-paper/BRIEF.md:30-32`): lo escribió un agente (Claude) fuera del canal gobernado, y está sin revisar.
Nada de esta carpeta toca un archivo existente.

## Principios

1. **El origen de una cifra es intocable: la única evidencia es la salida del código.** Eso significa los
   artefactos de `bench/results/`, escritos por scripts versionados, y lo que el verificador recalcula (Apéndices
   B y C).
2. **Lo que sale de un LLM es una afirmación que hay que verificar, no evidencia.** Esto incluye el manuscrito,
   `paper/claims.md`, los mensajes de commit y este mismo script. Por eso:
   - el registro se contrasta, no se da por bueno;
   - los chequeos se obtienen ejecutando el verificador, no leyendo su código;
   - el script se somete a pruebas negativas (`test_matrix.py`).
3. **La unidad de análisis es la categoría lógica de cada cifra,** de la mano de su estructura: dónde está y de
   qué depende. Cada categoría exige una evidencia distinta.

## Uso

```bash
python method-paper/prep/matrix/build_matrix.py
```

```bash
python method-paper/prep/matrix/test_matrix.py
```

El primero escribe `matrix.csv` (una fila por aparición de una cifra) y `summary.md` (el resumen) en esta carpeta.
El segundo trabaja sobre copias temporales del repositorio. Ninguno necesita red. Basta con numpy; los paquetes del
extra `bench` no hacen falta.

Las cifras del borrador están en `summary.md`, que se genera y no se edita a mano. Este README no las copia: hacerlo
sería repetir el problema que estudia el paper.

## Columnas de `matrix.csv`

| Columna | Qué es | De dónde sale |
|---|---|---|
| `linea`, `seccion`, `region`, `contexto` | Dónde está la cifra: línea, sección, zona del documento y contexto (prosa, tabla, fórmula, leyenda, lista) | Lectura del manuscrito por código |
| `tabla` | Para celdas de tabla, la fila y la columna | Cabecera y primera celda de la tabla |
| `cifra`, `valor` | La cifra tal como se imprime y su valor | Ídem |
| `categoria`, `regla` | Categoría lógica y la regla que la asignó | Reglas fijas en `build_matrix.py`, en orden |
| `pruebas`, `ubicada` | Chequeos del verificador que cubren la cifra, y si la ubican o solo la encuentran en algún sitio | Ejecución del verificador (`_artifact_checks()`); tablas B y C comparadas celda a celda |
| `datos` | Valor del artefacto o del recálculo con que coincide | Artefactos y verificador |
| `codigo` | Script que escribe ese artefacto | El `--out` por defecto de cada script |
| `depende_de` | Artefacto ← script ← módulos y datos de los que depende el script | Imports del script, recorridos de forma transitiva |
| `registro` | Filas de `paper/claims.md` que nombran esos chequeos | Misma regla de prefijos que el verificador |
| `estado` | Si la cifra está atada, y cómo | Derivado de lo anterior |
| `nota` | Ambigüedades: cadena compartida, chequeo de otra sección o fila, sin fila en el registro | Ídem |

## Categorías lógicas y la evidencia que exige cada una

| Categoría | Qué es | Evidencia exigida | Estados posibles |
|---|---|---|---|
| resultado | Cifra producida al ejecutar código, medida o derivada | Un artefacto y un chequeo que compare la cifra impresa con él | atada-ubicada, atada-presencia, atada-un-caracter, presencia-dudosa, coincide-otra-cifra, datos-sin-prueba, sin-respaldo, prueba-falla |
| parametro | Un ajuste del experimento: N, d, K, semillas, rejillas | Que el artefacto lo registre en su `config` (salida del código) o, como evidencia débil, que aparezca como literal en el código | fijado-en-config, fijado-en-codigo, literal-en-codigo, sin-respaldo-en-codigo |
| derivacion | Un hecho matemático: cotas, identidades, constantes de las proposiciones | Un test (`pytest`); el enlace con los tests está por hacer | por-mapear |
| entorno | Máquina y versiones | Que el artefacto lo registre en `host` | en-artefacto, declarada |
| referencia | Años, volúmenes y páginas de la bibliografía, y citas en el texto | Externa al código; fuera de H1 | excluida |
| texto | Numeración del documento: secciones, proposiciones, pasos, listas | Ninguna: no es una afirmación | excluida |
| notacion | Dígitos de nombres y notación: `c_1`, `‖·‖₂`, `float64`, `P1_GOD` | Ninguna | excluida |
| sin-clasificar | Lo que ninguna regla clasifica | La decides tú | por-decidir |

Qué significa cada estado de un resultado:

- **atada-ubicada:** celdas de los Apéndices B y C. La celda se compara con la constante del verificador y esa
  constante con el recálculo. En B la tolerancia es de ±2 décadas (`tools/verify_paper_tables.py:70`), así que
  comprueba el régimen, no el valor.
- **atada-presencia:** un chequeo publica esa cadena y su valor coincide con el artefacto, pero el verificador solo
  comprueba que la cadena aparezca en algún sitio. En tablas se exige además que el chequeo nombre la fila de la
  celda, o la columna si es de la misma sección.
- **atada-un-caracter:** cifras de un carácter. El verificador no las ubica; aquí se aceptan si un chequeo de la
  misma sección tiene el mismo valor y comparte palabras con el texto alrededor.
- **presencia-dudosa:** cadena corta (tres caracteres o menos) casada solo con un chequeo de otra sección. Puede ser
  la misma cifra repetida o una distinta que se imprime igual.
- **coincide-otra-cifra:** celda cuya cadena coincide con un chequeo que no nombra ni su fila ni su columna.
- **datos-sin-prueba:** sin chequeo. Algún artefacto contiene ese valor a la precisión impresa, y puede ser casual.
- **sin-respaldo:** ni chequeo ni dato.
- **prueba-falla:** el chequeo existe pero no coincide.

## Qué demuestran las pruebas negativas

`test_matrix.py` planta un error en una copia temporal y exige una reacción concreta:

| Prueba | Error plantado | Matriz | Verificador |
|---|---|---|---|
| `test_planted_figure` | Una cifra nueva en la prosa del §3.5 | sin-respaldo | Sigue en verde |
| `test_altered_occurrence` | Una de las apariciones de 0.981 cambiada | No atada | Sigue en verde: la cadena sigue impresa en otros sitios |
| `test_registry_row_removed` | La fila C13 borrada del registro | Cifras con chequeo y sin fila | Sigue en verde |
| `test_appendix_c_cell` | Una celda del Apéndice C | prueba-falla | Falla |
| `test_artifact_changed` | El valor de `reanchor.json` detrás de 0.981 | prueba-falla en todas sus apariciones | Falla |
| `test_reference_number` | Un año dentro de una referencia | Excluida por categoría | No aplica |

Las tres primeras son lo que el verificador no puede ver: comprueba en una dirección, del registro al texto
(`tools/verify_paper_tables.py:599-627`). Solo lee el manuscrito en sentido inverso para las tablas de los
Apéndices B y C (`tools/verify_paper_tables.py:165-201`).

**La segunda prueba encontró un defecto del propio diseño.** La categoría "resultado" se asignaba sobre todo porque
la cifra coincidía con un chequeo, y una cifra equivocada deja de coincidir: se salía de la categoría y H1 la habría
contado de menos. Se corrigió con una regla que no mira la evidencia (`decimal-en-texto`).

## Límites conocidos de la v0

1. **Las categorías salen de reglas de contexto escritas por un LLM.** `summary.md` lista cuántas filas asignó cada
   regla y las que quedan sin clasificar: hay que revisarlas.
2. **Igualdad de cadenas no es igualdad de cifra.** "Presencia" acepta tanto repeticiones legítimas como
   coincidencias. Las cadenas cortas de otra sección se marcan como dudosas y en tablas se exige fila o columna,
   pero solo leyendo se decide del todo.
3. **El emparejamiento de fila y chequeo se hace por palabras y prefijos.** Falla si el código y el texto nombran
   distinto la misma cosa: `pc1_extremes` se imprime como "First-PC deciles" y se resolvió por la columna.
4. **`datos-sin-prueba` y `literal-en-codigo` son evidencia débil:** pueden ser coincidencias.
5. **Las derivaciones están por enlazar** con sus tests (filas A1, A14 y A15 del registro).
6. **Los números escritos con letras** ("seven", "two") no entran.
7. **"Intocable" no está comprobado para los artefactos.** Los deterministas se podrían regenerar aquí y compararse
   byte a byte; los de tiempos no, porque dependen de la máquina. Es el siguiente paso para que el principio 1 sea
   una comprobación y no un supuesto.
8. **Dependencias por perturbación:** un chequeo cuyo valor no cambia con ninguna perturbación quedaría sin
   artefacto. `summary.md` los cuenta.

## Cómo sigue hacia H2

Las columnas `codigo` y `depende_de` separan el objeto medido (`polar_projector/`), el instrumento (`bench/`,
`tools/`) y los datos (`bench/data/`). Con la matriz ejecutada en cada commit del historial, cada corrección se
podrá clasificar solo con salida de código:

- **transcripción:** cambió la cifra impresa y no el artefacto;
- **instrumento:** cambió el artefacto porque cambió su script;
- **objeto:** cambió el operador.

Eso sustituye la clasificación por rutas de `case-data.md` §5.3, que sale de mensajes de commit, es decir, de
salida de LLM.

## Decisiones del 2026-11-02 y lo que queda

Decisiones del autor:

1. **Las derivables cuentan como atadas, pero solo si se comprueban:** una fórmula declarada sobre salida del
   código, recalculada desde los artefactos y comparada a la precisión impresa. El 2026-11-03 se precisó como columna
   de raíz e interacción (`../outline.md`, "Decisions taken on 2026-11-03", decisión 7).
2. **Esta carpeta entra en las rutas gobernadas.** La añade el autor al brief el día 1 (`method-paper/BRIEF.md:36`,
   `:66-71`), porque los agentes no modifican el brief (`method-paper/BRIEF.md:4-5`).

Por qué quedan sin atar o sin clasificar cifras en esta versión. Es una lectura del agente apoyada en un recálculo
exploratorio hecho en la sesión, todavía no en un chequeo:

- **Sin atar** (`summary.md:27-46`):
  - Las derivables de salida del código: la columna "vs. d = 16" del Apéndice A, "25×", "10³–10⁵" del §1 y el umbral
    "2×".
  - Dos definiciones que la regla del signo × tomó por resultados: "1×" y el "1.00×" de la fila de referencia del
    §3.1.
- **Sin clasificar** (`summary.md:94-99`):
  - Matemáticas escritas en prosa (líneas 349, 350 y 419 del manuscrito).
  - Un supuesto externo que ningún código produce: "60 Hz", línea 731.

Las correcciones de reglas y las comprobaciones de derivables se aplican el día 1, con el protocolo ya registrado y
antes de la ejecución definitiva. Aplicarlas hoy sería seguir ajustando el instrumento a la vista de sus resultados.

Queda por hacer:

1. Revisar las cifras dudosas de `summary.md`.
2. Confirmar el protocolo o cambiarlo antes de registrarlo.
