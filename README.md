# dsh-emergency-plan — Emergency plan element completeness and clause-level page locating

[![DSH Market](https://raw.githubusercontent.com/2BingLing/dsh-market/master/assets/readme/badge-listed-en.svg)](https://dsh.market/)

`dsh-emergency-plan` reads one emergency plan — its section tree, headings, page numbers and body text — and checks that plan's element completeness against the drafting guideline: which elements are present, which are absent, which appear only as a heading with no text under them, and where each one sits, by page where the material carries page numbers and by line otherwise. It applies a versioned rule pack to the plan type the material declares, and every finding names the clause it came from and states whether that clause is a direct requirement, a principle or a local configuration; a check that could not run says so in `skipped` instead of passing silently.

## What it looks like

![Terminal demo of dsh-emergency-plan: real output over its EP-004 fixture](https://raw.githubusercontent.com/PerryLink/dsh-emergency-plan/main/docs/assets/dsh-emergency-plan-demo.png)

Real output from this plugin over its own `EP-004` test fixture — not a mock-up. The rule pack ships no invented quotations, so a finding names both the clause it applied and the fact that the clause text was not obtained.

## What it answers

| You ask | What it answers |
|---|---|
| Our material never says which of the three plan types it is. What happens? | `EP-004` reports the material for not declaring `planType`, because each of the three types carries a different element list. It checks only that the declaration is there, not that it is the right one; while it is missing, `EP-002` and `EP-003` state in `skipped` which element list they assumed. |
| A 综合应急预案 has no 后期处置 chapter. Is that reported — and does it also need a 编制目的 section? | `EP-002` looks for the five first-level elements of the current guideline's chapter 6 (6.1~6.5) one by one and reports each one it cannot find, so a missing 后期处置 is reported. 编制目的 is not one of the five: the current edition removed it, and the pack accepts it only as an alias of 总则. The finding is `warn`, because the drafting guideline is a recommended national standard, not a mandatory one. |
| Which elements are mandatory in a 专项应急预案 and in a 现场处置方案? | `EP-001` requires the 专项应急预案's 7.1~7.4 elements and `EP-003` the 现场处置方案's 8.1~8.4, each reporting the elements it cannot find in the section tree; a heading that exists with no text under it is reported as empty. Both lists are floors, not closed lists — the 现场处置 clause reads 包括但不限于 — so an extra element is not a finding. In `EP-001` the 7.5 应急保障 element stays recommended; in `EP-003` the shorter list in the 《生产安全事故应急预案管理办法》 is kept as a separate basis and never merged with the guideline's. |
| We merged two plans and now the same element heading appears twice. Is that caught? | `EP-007` reports a required element that appears more than once and lists every heading that matched it. No clause states this outright — the pack derives it from the uniqueness of the 目次 order — so it is capped at `warn`, and the pack asks for human confirmation, because a duplicate usually comes from merging several plans. It compares the element list it applies, not every repeated heading in the material. |
| The report shows `EP-005` as `skipped`. Why — and must a plan carry page numbers? | `EP-005` can compare element order only when at least two elements carry a `page` or a `line`; without them it says so in `skipped` rather than assuming an order. `EP-006` treats page numbers as locating information: it stays quiet once the share of sections carrying a page reaches `minPageRatio` (0.5 by default) and, below that share, only raises an `info` finding. Both are capped at `info` — the order expectation is drawn from an informative appendix, not the standard's body — and a plan without page numbers is never reported as a breach of a clause: the report locates by line number instead. |
| Why do `EP-008` and `EP-009` appear under `skipped` instead of passing? | Both wait for configuration. `EP-009` runs only when `requireAttachments` is set to `true`, because a caller usually supplies the plan body without its attachments and reporting those as missing would be misleading; enabled, it looks for the eight attachment items and reports the ones it cannot find. `EP-008` runs only when `versionPatterns` are configured: with the list empty it does not dictate what a version marker should look like, and once configured it checks only whether the configured marker appears in a section heading — never whether the revision content is correct. |

## Standards it follows

| Document | Number | Cited by rules |
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

| Surface | Status |
|---|---|
| Harness | Peer range `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verified to accept both `0.2.0-rc.2` and `0.2.1-alpha.1`. `engines.dsh` is deliberately not declared: it has no reader and cannot reject a host |
| Node | `^22.19.0 || >=24.0.0` |
| Platforms | All (plain ESM; no native code, no network, no model call) |
| Tool mode | Works in `native`, `ptc` and `both`; for a batch of plans use `ptc` |

## What it does

Registers the `emergency_plan` tool. It reads one plan's section tree — headings, page numbers and body
text — applies a versioned rule pack, and returns a report in which every finding names the clause it
came from and states whether that clause is a direct requirement, a principle, or a local
configuration.

| Rule | Check | Severity | Basis kind |
|---|---|---|---|
| `EP-001` | a 专项应急预案 carries its 7.1–7.4 elements | warn | direct |
| `EP-002` | a 综合应急预案 carries its 6.1–6.5 elements | warn | direct |
| `EP-003` | a 现场处置方案 carries its 8.1–8.4 elements | warn | direct |
| `EP-004` | the material declares which of the three types it is | warn | direct |
| `EP-005` | the elements appear in the guideline's order | info | principle |
| `EP-006` | the sections carry page numbers, so a finding can be located | info | principle |
| `EP-007` | no element heading appears twice | warn | principle |
| `EP-008` | a version or revision marker is present, as configured | info | local |
| `EP-009` | the plan carries the attachment information (off by default) | info | direct |

The element lists live in the rule pack, not in the code, because they change with the guideline's
version. Severities reflect that GB/T 29639 is a **recommended** national standard: an incomplete
element list is a `warn`, not an `error`.

## Install

```sh
dsh plugin --profile <name> add dsh-emergency-plan
dsh --profile <name> --dump-config | grep 'dsh-emergency-plan'
```

## Configuration

| Key | Type | Default | Description |
|---|---|---|---|
| `rulesFile` | string | `rules/emergency-plan.yaml` | Rule-pack path, relative to the package root |
| `disabledRules` | string[] | `[]` | Rule ids to stop running; each appears in `skipped` |
| `onlyRules` | string[] | `[]` | Run only these rule ids; empty runs every rule |
| `skipNotes` | string | `""` | Note appended to every `skipped` reason |
| `timeoutMs` | number | `120000` | Cooperative tool timeout budget |

Rule-level parameters worth knowing:

- `EP-001` / `EP-002` / `EP-003` `elements` — the element list per plan type, as
  `[{ name, aliases }]`. Replace it to check against a different guideline version or against your own
  institution's template. An empty list makes the rule report that it could not run.
- `EP-006` `minPageRatio` — the share of sections that must carry a page number before the rule stays
  quiet.
- `EP-008` `versionPatterns` — the strings that count as a version marker for your templates. Empty
  means the rule does not run.
- `EP-009` `requireAttachments` — off by default, because a caller usually supplies the body without
  attachments; enable it only when the attachments are actually in the material.

## Material format

The tool accepts JSON or YAML, and also a plain-text plan. The section-tree form is preferred, because
the caller that extracted the plan already knows where each heading sits:

```yaml
name: 某公司生产安全事故综合应急预案
planType: comprehensive         # comprehensive | special | on-site
sections:
  - { title: 总则, page: 1, body: 本预案适用于…… }
  - { title: 应急组织机构及职责, page: 2, body: 明确应急组织形式…… }
  - { title: 应急响应, page: 3, body: 规定信息报告、预警与响应程序。 }
```

Headings are matched against each element's aliases in three widening steps: exact normalized
equality, containment, then a small edit distance, so that both `五、保障措施` and
`二、组织机构与职责` find their element. Numbering prefixes (`一、`, `1.1`, `**…**`) are stripped
before comparison. Pasting markdown (`# 总则`) also works and is split on the headings, without page
numbers — the report then says so.

## Rule sources

Rule data lives in `rules/emergency-plan.yaml`. Every rule carries a document, a document number, a
clause in the source's own numbering, a verbatim excerpt and the URL the excerpt was read from. The
loader enforces that an excerpt is a real quotation of at least eight characters, and that a check
resting only on a general principle or a local policy can never be declared `error`.

The clauses quoted come from **GB/T 29639-2020** clauses 5.1, 6, 7, 8, appendix C.1 and C.3, and from
**国家安全生产监督管理总局令第88号（应急管理部令第2号修正）** articles 13, 14, 15 and 16.

Three findings shaped this pack and are recorded in its header:

1. **"八要素" comes from a withdrawn standard.** The current comprehensive-plan list has five
   first-level elements, and 编制目的 was removed.
2. **Page numbers have no mandatory basis**, so they are a locating aid at `info` level, never a
   non-conformity.
3. **The standard code prefix changed.** 应急管理部公告 2025 年第 1 号 moved
   AQ/T 9011-2019 and ten other standards to the **YJ** prefix, keeping number, year and content —
   so the companion evaluation guide is now written **YJ/T 9011-2019（原 AQ/T 9011-2019）**.
   The evaluation guide is separate from the drafting guideline: GB/T 29639 governs **drafting**,
   YJ/T 9011 governs **evaluation**.

## Troubleshooting

- **Every element check reports itself as skipped.** The rule pack's `elements` list is empty for that
  plan type, or the material never declared `planType` and the check declined to assume one.
- **A heading you know exists is reported as missing.** Add it to that element's `aliases`. Matching is
  literal (with the three widening steps above), not semantic, by design.
- **`EP-005` reports nothing about order.** The sections carry neither `page` nor `line`, so there is
  nothing to order by; the rule says so in `skipped`.
- **`EP-006` complains about page numbers on a plan that has none.** That is the point of the rule, and
  it is `info`: it is telling you the report can only cite line numbers. Lower `minPageRatio` or read
  past it.
- **The plugin installs but the tool never appears.** Check that `main` resolves to `lib/index.mjs` and
  that `pnpm run build` produced it; a wrong `main` makes the loader skip the entry silently.
- **`dsh plugin add` refuses the package as incompatible.** The peer range covers `0.1.x` and `0.2.x`;
  if your runtime sits outside it, grant an explicit exemption:
  `dsh plugin --profile <name> allow-version dsh-emergency-plan@0.1.0 --dsh-version <runtime> --accept-risk`
- **`check` reports `manifest-peers` as failed.** The static checker compares against a hard-coded peer
  range that predates the 0.2 line. The runtime enforces peer compatibility at install time, so the
  declared range is the correct one; this is a known upstream issue in `dsh-plugin-dev`.

## Development

```sh
pnpm install
pnpm run typecheck   # tsc --noEmit
pnpm test            # vitest, paired fixtures per rule
pnpm run build       # tsdown -> lib/index.mjs + lib/index.d.mts
node ../scripts/sync-shared.mjs dsh-emergency-plan   # refresh src/shared from ../_shared
```

## License

[Apache License 2.0](LICENSE) © 2026 dsh-emergency-plan contributors.
