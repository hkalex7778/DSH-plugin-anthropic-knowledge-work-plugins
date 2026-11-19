/**
 * dsh-knowledge-work-data — 岗位技能 provider。
 *
 * 只在被 preset 挂载时注册：ctx.skills 是 host + per-scope 分层注册表，
 * 一次 registration 落进「调用它的 context 所在 layer」。因此这些技能只出现在
 * 选了「数据分析师」preset 的会话里，不会污染普通 Standard 会话的斜杠命令菜单。
 *
 * 没有引入 yaml 依赖：asset 的 frontmatter 只允许单行 `key: value`，
 * 由下面严格解析，不合规的条目跳过并告警（不误解析成奇怪内容）。
 *
 * @module @local/dsh-knowledge-work-data
 */

import { readdir, readFile } from 'node:fs/promises'
import { join, sep } from 'node:path'
import { fileURLToPath } from 'node:url'

/**
 * 与 @deepseek-ai/dsh-skill 的 BUNDLED_SKILL_RANK 同值。
 * 内联而非 import，避免本 bundle 依赖 dsh 安装目录的解析路径。
 */
const BUNDLED_SKILL_RANK = 600

/** 本岗位 provider 名；保留名 `runtime` 不可用。 */
const PROVIDER_NAME = 'dsh-knowledge-work-data'

const ASSET_ROOT = fileURLToPath(new URL('./assets/', import.meta.url))

/** Registry this plugin contributes to. */
export const inject = ['skills']

/** Cordis plugin identity. */
export const name = 'knowledge-work-data-skills'

// 不导出 Config：assets 随 bundle 打包，本插件没有可配置项。

const FRONTMATTER = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/u
const KEY_LINE = /^([A-Za-z][A-Za-z0-9-]*):[ \t]*(.*)$/u
/** Keys consumed here; any other key (e.g. upstream `argument-hint`) is ignored. */
const KNOWN_KEYS = new Set(['name', 'description', 'whenToUse', 'user-invocable', 'disable-model-invocation'])

/**
 * Parse a boolean frontmatter flag with the tolerant grammar
 * `dsh-skill-filesystem` accepts for the same keys.
 * @param {string} value - Raw scalar text after the colon.
 * @param {string} key - Key name for error messages.
 * @param {string} path - File path for error messages.
 * @returns {boolean}
 * @throws When the value is not a recognised boolean spelling.
 */
function parseBool(value, key, path) {
  const t = value.trim().toLowerCase()
  if (t === 'true' || t === 'yes' || t === 'on' || t === '1') return true
  if (t === 'false' || t === 'no' || t === 'off' || t === '0') return false
  throw new Error(`${path}: 键 ${key} 需要布尔值（true/false/yes/no/on/off/1/0），实际为 "${value}"`)
}

/**
 * Parse the strict single-line frontmatter subset a bundled skill may use.
 * @param {string} raw - Full SKILL.md text.
 * @param {string} path - Path for error messages.
 * @returns {{ name: string, description: string, whenToUse?: string, invocation: { modelInvocable: boolean, userInvocable: boolean }, content: string }}
 * @throws When frontmatter is missing, malformed, uses a block scalar, or lacks name/description.
 */
function parseSkill(raw, path) {
  const match = FRONTMATTER.exec(raw)
  if (!match?.[1]) throw new Error(`${path}: 缺少 YAML frontmatter`)
  const meta = {}
  for (const line of match[1].split(/\r?\n/u)) {
    if (line.trim() === '' || line.trimStart().startsWith('#')) continue
    if (/^[ \t]/u.test(line)) throw new Error(`${path}: 不支持缩进/多行值（每个键必须单行）：${line}`)
    const kv = KEY_LINE.exec(line)
    if (!kv) throw new Error(`${path}: frontmatter 行无法解析：${line}`)
    const [, key, rest] = kv
    if (!KNOWN_KEYS.has(key)) continue
    const value = rest.trim()
    if (value === '' || /^[|>][+-]?$/u.test(value)) throw new Error(`${path}: 键 ${key} 的值必须是非空单行文本`)
    const quoted = /^(['"])([\s\S]*)\1$/u.exec(value)
    meta[key] = (quoted ? quoted[2] : value).trim()
  }
  if (!meta.name || !meta.description) throw new Error(`${path}: frontmatter 需要 name 和 description`)
  // Omitted flags permit their surface, matching the filesystem provider default.
  const invocation = {
    modelInvocable: 'disable-model-invocation' in meta ? !parseBool(meta['disable-model-invocation'], 'disable-model-invocation', path) : true,
    userInvocable: 'user-invocable' in meta ? parseBool(meta['user-invocable'], 'user-invocable', path) : true,
  }
  return {
    name: meta.name,
    description: meta.description,
    whenToUse: meta.whenToUse,
    invocation,
    content: raw.slice(match[0].length).trim(),
  }
}

/**
 * Register the bundled 数据分析师 skills as a preset-scoped provider.
 * @param {import('@deepseek-ai/cordis').Context} ctx - Context carrying the skill registry.
 */
export function apply(ctx) {
  const readSkill = async name => {
    const directory = join(ASSET_ROOT, name)
    const path = join(directory, 'SKILL.md')
    const raw = await readFile(path, 'utf8')
    return { name, directory, meta: parseSkill(raw, path) }
  }

  const listSkillNames = async () => {
    const entries = await readdir(ASSET_ROOT, { withFileTypes: true })
    return entries.filter(e => e.isDirectory()).map(e => e.name).sort()
  }

  ctx.skills.registerProvider(control => ({
    name: PROVIDER_NAME,
    async list(options) {
      let names
      try {
        names = await listSkillNames()
      } catch (error) {
        if (options?.signal?.aborted === true) throw error
        ctx.logger?.warn?.(`${PROVIDER_NAME}: 无法读取技能目录：${error}`)
        return { candidates: [], complete: false }
      }
      const candidates = []
      let complete = true
      for (const skillName of names) {
        let skill
        try {
          skill = await readSkill(skillName)
        } catch (error) {
          if (options?.signal?.aborted === true) throw error
          // 缺文件/格式错：跳过这一条，其余照常提供。
          ctx.logger?.warn?.(`${PROVIDER_NAME}: 技能 ${skillName} 不可用：${error}`)
          continue
        }
        if (skill.meta.name !== skillName) {
          ctx.logger?.warn?.(`${PROVIDER_NAME}: 技能 ${skillName} 的 frontmatter name 与目录名不符，跳过`)
          continue
        }
        const directory = skill.directory.split(sep).join('/')
        candidates.push({
          name: skill.meta.name,
          description: skill.meta.description,
          whenToUse: skill.meta.whenToUse,
          invocation: skill.meta.invocation,
          provider: PROVIDER_NAME,
          source: 'bundled',
          rank: BUNDLED_SKILL_RANK,
          path: join(directory, 'SKILL.md'),
          resourceBase: { kind: 'directory', path: directory },
          locator: skillName,
        })
      }
      return { candidates, complete }
    },
    async get(candidate, options) {
      const { rank: _rank, locator: _locator, ...summary } = candidate
      let skill
      try {
        skill = await readSkill(candidate.locator)
      } catch (error) {
        if (options?.signal?.aborted === true) throw error
        control.invalidate()
        return undefined
      }
      return { ...summary, content: skill.meta.content }
    },
  }))
}
