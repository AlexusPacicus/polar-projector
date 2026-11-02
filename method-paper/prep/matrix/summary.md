# Matriz de trazabilidad: resumen (generado)

Generado por `method-paper/prep/matrix/build_matrix.py` en el commit `ad531cf`; el último commit que cambió sus entradas (`paper/`, `bench/`, `tools/`, `polar_projector/`) es `0b15002`. No editar a mano: se regenera con `python method-paper/prep/matrix/build_matrix.py`.

- Filas (apariciones de cifras en el manuscrito): 1344
- Chequeos del verificador: 281; con cadena de más de un carácter: 261
- Chequeos de más de un carácter que no casan con ninguna fila: 0
- Chequeos sin artefacto detectado al perturbar: 0
- Cadenas comprobadas que aparecen en más de un sitio del manuscrito: 86
- Cadenas compartidas por más de un chequeo: 31
- Cifras atadas por presencia: 420; con el chequeo en otra sección: 62

## Categoría lógica × estado

| Categoría | atada-presencia | atada-ubicada | atada-un-caracter | coincide-otra-cifra | datos-sin-prueba | declarada | en-artefacto | excluida | fijado-en-codigo | fijado-en-config | literal-en-codigo | por-decidir | por-mapear | presencia-dudosa | sin-respaldo | sin-respaldo-en-codigo | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| resultado | 420 | 26 | 8 | 4 | 1 |  |  |  |  |  |  |  |  | 10 | 9 |  | 478 |
| parametro |  |  |  |  |  |  |  |  | 10 | 95 | 27 |  |  |  |  | 2 | 134 |
| derivacion |  |  |  |  |  |  |  |  |  |  |  |  | 84 |  |  |  | 84 |
| entorno |  |  |  |  |  | 6 | 6 |  |  |  |  |  |  |  |  |  | 12 |
| referencia |  |  |  |  |  |  |  | 194 |  |  |  |  |  |  |  |  | 194 |
| texto |  |  |  |  |  |  |  | 190 |  |  |  |  |  |  |  |  | 190 |
| notacion |  |  |  |  |  |  |  | 248 |  |  |  |  |  |  |  |  | 248 |
| sin-clasificar |  |  |  |  |  |  |  |  |  |  |  | 4 |  |  |  |  | 4 |
| **Total** | 420 | 26 | 8 | 4 | 1 | 6 | 6 | 632 | 10 | 95 | 27 | 4 | 84 | 10 | 9 | 2 | **1344** |

## H1: cifras de resultado que no están atadas

Candidatas a refutar H1. Cada una pide revisión humana: la categoría la asignó una regla.

