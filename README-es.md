# dsh-emergency-plan — Completitud de los elementos del plan de emergencia y localización por página a nivel de cláusula

[![DSH Market](https://raw.githubusercontent.com/2BingLing/dsh-market/master/assets/readme/badge-listed-en.svg)](https://dsh.market/)

`dsh-emergency-plan` lee un plan de emergencia —su árbol de secciones, títulos, números de página y texto— y comprueba la completitud de los elementos de ese plan frente a la guía de redacción: qué elementos están presentes, cuáles faltan, cuáles aparecen solo como título sin texto debajo y dónde se sitúa cada uno, por página cuando el material trae números de página y por línea en caso contrario. Aplica un paquete de reglas versionado al tipo de plan que declara el material, y cada hallazgo indica la cláusula de la que procede y si esa cláusula es un requisito directo, un principio o una configuración local; una comprobación que no pudo ejecutarse lo dice en `skipped` en lugar de pasar en silencio.

## Cómo se ve la salida

![Terminal demo of dsh-emergency-plan: real output over its EP-004 fixture](https://raw.githubusercontent.com/PerryLink/dsh-emergency-plan/main/docs/assets/dsh-emergency-plan-demo.png)

Salida real de este plugin sobre su propio fixture de prueba `EP-004` — no es un montaje. El paquete de reglas no inventa citas, así que cada hallazgo nombra la cláusula aplicada y advierte que su texto no se obtuvo.

## Qué responde

| Usted pregunta | Qué responde |
|---|---|
| El material no dice cuál de los tres tipos de plan es. ¿Qué ocurre? | `EP-004` informa de que el material no declara `planType`, porque cada uno de los tres tipos tiene su propia lista de elementos. Solo comprueba que la declaración exista, no que sea la correcta; mientras falte, `EP-002` y `EP-003` indican en `skipped` qué lista de elementos dieron por supuesta. |
| Un 综合应急预案 no tiene el capítulo 后期处置. ¿Se informa de ello? ¿Hace falta además un apartado 编制目的? | `EP-002` busca uno a uno los cinco elementos de primer nivel del capítulo 6 de la guía vigente (6.1~6.5) e informa de cada uno que no encuentra, así que un 后期处置 ausente sí se informa. 编制目的 no es uno de esos cinco: la edición vigente lo suprimió y el paquete solo lo admite como alias de 总则. El hallazgo es `warn`, porque la guía de redacción es una norma nacional recomendada, no obligatoria. |
| ¿Qué elementos son obligatorios en un 专项应急预案 y en un 现场处置方案? | `EP-001` exige los elementos 7.1~7.4 del 专项应急预案 y `EP-003` los 8.1~8.4 del 现场处置方案, e informa de cada elemento que no encuentra en el árbol de secciones; si el título existe pero no hay texto debajo, se informa como vacío. Ambas listas son mínimos, no listas cerradas —la cláusula del 现场处置 dice 包括但不限于—, de modo que un elemento de más no genera hallazgo. En `EP-001` el elemento 7.5 应急保障 sigue siendo recomendado; en `EP-003` la lista más corta de la 《生产安全事故应急预案管理办法》 se cita como base aparte y nunca se funde con la de la guía. |
| Tras fusionar dos planes, el mismo título de elemento aparece dos veces. ¿Se detecta? | `EP-007` informa de un elemento exigido que aparece más de una vez y enumera todos los títulos que coincidieron con él. Ninguna cláusula lo dice expresamente —el paquete lo deduce de la unicidad del orden del 目次—, por lo que queda limitado a `warn`, y el paquete pide confirmación humana, porque el duplicado suele venir de fusionar varios planes. Compara la lista de elementos que aplica, no todos los títulos repetidos del material. |
| El informe muestra `EP-005` como `skipped`. ¿Por qué? ¿Es obligatorio numerar las páginas del plan? | `EP-005` solo puede comparar el orden de los elementos cuando al menos dos de ellos llevan `page` o `line`; si no, lo dice en `skipped` en lugar de suponer un orden. `EP-006` trata los números de página como información de localización: guarda silencio cuando la proporción de secciones con página alcanza `minPageRatio` (0,5 por defecto) y, por debajo de esa proporción, solo emite un aviso de nivel `info`. Ambas quedan limitadas a `info` —la expectativa de orden se deduce de un apéndice informativo, no del cuerpo de la norma— y un plan sin páginas nunca se informa como incumplimiento de una cláusula: el informe localiza por número de línea. |
| ¿Por qué `EP-008` y `EP-009` aparecen en `skipped` en lugar de pasar? | Las dos esperan configuración. `EP-009` solo se ejecuta con `requireAttachments` en `true`, porque quien llama suele entregar el cuerpo del plan sin sus anexos y dar los anexos ausentes por faltantes sería engañoso; activada, busca los ocho elementos de anexo e informa de los que no encuentra. `EP-008` solo se ejecuta si hay `versionPatterns` configurados: con la lista vacía no dicta cómo debe escribirse el identificador de versión y, una vez configurada, solo comprueba si el marcador aparece en algún título de sección, nunca si el contenido de la revisión es correcto. |

## Normas que sigue

| Documento | Número | Reglas que lo citan |
|---|---|---|
| 《生产经营单位生产安全事故应急预案编制导则》 | GB/T 29639-2020 | EP-001, EP-002, EP-003, EP-004, EP-005, EP-006, EP-007, EP-008, EP-009 |
| 《生产安全事故应急预案管理办法》 | 国家安全生产监督管理总局令第88号（应急管理部令第2号修正） | EP-001, EP-002, EP-003, EP-009 |

**Boundary:** this plugin checks an **emergency plan's element completeness** against the drafting
guideline and locates each element by page, reporting literal differences against cited clauses. It is
not `dsh-rulefile-check` (which audits a regulatory document's legality) and not
`dsh-hidden-risk-map` (which maps a hazard ledger to determination clauses). It reads one plan and
reports which elements are present, absent or empty, and where.

> ### ⚠️ Two corrections this plugin is built on — please read
>
> **1. "八要素" is not a current requirement.** The familiar list — 总则, 事故风险描述, 应急组织机构及职责,
> 预警及信息报告, 应急响应, 信息公开, 后期处置, 保障措施, 应急预案管理 — belongs to
> **GB/T 29639—2013**, which has been **entirely replaced**. Its namesake is not found in any current
> national document. The standard in force, **GB/T 29639-2020**, gives the comprehensive plan **five**
> first-level elements in clause 6 (6.1 总则 / 6.2 应急组织机构及职责 / 6.3 应急响应 / 6.4 后期处置 /
> 6.5 应急保障), and its foreword records that **编制目的 was removed**. Any rule citing 2013 clause
> numbers is citing a withdrawn standard. This pack cites only the 2020 clause numbers, and a test
> asserts that the 2013 number never appears.
>
> **2. Page numbers have no mandatory basis.** No national document requires a plan to carry page
> numbers; the appendix that governs 目次 is a **资料性附录** (informative, not normative) and does not
> contain the word 页码. Page numbers are therefore treated as **locating information that helps a
> reviewer**, reported at `info`, and never phrased as "does not comply with X". When a plan carries no
> page numbers the report falls back to line numbers.

A third, smaller correction is recorded in the pack: 《生产安全事故应急预案管理办法》's correct version
is **国家安全生产监督管理总局令第88号 (2016), amended by 应急管理部令第2号 (2019)** — not a bare
"应急管理部令第2号" — and 国办发〔2013〕101号 has been replaced by 国办发〔2024〕5号.

## Compatibility

| Superficie | Estado |
|---|---|
| Harness | Rango de peers `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verificado para aceptar tanto `0.2.0-rc.2` como `0.2.1-alpha.1`. **No se declara `engines.dsh`**: no tiene lector y no puede rechazar ningún host |
| Node | `^22.19.0 || >=24.0.0` |
| Plataformas | Todas (ESM puro; sin código nativo, sin red, sin llamada al modelo) |
| Modo de herramienta | Funciona en `native`, `ptc` y `both`; para un directorio completo use `ptc` |

## What it does

La tabla de reglas, los campos y el comportamiento detallado están en [README.md](README.md#what-it-does) (versión principal en inglés). El plugin sólo enumera divergencias literales frente a las cláusulas citadas e indica en `skipped` cada comprobación que no pudo ejecutarse.

## Install

```sh
dsh plugin --profile <name> add dsh-emergency-plan
dsh --profile <name> --dump-config | grep 'dsh-emergency-plan'
```

## Configuration

Todos los parámetros ajustables viven en el esquema Schemastery de `src/config.ts`, por lo que se cambian desde `cordis.yml` sin tocar el código; los umbrales por regla están en el paquete de reglas bajo `rules/`.

| Clave | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `rulesFile` | string | `rules/emergency-plan.yaml` | Ruta del paquete de reglas, relativa a la raíz del paquete |
| `disabledRules` | string[] | `[]` | Ids de reglas que se dejan de ejecutar; cada una aparece en `skipped` |
| `onlyRules` | string[] | `[]` | Ejecutar solo estas reglas; vacío ejecuta todas |
| `skipNotes` | string | `""` | Nota añadida a cada motivo de `skipped` |
| `timeoutMs` | number | `120000` | Presupuesto de tiempo de espera cooperativo de la herramienta |

## Material format

Acepta JSON o YAML. El ejemplo completo de campos está en [README.md](README.md#material-format) (versión principal en inglés). Los campos son opcionales en la capa de lectura y los valida el motor, de modo que una exportación parcial produce hallazgos sobre lo que falta en lugar de un fallo.

## Rule sources

Los datos de las reglas están separados del código: cada regla lleva documento, número, cláusula en la numeración propia de la fuente, extracto literal y URL de origen. El cargador impone que el extracto sea una cita real de al menos ocho caracteres y que una comprobación basada sólo en un principio general (`kind: derived-from-principle`, tope `warn`) o en una política local (`kind: institutional-configuration`, tope `info`) nunca se declare `error`.

Los límites verificados y las conclusiones deliberadamente **no** afirmadas están en [README.md](README.md#rule-sources) (versión principal en inglés) y en `rules/evidence/`.

## Troubleshooting

- **El plugin se instala pero la herramienta no aparece**: compruebe que `main` resuelve a `lib/index.mjs` y que `pnpm run build` lo generó.
- **`dsh plugin add` rechaza el paquete**: la faixa de peers cubre `0.1.x` y `0.2.x`; fuera de ella, conceda una exención explícita con `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`.
- **Una regla no se ejecutó**: lea el arreglo `skipped`.
- **`check` informa `manifest-peers` como fallo**: es un problema conocido de `dsh-plugin-dev`; el runtime aplica la compatibilidad al instalar.
- **Los horarios parecen desplazados**: toda la aritmética es de hora local sobre las cadenas entregadas.

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-emergency-plan
```

El último comando copia el kit compartido de `../_shared` a `src/shared/`; vuelva a ejecutarlo tras cada cambio compartido.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-emergency-plan contributors.
