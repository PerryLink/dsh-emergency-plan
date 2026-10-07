import { readFile, readdir } from 'node:fs/promises'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { loadRuleset } from '../src/shared/ruleset.ts'
import { parseMaterial } from '../src/parse.ts'
import { runCheck } from '../src/check.ts'
import { buildView } from '../src/view.ts'
import { findForbiddenWording } from '../src/shared/wording.ts'
import { addDays, diffDays, parseWallClock } from '../src/shared/datetime.ts'
import { parseYaml } from '../src/shared/yaml.ts'
import { toPlanType } from '../src/model.ts'
import { Config as ConfigSchema } from '../src/config.ts'
import { inject, name as pluginName, resolvePackageFile, TOOL_NAME } from '../src/index.ts'
import type { Report } from '../src/shared/report.ts'
import type { CheckOptions } from '../src/check.ts'

const here = dirname(fileURLToPath(import.meta.url))
const packageRoot = resolve(here, '..')
const rulesPath = join(packageRoot, 'rules', 'emergency-plan.yaml')
const fixturesRoot = join(here, 'fixtures')
const CHECKED_AT = '2026-10-06T00:00:00.000Z'

interface CaseFile {
  ruleId: string
  configure?: Record<string, Record<string, unknown>>
  pairs: { name: string; material: string; expect: { ruleId: string; count: number } }[]
}

async function loadPack() {
  return loadRuleset(await readFile(rulesPath, 'utf8'))
}

function runOptions(overrides: Partial<CheckOptions> = {}): CheckOptions {
  return { plugin: pluginName, checkedAt: CHECKED_AT, disabledRules: [], onlyRules: [], ...overrides }
}

function withConfiguration(ruleset: Awaited<ReturnType<typeof loadPack>>, configure: CaseFile['configure']) {
  if (configure === undefined) return ruleset
  return {
    ...ruleset,
    rules: ruleset.rules.map((rule) =>
      configure[rule.id] === undefined ? rule : { ...rule, params: { ...rule.params, ...configure[rule.id] } },
    ),
  }
}

async function runFixture(materialText: string, target: string, configure?: CaseFile['configure']): Promise<Report> {
  const ruleset = withConfiguration(await loadPack(), configure)
  return runCheck(parseMaterial(materialText, target), ruleset, runOptions())
}

function issuesOf(report: Report, ruleId: string) {
  return report.issues.filter((issue) => issue.ruleId === ruleId)
}

async function ruleDirectories(): Promise<string[]> {
  const entries = await readdir(fixturesRoot, { withFileTypes: true })
  return entries.filter((entry) => entry.isDirectory()).map((entry) => entry.name).sort()
}

async function readCases(directory: string): Promise<CaseFile> {
  return JSON.parse(await readFile(join(fixturesRoot, directory, 'cases.json'), 'utf8')) as CaseFile
}

const COMPREHENSIVE = {
  name: '某公司综合应急预案',
  planType: 'comprehensive',
  sections: [
    { title: '总则', page: 1, body: '本预案适用于本公司生产安全事故。' },
    { title: '应急组织机构及职责', page: 2, body: '明确应急组织形式及职责。' },
    { title: '应急响应', page: 3, body: '规定信息报告、预警与响应程序。' },
    { title: '后期处置', page: 4, body: '明确污染物处理与生产秩序恢复。' },
    { title: '应急保障', page: 5, body: '明确通信、队伍与物资装备保障。' },
  ],
}

