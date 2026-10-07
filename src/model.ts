/**
 * Input contract for the emergency-plan element checker.
 *
 * The material is the plan's section structure plus each section's body text and,
 * when the reader knows it, the page the section starts on. Page numbers matter
 * for this plugin: a finding that says "应急响应 is missing" is only actionable
 * if the reviewer can also see where the sections around it are.
 */

/** One heading found in the plan, with its position and body. */
export interface PlanSection {
  /** Heading text exactly as it appears in the plan. */
  title: string
  /** Heading depth, 1 for a top-level heading. */
  level?: number
  /** 1-based page the heading starts on, when the reader knows pagination. */
  page?: number
  /** 1-based line the heading was found on, when the reader is line-oriented. */
  line?: number
  /** Body text between this heading and the next. */
  body?: string
}

/** The whole normalized input. */
export interface PlanInput {
  target: string
  /** Plan name, for the report header. */
  name?: string
  /** Declared plan type; drives which element list applies. */
  planType?: string
  sections: PlanSection[]
  warnings: string[]
}

/** Recognised plan types, keyed by the spellings a plan might declare. */
export const PLAN_TYPES: Record<string, string> = {
  comprehensive: 'comprehensive',
  综合: 'comprehensive',
  综合应急预案: 'comprehensive',
  'on-site': 'on-site',
  现场: 'on-site',
  现场处置方案: 'on-site',
  专项: 'special',
  专项应急预案: 'special',
  special: 'special',
}

/** Narrow an arbitrary string to a known plan type. */
export function toPlanType(raw: string | undefined): string | undefined {
  if (raw === undefined) return undefined
  return PLAN_TYPES[raw.trim().toLowerCase()] ?? PLAN_TYPES[raw.trim()]
}
