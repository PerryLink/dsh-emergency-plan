/**
 * Pure check core: `(input, ruleset, options) => Report`.
 *
 * No plugin context, no I/O, no clock and no model access, so the whole rule set
 * is unit-testable without credentials. Every finding carries the verbatim
 * clause that produced it, and every check that could not run is reported in
 * `skipped` so an empty issue list can never be read as "nothing is wrong".
 *
 * The element lists live in the rule pack, not here, because which elements a
 * plan must contain depends on the plan type and on the version of the drafting
 * guideline in force. The checker's job is to find each element in the document's
 * own section tree and say where it is; whether the element's *content* is any
 * good stays with the review panel.
 */

import { disabledAsSkipped, formatBasis } from './shared/rules.ts'
import { paramStrings, ruleById } from './shared/ruleset.ts'
import { issueId, makeReport } from './shared/report.ts'
import { normalizeHeading } from './shared/tree.ts'
import { editDistance } from './shared/dictionary.ts'
import type { Issue, Locator, Report, Skipped } from './shared/report.ts'
import type { Ruleset } from './shared/rules.ts'
import type { PlanInput, PlanSection } from './model.ts'

/** Options that come from the plugin configuration rather than the rule pack. */
export interface CheckOptions {
  plugin: string
  checkedAt: string
  disabledRules: readonly string[]
  onlyRules: readonly string[]
  skipNotes?: string
}

interface RuleContext {
  input: PlanInput
  ruleset: Ruleset
  issues: Issue[]
  skipped: Skipped[]
  fired: Set<string>
  skipReasons: Map<string, string>
  add(ruleId: string, locator: Locator, found: string, expected: string, fix?: string): void
  skip(ruleId: string, reason: string): void
}

/** A required element as declared in the rule pack. */
interface ElementSpec {
  /** Canonical name, used in the report. */
  name: string
  /** Accepted heading spellings; matching is by normalized containment. */
  aliases: string[]
}

function locatorOf(section: PlanSection): Locator {
  const locator: Locator = {}
  if (section.page !== undefined) locator.page = section.page
  if (section.line !== undefined) locator.line = section.line
  if (locator.page === undefined && locator.line === undefined) locator.cell = section.title
  return locator
}

function basisOf(ruleset: Ruleset, ruleId: string): string {
  const rule = ruleById(ruleset, ruleId)
  return formatBasis(rule.basis, rule.alsoBasis ?? [])
}

function makeAdd(context: Omit<RuleContext, 'add' | 'skip'>): RuleContext['add'] {
  return (ruleId, locator, found, expected, fix) => {
    const rule = ruleById(context.ruleset, ruleId)
    const issue: Issue = {
      id: issueId(context.ruleset.plugin, ruleId, locator),
      ruleId,
      severity: rule.severity,
      locator,
      found,
      expected,
      basis: formatBasis(rule.basis, rule.alsoBasis ?? []),
    }
    if (fix !== undefined) issue.fix = fix
    context.issues.push(issue)
    context.fired.add(ruleId)
  }
}

/**
 * Read the element list for one plan type out of the rule pack.
 * @param ruleId - the rule that carries the list.
 * @param ruleset - the rule pack.
 * @returns the declared elements, or an empty list when the list is not configured.
 */
function elementSpecs(ruleset: Ruleset, ruleId: string): ElementSpec[] {
  const rule = ruleById(ruleset, ruleId)
  const raw = rule.params.elements
  if (!Array.isArray(raw)) return []
  const out: ElementSpec[] = []
  for (const entry of raw) {
    if (typeof entry !== 'object' || entry === null) continue
    const record = entry as Record<string, unknown>
    if (typeof record.name !== 'string' || record.name.trim() === '') continue
    const aliases = Array.isArray(record.aliases)
      ? record.aliases.filter((value): value is string => typeof value === 'string' && value.trim() !== '')
      : []
    out.push({ name: record.name.trim(), aliases: aliases.length > 0 ? aliases : [record.name.trim()] })
  }
  return out
}

/**
 * Find the section that satisfies one element, or undefined.
 *
 * Headings are matched in three widening steps — exact normalized equality, then
 * containment, then a small edit distance — because real plans write the same
 * element several ways ("组织机构与职责" against the guideline's "组织机构及职责").
 * The edit-distance step only applies to names long enough that a one-character
 * difference is a wording variant rather than a different element.
 */
