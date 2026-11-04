# Matriz de trazabilidad: resumen (generado)

Generado por `method-paper/prep/matrix/build_matrix.py` en el commit `(sin git)`; el último commit que cambió sus entradas (`paper/`, `bench/`, `tools/`, `polar_projector/`) es `(sin git)`. No editar a mano: se regenera con `python method-paper/prep/matrix/build_matrix.py`.

- Filas (apariciones de cifras en el manuscrito): 1325
- Chequeos del verificador: 281; con cadena de más de un carácter: 261
- Chequeos de más de un carácter que no casan con ninguna fila: 0
- Chequeos sin artefacto detectado al perturbar: 0
- Cadenas comprobadas que aparecen en más de un sitio del manuscrito: 85
- Cadenas compartidas por más de un chequeo: 31
- Cifras atadas por presencia: 420; con el chequeo en otra sección: 62

## Categoría lógica × estado

| Categoría | atada-presencia | atada-ubicada | atada-un-caracter | coincide-otra-cifra | datos-sin-prueba | declarada | en-artefacto | excluida | fijado-en-codigo | fijado-en-config | literal-en-codigo | por-decidir | por-mapear | presencia-dudosa | sin-respaldo | sin-respaldo-en-codigo | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| resultado | 420 | 26 | 8 | 4 | 1 |  |  |  |  |  |  |  |  | 11 | 9 |  | 479 |
| parametro |  |  |  |  |  |  |  |  | 10 | 97 | 27 |  |  |  |  | 2 | 136 |
| derivacion |  |  |  |  |  |  |  |  |  |  |  |  | 75 |  |  |  | 75 |
| entorno |  |  |  |  |  | 6 | 6 |  |  |  |  |  |  |  |  |  | 12 |
| referencia |  |  |  |  |  |  |  | 194 |  |  |  |  |  |  |  |  | 194 |
| texto |  |  |  |  |  |  |  | 185 |  |  |  |  |  |  |  |  | 185 |
| notacion |  |  |  |  |  |  |  | 217 |  |  |  |  |  |  |  |  | 217 |
| sin-clasificar |  |  |  |  |  |  |  |  |  |  |  | 27 |  |  |  |  | 27 |
| **Total** | 420 | 26 | 8 | 4 | 1 | 6 | 6 | 596 | 10 | 97 | 27 | 27 | 75 | 11 | 9 | 2 | **1325** |

## H1: cifras de resultado que no están atadas

Candidatas a refutar H1. Cada una pide revisión humana: la categoría la asignó una regla.

