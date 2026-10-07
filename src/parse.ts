/**
 * Reader for the canonical emergency-plan material.
 *
 * The material is JSON or YAML. The preferred shape is a `sections` list, because
 * the caller that extracted the plan already knows where each heading sits;
 * a plain text `text` field is also accepted and split on markdown-style headings
 * so a quick paste still works, minus page numbers.
 */

import { YamlSubsetError, parseYaml } from './shared/yaml.ts'
import { toPlanType } from './model.ts'
import type { PlanInput, PlanSection } from './model.ts'

/** Raised when the material cannot be read at all. */
export class MaterialError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'MaterialError'
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function text(value: unknown): string | undefined {
  if (value === undefined || value === null) return undefined
  if (typeof value === 'string') return value.trim() === '' ? undefined : value.trim()
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  return undefined
}

function positiveInt(value: unknown): number | undefined {
  const raw = text(value)
  if (raw === undefined || !/^\d+$/.test(raw)) return undefined
  const parsed = Number.parseInt(raw, 10)
  return parsed > 0 ? parsed : undefined
}

function parseSection(raw: unknown, index: number): PlanSection {
  if (typeof raw === 'string') {
    const title = text(raw)
    if (title === undefined) throw new MaterialError(`sections[${index}] 的标题为空`)
    return { title }
  }
  if (!isRecord(raw)) throw new MaterialError(`sections[${index}] 必须是映射或字符串`)
  const title = text(raw.title ?? raw.heading ?? raw.name)
  if (title === undefined) throw new MaterialError(`sections[${index}] 缺少必填字段 title`)
  const section: PlanSection = { title }
  const level = positiveInt(raw.level)
  if (level !== undefined) section.level = level
  const page = positiveInt(raw.page)
  if (page !== undefined) section.page = page
  const line = positiveInt(raw.line)
  if (line !== undefined) section.line = line
  const body = text(raw.body ?? raw.text)
  if (body !== undefined) section.body = body
  return section
}

/** Split pasted text on markdown headings, or treat each non-empty line as a heading. */
function sectionsFromText(source: string): PlanSection[] {
  const lines = source.split(/\r?\n/)
  const out: PlanSection[] = []
  const headingPattern = /^(#{1,6})\s+(.*)$/
  let sawHeading = false
  for (const line of lines) {
    const match = headingPattern.exec(line)
    if (match !== null) {
      sawHeading = true
      out.push({ title: (match[2] ?? '').trim(), level: (match[1] ?? '#').length })
    }
  }
  if (sawHeading) return out.filter((section) => section.title !== '')
  // No markdown headings: treat short standalone lines as headings, which is what
  // a plain-text outline looks like.
  for (const line of lines) {
    const trimmed = line.trim()
    if (trimmed === '' || trimmed.length > 40) continue
    out.push({ title: trimmed })
  }
  return out
}

/**
 * Parse material into the normalized input contract.
 * @param source - JSON or YAML text.
 * @param target - description of where the material came from.
 * @returns the normalized input.
 */
export function parseMaterial(source: string, target: string): PlanInput {
  const trimmed = source.trim()
  if (trimmed === '') throw new MaterialError('材料为空')
  let document: unknown
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    try {
      document = JSON.parse(trimmed)
    } catch (error) {
      throw new MaterialError(`JSON 无法解析：${error instanceof Error ? error.message : String(error)}`)
    }
  } else {
    try {
      document = parseYaml(trimmed)
    } catch (error) {
      // A plan pasted as plain text is not YAML: markdown headings and prose make
      // the YAML reader throw, and that is not an error the caller should see.
      if (!(error instanceof YamlSubsetError)) throw error
      document = trimmed
    }
  }

  const warnings: string[] = []
  const input: PlanInput = { target, sections: [], warnings }

  if (typeof document === 'string') {
    input.sections = sectionsFromText(document)
  } else if (Array.isArray(document)) {
    input.sections = document.map((entry, index) => parseSection(entry, index))
  } else if (isRecord(document)) {
    const name = text(document.name ?? document.title)
    if (name !== undefined) input.name = name
    const declared = text(document.planType ?? document.type)
    if (declared !== undefined) {
      const resolved = toPlanType(declared)
      if (resolved === undefined) {
        warnings.push(`planType 的值「${declared}」无法识别为综合应急预案 / 专项应急预案 / 现场处置方案，将按综合应急预案的要素清单检查`)
      } else {
        input.planType = resolved
      }
    }
    if (Array.isArray(document.sections)) {
      input.sections = document.sections.map((entry, index) => parseSection(entry, index))
    } else {
      const body = text(document.text ?? document.content)
      if (body !== undefined) input.sections = sectionsFromText(body)
    }
  } else if (document !== null) {
    throw new MaterialError('材料根节点必须是映射、列表或字符串')
  }

  if (input.sections.length === 0) {
    throw new MaterialError('未能从材料中读取到任何章节标题')
  }
  const withPage = input.sections.filter((section) => section.page !== undefined).length
  if (withPage === 0) {
    warnings.push('材料未提供任何章节的页码，报告将按行号定位；如需按页定位请在抽取阶段提供 page 字段')
  }

  return input
}