function findElement(sections: readonly PlanSection[], spec: ElementSpec): PlanSection | undefined {
  // `一、总则` and `总则` are the same heading; strip numbering before comparing.
  const titleOf = (section: PlanSection): string => normalizeHeading(section.title).title
  const wanted = spec.aliases.map((alias) => normalizeHeading(alias).title)
  for (const alias of wanted) {
    const exact = sections.find((section) => titleOf(section) === alias)
    if (exact !== undefined) return exact
  }
  for (const alias of wanted) {
    const contained = sections.find((section) => {
      const title = titleOf(section)
      return title.includes(alias) || alias.includes(title)
    })
    if (contained !== undefined) return contained
  }
  let best: { section: PlanSection; distance: number } | undefined
  for (const alias of wanted) {
    // A heading variant may drop a qualifier ("应急组织机构及职责" against
    // "组织机构与职责"), so allow a marginal edit distance that scales with the
    // name's length — never more than two characters, and none for short names.
    const allowance = alias.length >= 8 ? 2 : alias.length >= 5 ? 1 : 0
    if (allowance === 0) continue
    for (const section of sections) {
      const title = titleOf(section)
      if (title.length < 5) continue
      if (Math.abs(title.length - alias.length) > allowance) continue
      const distance = editDistance(title, alias)
      if (distance > allowance) continue
      if (best === undefined || distance < best.distance) best = { section, distance }
    }
  }
  return best?.section
}

/**
 * EP-001 / EP-002 / EP-003 — the element list for the declared plan type.
 * @param context - check context.
 * @param ruleId - which plan type's list to apply.
 * @param label - the plan type as it should read in the report.
 */
function checkElements(context: RuleContext, ruleId: string, label: string): void {
  const declared = context.input.planType
  const expected = ruleId === 'EP-001' ? undefined : ruleId === 'EP-002' ? 'comprehensive' : ruleId === 'EP-003' ? 'on-site' : 'special'
  if (expected !== undefined && declared !== undefined && declared !== expected) {
    context.skip(ruleId, `材料声明的预案类型为「${declared}」，不是${label}，本条不适用`)
    return
  }
  if (expected !== undefined && declared === undefined) {
    context.skip(ruleId, `材料未声明 planType；本条按${label}的要素清单检查，请确认该假设成立`)
  }
  const specs = elementSpecs(context.ruleset, ruleId)
  if (specs.length === 0) {
    context.skip(ruleId, '规则库未配置 elements：要素清单随导则版本变化，本条不执行；请在本机构规则库中填写')
    return
  }
  for (const spec of specs) {
    const section = findElement(context.input.sections, spec)
    if (section === undefined) {
      context.add(
        ruleId,
        {},
        `材料中未找到要素「${spec.name}」`,
        `${label}应当包含要素「${spec.name}」`,
        `检查的别名：${spec.aliases.join(' / ')}；如本机构使用其他表述，请在该要素的 aliases 中补充`,
      )
      continue
    }
    if ((section.body ?? '').trim() !== '') continue
    context.add(
      ruleId,
      locatorOf(section),
      `要素「${spec.name}」已出现（标题「${section.title}」），但其后没有正文内容`,
      `${label}的该要素应当有对应内容`,
      '材料只提供了标题时无法判断内容是否齐备，请提供章节正文后重新检查',
    )
  }
}

/** EP-004 — the plan states which type it is. */
function checkPlanTypeDeclared(context: RuleContext): void {
  const ruleId = 'EP-004'
  const rule = ruleById(context.ruleset, ruleId)
  if (rule.params.requirePlanType === false) {
    context.skip(ruleId, '规则库配置为不要求声明预案类型，本条不执行')
    return
  }
  if (context.input.planType !== undefined) return
  context.add(
    ruleId,
    {},
    '材料未声明 planType',
    '不同预案类型的要素清单不同，应先声明预案类型',
    '在材料中加入 planType: comprehensive / special / on-site 之一',
  )
}

