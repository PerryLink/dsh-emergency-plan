# dsh-emergency-plan — 应急预案要素齐备性与条款级页码定位

`dsh-emergency-plan` 读取一份应急预案——它的章节树、标题、页码与正文——核对这份预案的要素齐备性是否符合编制导则：哪些要素已出现、哪些缺失、哪些只有标题而标题之下没有正文，以及各要素在材料里的位置，材料带页码时按页定位、否则按行号定位。它按材料声明的预案类型套用版本化规则库，每条差异都写出所依据的条款，并标明该条款是直接规定、原则性推论还是本机构配置；无法执行的检查会在 `skipped` 中说明，而不是静默通过。

## 它回答什么问题

| 你会问 | 它怎么答 |
|---|---|
| 材料里没写这是三类预案中的哪一类，会怎么样？ | `EP-004` 会报出材料未声明 `planType`，因为三类预案的要素清单各不相同。它只核对是否声明，不判断该声明是否正确；声明缺失期间，`EP-002` 与 `EP-003` 会在 `skipped` 中写明自己假定按哪一份要素清单检查。 |
| 一份综合应急预案没有「后期处置」一章，会被报出吗？还需要写「编制目的」吗？ | `EP-002` 按现行导则第 6 章的五个一级要素（6.1~6.5）逐项查找，找不到「后期处置」就报出该缺项。「编制目的」不是这五个要素之一：现行版本已将其去掉，规则库只在「总则」的别名里兼容它。该条报出的是 `warn`，因为编制导则是推荐性国家标准，不是强制要求。 |
| 专项应急预案和现场处置方案分别必须有哪些要素？ | `EP-001` 要求专项应急预案具备 7.1~7.4 要素，`EP-003` 要求现场处置方案具备 8.1~8.4 要素，各自报出在章节树里找不到的要素；标题在、标题之下没有正文的，按「空」报出。两份清单都是下限而非封闭清单——现场处置那一条的原文写着「包括但不限于」——多写要素不会被报出。7.5 应急保障在 `EP-001` 中仍属推荐项；《生产安全事故应急预案管理办法》里较短的那份清单在 `EP-003` 中单独标注为依据，不与导则的清单合并表述。 |
| 合并两份预案后，同一个要素标题出现了两次，会被查出来吗？ | `EP-007` 会报出出现不止一次的必备要素，并列出匹配到它的各个标题。这件事没有明文条款可援引——规则库依据的是目次次序的唯一性，因而封顶 `warn`——且规则库要求人工确认，因为重复通常来自合并多份预案。它比对的只是它所适用的那份要素清单，不是材料里所有重复的标题。 |
| 报告里 `EP-005` 显示 `skipped`，为什么？预案一定要标页码吗？ | `EP-005` 只有在至少两个要素带 `page` 或 `line` 时才能核对顺序，否则在 `skipped` 中说明原因，而不是凭空假定一个顺序。`EP-006` 把页码当作辅助定位信息：带页码的章节占比达到 `minPageRatio`（默认 0.5）时它不报差异，低于该比例时只作 `info` 级提示。两条都封顶 `info`——顺序要求由资料性附录推论而来，标准正文并无此规定——没有页码时也不会被表述为「不符合某条规定」，报告改按行号定位。 |
| 为什么 `EP-008` 和 `EP-009` 出现在 `skipped` 里，而不是通过？ | 两条都在等配置。`EP-009` 只有把 `requireAttachments` 设为 `true` 才执行，因为调用方通常只给正文、不给附件，把「没给附件」当成缺项会误导；启用后它按八项附件条目查找，报出找不到的条目。`EP-008` 只有配置了 `versionPatterns` 才执行：列表为空时它不替使用方规定版本标识该写成什么样，配置后也只核对章节标题里是否出现配置的标识词，不判断修订内容是否正确。 |

## 依据的标准

| 文件 | 文号 | 引用它的规则 |
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

| 项目 | 状态 |
|---|---|
| Harness | 对等版本范围 `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` —— 已实测同时接受 `0.2.0-rc.2` 与 `0.2.1-alpha.1`。**刻意不声明 `engines.dsh`**：它没有任何读取者，也无法拒装任何宿主 |
| Node | `^22.19.0 || >=24.0.0` |
| 平台 | 全平台（纯 ESM；无原生代码、无联网、不调用模型） |
| 工具模式 | `native` / `ptc` / `both` 均可；批量校验整个目录时建议 `ptc`，schema 成本只付一次 |

## What it does

规则表、字段说明与行为细节见 [README.md](README.md#what-it-does)（英文主版本）。本插件只列出材料与所引条款之间的字面差异，并对无法执行的检查在 `skipped` 中逐项说明。

## Install

```sh
dsh plugin --profile <name> add dsh-emergency-plan
dsh --profile <name> --dump-config | grep 'dsh-emergency-plan'
```

## Configuration

全部可调参数都在 `src/config.ts` 的 Schemastery schema 中，只改 `cordis.yml` 即可生效，无需改代码；逐条阈值在 `rules/` 下的规则库文件里。

| 键 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `rulesFile` | string | `rules/emergency-plan.yaml` | 规则库文件路径，相对插件包根目录 |
| `disabledRules` | string[] | `[]` | 要停用的规则 id 列表；每条都会出现在 `skipped` 中 |
| `onlyRules` | string[] | `[]` | 只执行这些规则 id；留空表示执行全部规则 |
| `skipNotes` | string | `""` | 附加到每条 `skipped` 说明后的备注 |
| `timeoutMs` | number | `120000` | 工具协作式超时预算（毫秒） |

## Material format

支持 JSON 与 YAML。完整字段示例见 [README.md](README.md#material-format)（英文主版本）。字段在读取层是可选的，由检查引擎校验，因此部分导出的材料会产生"缺项"类差异，而不是让程序崩溃。

## Rule sources

规则数据与代码分离，每条规则都带文件名、文号、按原文自身编号体系的条款号、逐字摘录与来源地址。加载期强制：摘录必须是真实引文且不少于八个字符；依据仅为原则性条款（`kind: derived-from-principle`，严重级上限 `warn`）或本机构配置（`kind: institutional-configuration`，上限 `info`）的检查不得标为 `error`。夸大依据的规则库会在加载期失败，而不会产出一份看起来很有底气的报告。

核验中确认的边界与"刻意没有作出的结论"见 [README.md](README.md#rule-sources)（英文主版本）与随包的 `rules/evidence/` 目录。

## Troubleshooting

- **插件装上了但工具不出现**：确认 `main` 指向 `lib/index.mjs` 且 `pnpm run build` 已生成该文件；`main` 写错会让加载器静默跳过该条目。
- **`dsh plugin add` 报版本不兼容**：peer 范围覆盖 `0.1.x` 与 `0.2.x`；若运行时在其之外，可显式豁免：`dsh plugin --profile <name> allow-version <包名@版本> --dsh-version <runtime> --accept-risk`
- **某条规则没有执行**：查看 `skipped` 数组，其中写明了规则 id 与原因。
- **`check` 报 `manifest-peers` 失败**：静态检查器比对的是一份早于 0.2 世代的硬编码 peer 范围；安装期的 peer 校验以运行时为准。这是 `dsh-plugin-dev` 的已知上游问题。
- **时间看起来偏移**：全部计算都是对输入字符串做墙上时钟运算，不做时区换算。

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-emergency-plan
```

第 4 项把 `../_shared` 的共享件同步进 `src/shared/`；每次改动共享件后都要重跑。

## License

[Apache License 2.0](LICENSE) © 2026 dsh-emergency-plan contributors.