| Línea | Cifra | Estado | Regla | Datos | Contexto |
|---:|---|---|---|---|---|
| 115 | 10^3 | sin-respaldo | orden-de-magnitud |  | e, plausible values wrong by factors of   \(  |
| 115 | 10^5 | sin-respaldo | orden-de-magnitud |  | e values wrong by factors of   \( 10^3 \)–\(  |
| 372 | 25× | sin-respaldo | unidad-de-resultado |  |  stays flat as \( N \) grows — 2.7% across a  |
| 372 | 25× | sin-respaldo | unidad-de-resultado |  |  N \) grows — 2.7% across a 25× corpus and a  |
| 391 | 1.00× | coincide-otra-cifra | coincide-con-chequeo | §A  d=384 floor = 1.00376 | tabla L386 / fila '**`evaluate()` — per stimulus, prepared frame**' / columna 'Relative co |
| 568 | 1× | sin-respaldo | unidad-de-resultado |  |   |
| 590 | 2× | sin-respaldo | unidad-de-resultado |  | aying level: both t-SNE and UMAP-refit cross  |
| 955 | 25× | sin-respaldo | unidad-de-resultado |  | nd its per-stimulus latency is flat across a  |
| 1097 | 1.00× | coincide-otra-cifra | coincide-con-chequeo | §A  d=384 floor = 1.00376 | tabla L1095 / fila '16' / columna 'vs. \( d = 16 \)' |
| 1098 | 1.01× | coincide-otra-cifra | coincide-con-chequeo | §3.3 pca_fit_once worst lift = 1.00506; §3.4 kmeans2 worst l | tabla L1095 / fila '64' / columna 'vs. \( d = 16 \)' |
| 1099 | 1.15× | datos-sin-prueba | celda-de-tabla | scale.json:rules.pc1_extremes.unit.lift_per_step[1]; scale.j | tabla L1095 / fila '256' / columna 'vs. \( d = 16 \)' |
| 1101 | 1.45× | coincide-otra-cifra | coincide-con-chequeo | §3.4 isometric pc1_extremes median lift = 1.44867 | tabla L1095 / fila '1024' / columna 'vs. \( d = 16 \)' |
| 1102 | 2.85× | sin-respaldo | celda-de-tabla |  | tabla L1095 / fila '4096' / columna 'vs. \( d = 16 \)' |
| 1103 | 5.65× | sin-respaldo | celda-de-tabla |  | tabla L1095 / fila '8192' / columna 'vs. \( d = 16 \)' |

## Presencia dudosa: cadenas cortas casadas con un chequeo de otra sección

Pueden ser la misma cifra repetida (el 29× del resumen es el del §3.5) o una cifra distinta que se imprime igual. Solo leyendo se distingue.

| Línea | Cifra | Estado | Regla | Datos | Contexto |
|---:|---|---|---|---|---|
| 24 | 2.7% | presencia-dudosa | coincide-con-chequeo | §3  sweep flatness % = 2.74562 | ed frame, and a stateless call stays flat to  |
| 26 | 29× | presencia-dudosa | coincide-con-chequeo | §3.5 re-anchoring factor = 29.0714 | he recall of a query's 15 nearest neighbours  |
| 92 | 229× | presencia-dudosa | coincide-con-chequeo | §3.5 cost query-frame ratio, local PCA over re-anchored = 22 | coupled — and it still scores only 0.023, at  |
| 102 | 29× | presencia-dudosa | coincide-con-chequeo | §3.5 re-anchoring factor = 29.0714 | 3) — and raises local neighbourhood recovery  |
| 123 | 29× | presencia-dudosa | coincide-con-chequeo | §3.5 re-anchoring factor = 29.0714 | te does it   better.** Re-anchoring is worth  |
| 827 | 29× | presencia-dudosa | coincide-con-chequeo | §3.5 re-anchoring factor = 29.0714 | he query raises local neighbourhood recovery  |
| 910 | 409 | presencia-dudosa | coincide-con-chequeo | §2.1 poles window count of pole A's part = 409 | .2), the initial   500-chunk window contains  |
| 910 | 91 | presencia-dudosa | coincide-con-chequeo | §2.1 poles window count of pole B's part = 91 | unk window contains 409 chunks of P1_GOD and  |
| 1113 | 24× | presencia-dudosa | coincide-con-chequeo | §3.1 sliding-window PCA over project() = 24.2773 | v2`, §3.2) — costing only 1.16× more despite  |
| 1113 | 90% | presencia-dudosa | coincide-con-chequeo | §3.1 dispatch share at d=384 % (nearest ten) = 90 | × the floating-point work, because **roughly  |

## Atadas solo por valor: cifras de un carácter

El verificador las cuenta pero no las ubica. Aquí se aceptan si un chequeo de la misma sección tiene el mismo valor y comparte palabras con el texto que las rodea.

| Línea | Cifra | Estado | Regla | Datos | Contexto |
|---:|---|---|---|---|---|
| 463 | 7 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 random_fixed still steps = 7; §3.2 pca_fit_once still s | tabla L461 / fila 'Fixed random projection, \( 2 \times d \)' / columna 'Still steps' |
| 464 | 7 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 random_fixed still steps = 7; §3.2 pca_fit_once still s | tabla L461 / fila 'PCA, fit once on the initial window' / columna 'Still steps' |
| 465 | 7 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 random_fixed still steps = 7; §3.2 pca_fit_once still s | tabla L461 / fila 'Polar Projector, fixed anchor' / columna 'Still steps' |
| 466 | 0 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 polar_moving still steps = 0; §3.2 umap_refit still ste | tabla L461 / fila 'Polar Projector, moving anchor' / columna 'Still steps' |
| 467 | 7 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 random_fixed still steps = 7; §3.2 pca_fit_once still s | tabla L461 / fila 'UMAP, fit once + `transform()`' / columna 'Still steps' |
| 468 | 0 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 polar_moving still steps = 0; §3.2 umap_refit still ste | tabla L461 / fila 'UMAP, refit per step' / columna 'Still steps' |
| 469 | 0 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 polar_moving still steps = 0; §3.2 umap_refit still ste | tabla L461 / fila 't-SNE, refit per step' / columna 'Still steps' |
| 482 | 7 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 random_fixed still steps = 7; §3.2 pca_fit_once still s | olumn does not show.* Four arms are still at  |

## Chequeos que no casan con ninguna fila

Si no es cero, el lector de la matriz no reconoce una cifra que el verificador sí encuentra.

- Ninguno.

## Chequeos sin artefacto detectado al perturbar

- Ninguno.

Perturbaciones que rompieron el cálculo (no aportan dependencia):

- `conditioning.json`: round: StopIteration

## Sin clasificar (por decidir)

- L349 `1` … : \( \|r\|_2 = \sin\theta \), rising to ⟨1⟩ at \( \theta = 90° \) an
- L350 `0` … \theta = 90° \) and falling back toward ⟨0⟩ as \( \theta \to 180° \)
- L419 `1` … h sides, which pulls every ratio toward ⟨1⟩ ; net of it the operator
- L731 `60` … he table is shorter than one frame of a ⟨60⟩ Hz display, so cost does

## Reglas que asignaron cada categoría

| Categoría | Regla | Filas |
|---|---|---:|
| derivacion | angulo | 5 |
| derivacion | formula | 79 |
| entorno | entorno | 12 |
| notacion | codigo-o-enlace | 12 |
| notacion | declaraciones | 3 |
| notacion | identificador | 25 |
| notacion | subindice-o-exponente | 208 |
| parametro | coincide-con-config | 27 |
| parametro | columna-de-parametros | 21 |
| parametro | denominador | 10 |
| parametro | parametro-explicito | 37 |
| parametro | parametro-por-contexto | 39 |
| referencia | cita-en-el-texto | 27 |
| referencia | seccion-de-referencias | 167 |
| resultado | celda-de-tabla | 3 |
| resultado | celda-tabla-ubicada | 26 |
| resultado | coincide-con-chequeo | 434 |
| resultado | coincide-con-chequeo-un-caracter | 8 |
| resultado | orden-de-magnitud | 2 |
| resultado | unidad-de-resultado | 5 |
| sin-clasificar | sin-regla | 4 |
| texto | encabezado | 14 |
| texto | numeracion-de-lista | 2 |
| texto | paso-de-algoritmo | 17 |
| texto | portada | 1 |
| texto | referencia-interna | 156 |
