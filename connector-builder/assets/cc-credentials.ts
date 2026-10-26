import { existsSync, readFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { basename, join } from 'node:path'

type JsonObject = Record<string, unknown>
type CredentialEnvironment = Readonly<Record<string, string | undefined>>

export interface CredentialLookupOptions {
  home?: string
  env?: CredentialEnvironment
}

function readObject(path: string): JsonObject {
  if (!existsSync(path)) return {}
  let value: unknown
  try {
    value = JSON.parse(readFileSync(path, 'utf8'))
  } catch {
    throw new Error(`Credential store is not valid JSON: ${basename(path)}`)
  }
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as JsonObject
    : {}
}

function normalizeName(name: string): string {
  return name.trim().toUpperCase()
}

function resolveOpenClawHome(options: CredentialLookupOptions): string {
  if (options.home) return options.home
  const env = options.env ?? process.env
  const configured = (env.OPENCLAW_HOME || env.CC_OPENCLAW_HOME || '').trim()
  if (!configured) return join(homedir(), '.openclaw')
  if (basename(configured) === '.openclaw' || basename(configured) === '.clawdbot') {
    return configured
  }
  const nested = join(configured, '.openclaw')
  return existsSync(nested) ? nested : configured
}

function readRuntimeEnv(path: string): Record<string, string> {
  if (!existsSync(path)) return {}
  const values: Record<string, string> = {}
  for (const rawLine of readFileSync(path, 'utf8').split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#') || !line.includes('=')) continue
    const separator = line.indexOf('=')
    const key = normalizeName(line.slice(0, separator))
    let value = line.slice(separator + 1).trim()
    if (
      value.length >= 2 &&
      ((value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'")))
    ) {
      value = value.slice(1, -1)
    }
    if (key) values[key] = value
  }
  return values
}

function readSecretStore(home: string): Record<string, string> {
  const raw = readObject(join(home, 'control-center-secrets.json'))
  return Object.fromEntries(
    Object.entries(raw).filter((entry): entry is [string, string] =>
      typeof entry[1] === 'string' && entry[1].length > 0
    ),
  )
}

function resolveCustomVariable(
  name: string,
  home: string,
  secrets: Record<string, string>,
): string {
  const credentials = readObject(join(home, 'control-center-credentials.json'))
  const rawVariables = credentials.variables
  const variables =
    rawVariables && typeof rawVariables === 'object' && !Array.isArray(rawVariables)
      ? rawVariables as JsonObject
      : {}
  const rawEntry = variables[name]
  const entry =
    rawEntry && typeof rawEntry === 'object' && !Array.isArray(rawEntry)
      ? rawEntry as JsonObject
      : {}

  if (entry.visibility === 'secret' && typeof entry.secretRef === 'string') {
    return secrets[entry.secretRef.trim().replace(/^\/+/, '')]?.trim() || ''
  }
  return typeof entry.value === 'string' ? entry.value.trim() : ''
}

/**
 * Resolves a server-side connector credential without caching.
 *
 * Control Center custom variables are authoritative in agent runtime. Direct
 * secret-store entries, process env (for Netlify), and the legacy runtime .env
 * file are compatibility fallbacks in that order.
 */
export function getEnvOrVariable(
  name: string,
  options: CredentialLookupOptions = {},
): string {
  const normalized = normalizeName(name)
  if (!normalized) return ''

  const home = resolveOpenClawHome(options)
  const secrets = readSecretStore(home)
  const customVariable = resolveCustomVariable(normalized, home, secrets)
  if (customVariable) return customVariable

  const directSecret = secrets[normalized]?.trim()
  if (directSecret) return directSecret

  const env = options.env ?? process.env
  const processValue = env[normalized]?.trim()
  if (processValue) return processValue

  return readRuntimeEnv(join(home, '.env'))[normalized]?.trim() || ''
}

export function requireCredential(
  name: string,
  options: CredentialLookupOptions = {},
): string {
  const normalized = normalizeName(name)
  const value = getEnvOrVariable(normalized, options)
  if (!value) throw new Error(`Missing required credential ${normalized}`)
  return value
}