describe('rule pack', () => {
  it('declares a citable basis for every rule', async () => {
    const ruleset = await loadPack()
    expect(ruleset.plugin).toBe(pluginName)
    expect(ruleset.rules.length).toBeGreaterThanOrEqual(9)
    for (const rule of ruleset.rules) {
      expect(rule.basis.document, `${rule.id} document`).not.toBe('')
      expect(rule.basis.clause, `${rule.id} clause`).not.toBe('')
      expect(rule.basis.excerpt.length, `${rule.id} excerpt`).toBeGreaterThanOrEqual(8)
      expect(rule.basis.source, `${rule.id} source`).toMatch(/^https?:\/\//)
      expect(['direct', 'derived-from-principle', 'institutional-configuration']).toContain(rule.basis.kind)
    }
  })

  it('never lets a principle-derived or locally configured check be an error', async () => {
    const ruleset = await loadPack()
    for (const rule of ruleset.rules) {
      if (rule.basis.kind === 'derived-from-principle') expect(rule.severity, rule.id).not.toBe('error')
      if (rule.basis.kind === 'institutional-configuration') expect(rule.severity, rule.id).toBe('info')
    }
  })

  it('never states the colloquial "eight elements" name as a requirement and never cites the superseded 2013 standard', async () => {
    const ruleset = await loadPack()
    for (const rule of ruleset.rules) {
      expect(rule.title, rule.id).not.toContain('八要素')
      expect(rule.basis.clause, rule.id).not.toContain('八要素')
      expect(rule.basis.excerpt, rule.id).not.toContain('八要素')
      expect(rule.basis.number, rule.id).not.toContain('29639-2013')
      for (const extra of rule.alsoBasis ?? []) expect(extra.number, rule.id).not.toContain('2013')
    }
    // The header is allowed to name it in order to debunk it, but must say so.
    const source = await readFile(rulesPath, 'utf8')
    expect(source).toContain('「八要素」不是现行国家文件的表述')
    expect(source).toContain('已被全部代替的 GB/T 29639—2013')
  })

  it('uses the current five first-level elements for the comprehensive plan', async () => {
    const ruleset = await loadPack()
    const comprehensive = ruleset.rules.find((rule) => rule.id === 'EP-002')
    const elements = comprehensive?.params.elements as { name: string; aliases: string[] }[]
    expect(elements.map((element) => element.name)).toEqual([
      '总则',
      '应急组织机构及职责',
      '应急响应',
      '后期处置',
      '应急保障',
    ])
    // The retired 2013 elements must not be first-class requirements.
    for (const retired of ['信息公开', '信息发布', '应急预案管理']) {
      expect(elements.map((element) => element.name)).not.toContain(retired)
    }
  })

  it('cites the management measure by its full version lineage, not as a bare ministerial order', async () => {
    const ruleset = await loadPack()
    const rule = ruleset.rules.find((entry) => entry.id === 'EP-001')
    const extra = rule?.alsoBasis?.[0]
    expect(extra?.number).toContain('国家安全生产监督管理总局令第88号')
    expect(extra?.number).toContain('应急管理部令第2号修正')
  })

  it('treats the attachment list as a body clause rather than a normative appendix', async () => {
    const ruleset = await loadPack()
    const attachments = ruleset.rules.find((rule) => rule.id === 'EP-009')
    expect(attachments?.params.requireAttachments).toBe(false)
    expect(attachments?.basis.number).toContain('第88号')
    expect(attachments?.note).toContain('正文条款，非资料性附录')
  })

  it('states that page numbering has no national mandatory basis', async () => {
    const ruleset = await loadPack()
    const locatable = ruleset.rules.find((rule) => rule.id === 'EP-006')
    expect(locatable?.severity).toBe('info')
    expect(locatable?.note).toContain('未核实到任何国家层面文件要求应急预案标注页码')
    expect(locatable?.note).toContain('不得表述为')
  })

  it('records the AQ to YJ standard-code change in the rule pack header', async () => {
    const source = await readFile(rulesPath, 'utf8')
    expect(source).toContain('YJ/T 9011-2019（原 AQ/T 9011-2019）')
    expect(source).toContain('2025 年第 1 号')
  })

  it('refuses a rule pack that overstates a principle-derived check', () => {
    const overstated = [
      'plugin: probe',
      'version: "0"',
      'rules:',
      '  - id: X-001',
      '    title: probe',
      '    severity: error',
      '    basis:',
      '      document: 《X》',
      '      number: X〔2020〕1号',
      '      clause: 第一条',
      '      excerpt: 这是一个足够长的逐字摘录示例。',
      '      kind: derived-from-principle',
      '      source: https://example.invalid/x',
    ].join('\n')
    expect(() => loadRuleset(overstated)).toThrow(/strongest permitted severity/)
  })
})

describe('paired fixtures', () => {
  it('has both a compliant and a violating sample for every rule', async () => {
    const ruleset = await loadPack()
    const covered = new Set<string>()
    for (const directory of await ruleDirectories()) {
      const cases = await readCases(directory)
      expect(cases.pairs.filter((pair) => pair.expect.count === 0).length, `${directory} compliant sample`).toBeGreaterThanOrEqual(1)
      expect(cases.pairs.filter((pair) => pair.expect.count > 0).length, `${directory} violating sample`).toBeGreaterThanOrEqual(1)
      for (const pair of cases.pairs) {
        const material = await readFile(join(fixturesRoot, directory, pair.material), 'utf8')
        const report = await runFixture(material, pair.material, cases.configure)
        const matched = issuesOf(report, cases.ruleId)
        expect(
          matched.length,
          `${directory}/${pair.name} expected ${pair.expect.count} × ${cases.ruleId}, got ${matched.map((issue) => issue.found).join(' | ')}`,
        ).toBe(pair.expect.count)
        covered.add(cases.ruleId)
      }
    }
    for (const rule of ruleset.rules) expect(covered.has(rule.id), `covered ${rule.id}`).toBe(true)
  })

  it('gives every issue a citable basis and a stable id', async () => {
    for (const directory of await ruleDirectories()) {
      const cases = await readCases(directory)
      for (const pair of cases.pairs) {
        const material = await readFile(join(fixturesRoot, directory, pair.material), 'utf8')
        const report = await runFixture(material, pair.material, cases.configure)
        for (const issue of report.issues) {
          expect(issue.basis).toContain('「')
          expect(issue.id).toMatch(/^dsh-emergency-plan\.EP-\d{3}\.[0-9a-f]{8}$/)
          expect(issue.found).not.toBe('')
          expect(issue.expected).not.toBe('')
        }
      }
    }
  })
})

describe('element matching', () => {
  it('locates a section by page number so the finding can be jumped to', async () => {
    const ruleset = await loadPack()
    const material = JSON.stringify({
      planType: 'comprehensive',
      sections: [
        { title: '总则', page: 1, body: 'x' },
        { title: '应急组织机构及职责', page: 2, body: 'x' },
        { title: '应急响应', page: 3, body: '' },
        { title: '后期处置', page: 4, body: 'x' },
        { title: '应急保障', page: 5, body: 'x' },
      ],
    })
    const report = runCheck(parseMaterial(material, 'inline'), ruleset, runOptions())
    const empty = issuesOf(report, 'EP-002')
    expect(empty).toHaveLength(1)
    expect(empty[0]?.locator.page).toBe(3)
    expect(empty[0]?.found).toContain('没有正文内容')
  })

  it('accepts a synonym heading for the same element', async () => {
    const ruleset = await loadPack()
    const material = JSON.stringify({
      planType: 'comprehensive',
      sections: [
        { title: '一、总则', page: 1, body: 'x' },
        { title: '二、组织机构与职责', page: 2, body: 'x' },
        { title: '三、应急响应', page: 3, body: 'x' },
        { title: '四、后期处置', page: 4, body: 'x' },
        { title: '五、保障措施', page: 5, body: 'x' },
      ],
    })
    const report = runCheck(parseMaterial(material, 'inline'), ruleset, runOptions())
    expect(issuesOf(report, 'EP-002')).toHaveLength(0)
  })

  it('splits pasted markdown headings into a section tree', () => {
    const input = parseMaterial('# 总则\n正文\n# 应急响应\n正文', 'inline')
    expect(input.sections.map((section) => section.title)).toEqual(['总则', '应急响应'])
    expect(input.warnings.join(' ')).toContain('未提供任何章节的页码')
  })

  it('recognises the three plan types by their common spellings', () => {
    expect(toPlanType('综合应急预案')).toBe('comprehensive')
    expect(toPlanType('现场处置方案')).toBe('on-site')
    expect(toPlanType('专项')).toBe('special')
    expect(toPlanType('不认识的类型')).toBeUndefined()
  })
})

describe('skipped reporting', () => {
  it('admits that the order check needs positions', async () => {
    const ruleset = await loadPack()
    const material = JSON.stringify({
      planType: 'comprehensive',
      sections: ['总则', '应急组织机构及职责', '应急响应', '后期处置', '应急保障'].map((title) => ({ title, body: 'x' })),
    })
    const report = runCheck(parseMaterial(material, 'inline'), ruleset, runOptions())
    expect(report.skipped.find((entry) => entry.rule === 'EP-005')?.reason).toContain('无法核对顺序')
  })

  it('admits that the attachment check is off by default', async () => {
    const report = await runFixture(JSON.stringify(COMPREHENSIVE), 'inline')
    expect(report.skipped.find((entry) => entry.rule === 'EP-009')?.reason).toContain('requireAttachments')
  })

  it('says when an element list is not configured', async () => {
    const ruleset = await loadPack()
    const stripped = {
      ...ruleset,
      rules: ruleset.rules.map((rule) => (rule.id === 'EP-002' ? { ...rule, params: {} } : rule)),
    }
    const input = parseMaterial(JSON.stringify(COMPREHENSIVE), 'inline')
    const report = runCheck(input, stripped, runOptions())
    expect(report.skipped.find((entry) => entry.rule === 'EP-002')?.reason).toContain('未配置 elements')
  })

  it('names disabled rules exactly once and appends the configured note', async () => {
    const ruleset = await loadPack()
    const input = parseMaterial(JSON.stringify(COMPREHENSIVE), 'inline')
    const report = runCheck(input, ruleset, runOptions({ disabledRules: ['EP-007'], skipNotes: '本机构预案模板' }))
    const entries = report.skipped.filter((item) => item.rule === 'EP-007')
    expect(entries).toHaveLength(1)
    expect(entries[0]?.reason).toContain('禁用')
    expect(entries[0]?.reason).toContain('本机构预案模板')
  })
})

describe('report rendering', () => {
  it('never uses adjudicating wording and always carries the disclaimer', async () => {
    const material = await readFile(join(fixturesRoot, 'EP-002', 'EP-002-unsafe.json'), 'utf8')
    const report = await runFixture(material, 'EP-002-unsafe.json')
    const view = buildView(report)
    expect(findForbiddenWording(view.markdown)).toEqual([])
    expect(view.markdown).toContain('免责声明')
    expect(view.markdown).toContain('未执行的检查')
    expect(JSON.parse(view.reportJson)).toMatchObject({ plugin: pluginName, summary: report.summary })
  })
})

describe('plugin contract', () => {
  it('declares a static inject array covering every service apply touches', () => {
    expect(Array.isArray(inject)).toBe(true)
    expect(inject).toContain('tools')
  })

  it('exposes a Schemastery Config with serializable defaults', () => {
    const resolved = ConfigSchema(null)
    expect(resolved.rulesFile).toBe('rules/emergency-plan.yaml')
    expect(resolved.disabledRules).toEqual([])
    expect(resolved.timeoutMs).toBeGreaterThan(0)
  })

  it('resolves the packaged rule pack and rejects a missing one', () => {
    expect(resolvePackageFile('rules/emergency-plan.yaml')).toBe(rulesPath)
    expect(() => resolvePackageFile('rules/does-not-exist.yaml')).toThrow(/未找到/)
  })

  it('names the tool after the package family convention', () => {
    expect(TOOL_NAME).toBe('emergency_plan')
  })
})

describe('material reader', () => {
  it('rejects empty material instead of reporting an empty result', () => {
    expect(() => parseMaterial('   ', 'inline')).toThrow(/材料为空/)
  })

  it('rejects material with no section headings', () => {
    expect(() => parseMaterial('{}', 'inline')).toThrow(/章节标题/)
  })
})

describe('shared kit', () => {
  it('parses wall-clock timestamps and rejects impossible dates', () => {
    expect(parseWallClock('2026-03-15')).toEqual({ date: '2026-03-15', time: '00:00', hasTime: false, minutes: 0 })
    expect(parseWallClock('2026-02-30')).toBeUndefined()
  })

  it('does calendar arithmetic', () => {
    expect(addDays('2026-03-31', 1)).toBe('2026-04-01')
    expect(diffDays('2026-03-01', '2026-03-06')).toBe(5)
  })

  it('reads the supported YAML subset including block scalars with quotes', () => {
    expect(parseYaml('a: 1\nb:\n  - x\n')).toEqual({ a: 1, b: ['x'] })
    expect(parseYaml('note: >-\n  本条只核对"是否填写"，不判断选择。\n')).toEqual({
      note: '本条只核对"是否填写"，不判断选择。',
    })
    expect(() => parseYaml('a: 1\na: 2\n')).toThrow(/duplicate/)
  })
})