| Línea | Cifra | Estado | Regla | Datos | Contexto |
|---:|---|---|---|---|---|
| 148 | 10^3 | sin-respaldo | orden-de-magnitud |  | e, plausible values wrong by factors of   \(  |
| 148 | 10^5 | sin-respaldo | orden-de-magnitud |  | e values wrong by factors of   \( 10^3 \)–\(  |
| 408 | 25× | sin-respaldo | unidad-de-resultado |  |  stays flat as \( N \) grows — 2.7% across a  |
| 408 | 25× | sin-respaldo | unidad-de-resultado |  |  N \) grows — 2.7% across a 25× corpus and a  |
| 427 | 1.00× | coincide-otra-cifra | coincide-con-chequeo | §A  d=384 floor = 1.00376 | tabla L422 / fila '**`evaluate()` — per stimulus, prepared frame**' / columna 'Relative co |
| 604 | 1× | sin-respaldo | unidad-de-resultado |  |   |
| 626 | 2× | sin-respaldo | unidad-de-resultado |  | aying level: both t-SNE and UMAP-refit cross  |
| 991 | 25× | sin-respaldo | unidad-de-resultado |  | nd its per-stimulus latency is flat across a  |
| 1132 | 1.00× | coincide-otra-cifra | coincide-con-chequeo | §A  d=384 floor = 1.00376 | tabla L1130 / fila '16' / columna 'vs. \( d = 16 \)' |
| 1133 | 1.01× | coincide-otra-cifra | coincide-con-chequeo | §3.3 pca_fit_once worst lift = 1.00506; §3.4 kmeans2 worst l | tabla L1130 / fila '64' / columna 'vs. \( d = 16 \)' |
| 1134 | 1.15× | datos-sin-prueba | celda-de-tabla | scale.json:rules.pc1_extremes.unit.lift_per_step[1]; scale.j | tabla L1130 / fila '256' / columna 'vs. \( d = 16 \)' |
| 1136 | 1.45× | coincide-otra-cifra | coincide-con-chequeo | §3.4 isometric pc1_extremes median lift = 1.44867 | tabla L1130 / fila '1024' / columna 'vs. \( d = 16 \)' |
| 1137 | 2.85× | sin-respaldo | celda-de-tabla |  | tabla L1130 / fila '4096' / columna 'vs. \( d = 16 \)' |
| 1138 | 5.65× | sin-respaldo | celda-de-tabla |  | tabla L1130 / fila '8192' / columna 'vs. \( d = 16 \)' |

## Presencia dudosa: cadenas cortas casadas con un chequeo de otra sección

Pueden ser la misma cifra repetida (el 29× del resumen es el del §3.5) o una cifra distinta que se imprime igual. Solo leyendo se distingue.

| Línea | Cifra | Estado | Regla | Datos | Contexto |
|---:|---|---|---|---|---|
| 57 | 2.7% | presencia-dudosa | coincide-con-chequeo | §3  sweep flatness % = 2.74562 | ed frame, and a stateless call stays flat to  |
| 59 | 29× | presencia-dudosa | coincide-con-chequeo | §3.5 re-anchoring factor = 29.0714 | he recall of a query's 15 nearest neighbours  |
| 125 | 229× | presencia-dudosa | coincide-con-chequeo | §3.5 cost query-frame ratio, local PCA over re-anchored = 22 | coupled — and it still scores only 0.023, at  |
| 135 | 29× | presencia-dudosa | coincide-con-chequeo | §3.5 re-anchoring factor = 29.0714 | 3) — and raises local neighbourhood recovery  |
| 156 | 29× | presencia-dudosa | coincide-con-chequeo | §3.5 re-anchoring factor = 29.0714 | te does it   better.** Re-anchoring is worth  |
| 313 | 11 | presencia-dudosa | coincide-con-chequeo | §3.1 working set ratio = 11.2562 | k] ← σ    ▷ no e_k, no dot, no norm pass   |
| 863 | 29× | presencia-dudosa | coincide-con-chequeo | §3.5 re-anchoring factor = 29.0714 | he query raises local neighbourhood recovery  |
| 946 | 409 | presencia-dudosa | coincide-con-chequeo | §2.1 poles window count of pole A's part = 409 | .2), the initial   500-chunk window contains  |
| 946 | 91 | presencia-dudosa | coincide-con-chequeo | §2.1 poles window count of pole B's part = 91 | unk window contains 409 chunks of P1_GOD and  |
| 1148 | 24× | presencia-dudosa | coincide-con-chequeo | §3.1 sliding-window PCA over project() = 24.2773 | v2`, §3.2) — costing only 1.16× more despite  |
| 1148 | 90% | presencia-dudosa | coincide-con-chequeo | §3.1 dispatch share at d=384 % (nearest ten) = 90 | × the floating-point work, because **roughly  |

## Atadas solo por valor: cifras de un carácter

El verificador las cuenta pero no las ubica. Aquí se aceptan si un chequeo de la misma sección tiene el mismo valor y comparte palabras con el texto que las rodea.

| Línea | Cifra | Estado | Regla | Datos | Contexto |
|---:|---|---|---|---|---|
| 499 | 7 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 random_fixed still steps = 7; §3.2 pca_fit_once still s | tabla L497 / fila 'Fixed random projection, \( 2 \times d \)' / columna 'Still steps' |
| 500 | 7 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 random_fixed still steps = 7; §3.2 pca_fit_once still s | tabla L497 / fila 'PCA, fit once on the initial window' / columna 'Still steps' |
| 501 | 7 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 random_fixed still steps = 7; §3.2 pca_fit_once still s | tabla L497 / fila 'Polar Projector, fixed anchor' / columna 'Still steps' |
| 502 | 0 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 polar_moving still steps = 0; §3.2 umap_refit still ste | tabla L497 / fila 'Polar Projector, moving anchor' / columna 'Still steps' |
| 503 | 7 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 random_fixed still steps = 7; §3.2 pca_fit_once still s | tabla L497 / fila 'UMAP, fit once + `transform()`' / columna 'Still steps' |
| 504 | 0 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 polar_moving still steps = 0; §3.2 umap_refit still ste | tabla L497 / fila 'UMAP, refit per step' / columna 'Still steps' |
| 505 | 0 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 polar_moving still steps = 0; §3.2 umap_refit still ste | tabla L497 / fila 't-SNE, refit per step' / columna 'Still steps' |
| 518 | 7 | atada-un-caracter | coincide-con-chequeo-un-caracter | §3.2 random_fixed still steps = 7; §3.2 pca_fit_once still s | olumn does not show.* Four arms are still at  |

## Chequeos que no casan con ninguna fila

Si no es cero, el lector de la matriz no reconoce una cifra que el verificador sí encuentra.

- Ninguno.

## Chequeos sin artefacto detectado al perturbar

- Ninguno.

Perturbaciones que rompieron el cálculo (no aportan dependencia):

- `conditioning.json`: round: StopIteration

## Sin clasificar (por decidir)

- L302 `2` … ce per active context      require  d ≥ ⟨2⟩ ,  finite inputs,  δ > 0,
- L302 `0` … require  d ≥ 2,  finite inputs,  δ > ⟨0⟩ ,  ε_norm > 0,  ε_colline
- L302 `0` … ≥ 2,  finite inputs,  δ > 0,  ε_norm > ⟨0⟩ ,  ε_collinear > 0   1  i
- L302 `0` … ts,  δ > 0,  ε_norm > 0,  ε_collinear > ⟨0⟩ 1  if ‖c₁‖₂ > ε_norm
- L303 `1` … δ > 0,  ε_norm > 0,  ε_collinear > 0 ⟨1⟩ if ‖c₁‖₂ > ε_norm  then
- L303 `0` … _norm  then  ĉ₁ ← c₁/‖c₁‖₂   else  ĉ₁ ← ⟨0⟩ 2  c_A⊥ ← c_A − ⟨c_A,
- L304 `2` … m  then  ĉ₁ ← c₁/‖c₁‖₂   else  ĉ₁ ← 0 ⟨2⟩ c_A⊥ ← c_A − ⟨c_A, ĉ₁⟩·
- L305 `3` … ▷ O(d) ⟨3⟩ c_B⊥ ← c_B − ⟨c_B, ĉ₁⟩·
- L306 `4` … ▷ O(d) ⟨4⟩ d_raw ← c_A⊥ − c_B⊥   5
- L307 `5` … 4  d_raw ← c_A⊥ − c_B⊥ ⟨5⟩ if ‖d_raw‖₂ ≥ ε_colline
- L308 `6` … 5  if ‖d_raw‖₂ ≥ ε_collinear then ⟨6⟩ v_dipole ← d_raw
- L309 `7` … 6      v_dipole ← d_raw ⟨7⟩ else
- L310 `8` … ▷ collinear fallback, Prop. 2 ⟨8⟩ k ← argmin_i |ĉ₁[i]
- L311 `9` … ▷ canonical; ties break by index ⟨9⟩ σ ← √(1 − ĉ₁[k]²)
- L311 `1` … cal; ties break by index   9      σ ← √( ⟨1⟩ − ĉ₁[k]²)
- L312 `10` … ▷ closed form, Remark above ⟨10⟩ u⊥ ← (−ĉ₁[k]/σ)·ĉ₁
- L313 `2` … o dot, no norm pass  11      v_dipole ← ⟨2⟩ δ·u⊥  12  return frame ←
- L314 `12` … 11      v_dipole ← 2δ·u⊥ ⟨12⟩ return frame ← (c₁, ĉ₁,
- L317 `13` … ▷ per stimulus, hot path ⟨13⟩ r ← (vₙ − c₁) − ⟨vₙ − c
- L318 `14` … ▷ O(d) ⟨14⟩ λ* ← ⟨r, v_dipole⟩ / ‖v
- L319 `−1` … ched in the frame  15  λ  ← min(max(λ*, ⟨−1⟩ ), 1)                   ▷
- L319 `1` … in the frame  15  λ  ← min(max(λ*, −1), ⟨1⟩ )                   ▷ sca
- L321 `17` … ▷ vector form, never scalar ⟨17⟩ return (λ, d_esc) ─────
- L385 `1` … : \( \|r\|_2 = \sin\theta \), rising to ⟨1⟩ at \( \theta = 90° \) an
- L386 `0` … \theta = 90° \) and falling back toward ⟨0⟩ as \( \theta \to 180° \)
- L455 `1` … h sides, which pulls every ratio toward ⟨1⟩ ; net of it the operator
- L767 `60` … he table is shorter than one frame of a ⟨60⟩ Hz display, so cost does

## Reglas que asignaron cada categoría

| Categoría | Regla | Filas |
|---|---|---:|
| derivacion | angulo | 5 |
| derivacion | formula | 70 |
| entorno | entorno | 12 |
| notacion | codigo-o-enlace | 12 |
| notacion | declaraciones | 2 |
| notacion | identificador | 24 |
| notacion | subindice-o-exponente | 179 |
| parametro | coincide-con-config | 29 |
| parametro | columna-de-parametros | 21 |
| parametro | denominador | 10 |
| parametro | parametro-explicito | 37 |
| parametro | parametro-por-contexto | 39 |
| referencia | cita-en-el-texto | 27 |
| referencia | seccion-de-referencias | 167 |
| resultado | celda-de-tabla | 3 |
| resultado | celda-tabla-ubicada | 26 |
| resultado | coincide-con-chequeo | 435 |
| resultado | coincide-con-chequeo-un-caracter | 8 |
| resultado | orden-de-magnitud | 2 |
| resultado | unidad-de-resultado | 5 |
| sin-clasificar | sin-regla | 27 |
| texto | encabezado | 14 |
| texto | numeracion-de-lista | 2 |
| texto | portada | 12 |
| texto | referencia-interna | 157 |