/** EP-005 — the elements appear in the guideline's order. */
function checkElementOrder(context: RuleContext): void {
  const ruleId = 'EP-005'
  const rule = ruleById(context.ruleset, ruleId)
  if (rule.params.checkOrder === false) {
    context.skip(ruleId, '规则库配置为不检查要素顺序，本条不执行')
    return
  }
  const listRuleId = context.input.planType === 'on-site' ? 'EP-003' : 'EP-002'
  const specs = elementSpecs(context.ruleset, listRuleId)
  if (specs.length === 0) {
    context.skip(ruleId, '规则库未配置要素清单，无法核对顺序')
    return
  }
  const located = specs
    .map((spec, index) => ({ spec, index, section: findElement(context.input.sections, spec) }))
    .filter((entry): entry is { spec: ElementSpec; index: number; section: PlanSection } => entry.section !== undefined)
  const positioned = located.filter((entry) => entry.section.page !== undefined || entry.section.line !== undefined)
  if (positioned.length < 2) {
    context.skip(ruleId, '可定位的要素少于 2 个，无法核对顺序；请为章节提供 page 或 line')
    return
  }
  const reverse = positioned.map((entry) => ({
    ...entry,
    at: entry.section.page ?? entry.section.line ?? 0,
  }))
  for (let index = 1; index < reverse.length; index++) {
    const previous = reverse[index - 1] as (typeof reverse)[number]
    const current = reverse[index] as (typeof reverse)[number]
    if (current.index > previous.index && current.at < previous.at) {
      context.add(
        ruleId,
        locatorOf(current.section),
        `要素「${current.spec.name}」位于第 ${current.at} 位，排在其前面的「${previous.spec.name}」（第 ${previous.at} 位）之后但在要素清单中更靠后`,
        '要素顺序应与导则的要素清单一致',
        '核对章节顺序；材料未提供页码时按行号核对',
      )
    }
  }
}

/** EP-006 — every section carries a locatable position. */
function checkSectionLocatable(context: RuleContext): void {
  const ruleId = 'EP-006'
  const rule = ruleById(context.ruleset, ruleId)
  const ratio = typeof rule.params.minPageRatio === 'number' ? rule.params.minPageRatio : 0.5
  const total = context.input.sections.length
  const withPage = context.input.sections.filter((section) => section.page !== undefined).length
  if (total === 0) {
    context.skip(ruleId, '材料中没有章节')
    return
  }
  if (withPage / total >= ratio) {
    context.skip(ruleId, `已有 ${withPage}/${total} 个章节带页码，达到配置的比例 ${ratio}，本条不报差异`)
    return
  }
  context.add(
    ruleId,
    {},
    `材料中只有 ${withPage}/${total} 个章节带页码，低于配置比例 ${ratio}`,
    '按本机构配置，报告应能按页定位要素',
    '在抽取阶段提供每个章节的起始页码；未提供页码时报告只能按行号定位',
  )
}

/** EP-007 — a duplicate element heading usually means the plan was merged badly. */
function checkDuplicateElements(context: RuleContext): void {
  const ruleId = 'EP-007'
  const listRuleId = context.input.planType === 'on-site' ? 'EP-003' : 'EP-002'
  const specs = elementSpecs(context.ruleset, listRuleId)
  if (specs.length === 0) {
    context.skip(ruleId, '规则库未配置要素清单，无法核对重复')
    return
  }
  for (const spec of specs) {
    const matches = context.input.sections.filter((section) => findElement([section], spec) !== undefined)
    if (matches.length <= 1) continue
    const first = matches[0] as PlanSection
    context.add(
      ruleId,
      locatorOf(first),
      `要素「${spec.name}」在材料中出现 ${matches.length} 次（标题：${matches.map((section) => section.title).join(' / ')}）`,
      '同一要素在预案中应只出现一次',
      '核对是否为合并多份预案时产生的重复章节',
    )
  }
}

/** EP-008 — the plan records its own version and revision. */
function checkVersionRecord(context: RuleContext): void {
  const ruleId = 'EP-008'
  const rule = ruleById(context.ruleset, ruleId)
  const patterns = paramStrings(rule, 'versionPatterns', [])
  if (patterns.length === 0) {
    context.skip(ruleId, '规则库未配置 versionPatterns：未找到国家层面对版本号与修订记录格式的明文，本条不执行')
    return
  }
  const titles = context.input.sections.map((section) => section.title).join(' ')
  const hit = patterns.some((pattern) => titles.includes(pattern))
  if (hit) return
  context.add(
    ruleId,
    {},
    `材料章节标题中未出现配置的版本或修订标识（${patterns.join(' / ')}）`,
    '按本机构配置，预案应标明版本或修订信息',
    '核对是否缺少版本或修订记录章节；本条为提示级，无国家明文格式要求',
  )
}

/**
 * EP-009 — the attachment information the management measure requires.
 *
 * Off by default: a caller usually supplies the plan body without its
 * attachments, and reporting "no attachments were given" as a gap would be
 * misleading. When the deployment enables it, the attachment items are matched
 * the same way as the body elements.
 */
function checkAttachments(context: RuleContext): void {
  const ruleId = 'EP-009'
  const rule = ruleById(context.ruleset, ruleId)
  if (rule.params.requireAttachments !== true) {
    context.skip(
      ruleId,
      '规则库未启用 requireAttachments：材料往往只提供正文、不含附件，未启用时本条不执行；需要核对请配置为 true 并一并提供附件章节',
    )
    return
  }
  const specs = elementSpecs(context.ruleset, ruleId)
  if (specs.length === 0) {
    context.skip(ruleId, '规则库未配置 elements：附件项清单随导则版本变化，本条不执行')
    return
  }
  for (const spec of specs) {
    const section = findElement(context.input.sections, spec)
    if (section !== undefined) continue
    context.add(
      ruleId,
      {},
      `材料中未找到附件项「${spec.name}」`,
      `预案应包含附件信息，包括${spec.name}`,
      `检查的别名：${spec.aliases.join(' / ')}；材料只提供正文时，附件缺项可能只是未被提供`,
    )
  }
}

const CHECKERS: readonly ((context: RuleContext) => void)[] = [
  (context) => checkElements(context, 'EP-001', '专项应急预案'),
  (context) => checkElements(context, 'EP-002', '综合应急预案'),
  (context) => checkElements(context, 'EP-003', '现场处置方案'),
  checkPlanTypeDeclared,
  checkElementOrder,
  checkSectionLocatable,
  checkDuplicateElements,
  checkVersionRecord,
  checkAttachments,
]

/**
 * Run the whole rule pack against one plan.
 * @param input - normalized material.
 * @param ruleset - validated rule pack.
 * @param options - plugin identity, clock value and rule selection.
 * @returns the report, with `skipped` listing every check that did not run.
 */
export function runCheck(input: PlanInput, ruleset: Ruleset, options: CheckOptions): Report {
  const disabled = new Set([...ruleset.disabled, ...options.disabledRules])
  const only = new Set(options.onlyRules)
  const base = {
    input,
    ruleset,
    issues: [] as Issue[],
    skipped: [] as Skipped[],
    fired: new Set<string>(),
    skipReasons: new Map<string, string>(),
  }
  const context: RuleContext = {
    ...base,
    add: makeAdd(base),
    skip: (ruleId, reason) => {
      base.skipReasons.set(ruleId, reason)
    },
  }

  for (const checker of CHECKERS) checker(context)

  const withNote = (reason: string): string => (options.skipNotes === undefined ? reason : `${reason}；${options.skipNotes}`)
  const skipped: Skipped[] = disabledAsSkipped(ruleset, [...disabled], withNote('该规则在当前配置中被禁用'))
  const already = new Set(skipped.map((entry) => entry.rule))
  for (const [ruleId, reason] of base.skipReasons) {
    if (already.has(ruleId)) continue
    if (disabled.has(ruleId) || (options.onlyRules.length > 0 && !only.has(ruleId))) continue
    skipped.push({ rule: ruleId, reason: withNote(reason) })
    already.add(ruleId)
  }
  for (const rule of ruleset.rules) {
    if (disabled.has(rule.id) || base.fired.has(rule.id) || already.has(rule.id)) continue
    if (options.onlyRules.length > 0 && !only.has(rule.id)) continue
    skipped.push({ rule: rule.id, reason: withNote('材料满足该检查的前置条件且未发现差异条目') })
  }
  if (options.onlyRules.length > 0) {
    const notSelected = ruleset.rules.filter((rule) => !only.has(rule.id) && !disabled.has(rule.id))
    if (notSelected.length > 0) {
      skipped.push({
        rule: notSelected.map((rule) => rule.id).join(','),
        reason: withNote(`本次调用通过 only 参数把执行范围限制为 ${[...only].join(', ')}，上列规则未执行`),
      })
    }
  }

  return makeReport({
    plugin: options.plugin,
    target: input.target,
    rulesetVersion: ruleset.version,
    checkedAt: options.checkedAt,
    issues: context.issues,
    skipped,
  })
}
