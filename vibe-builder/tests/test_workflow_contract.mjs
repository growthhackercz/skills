#!/usr/bin/env node
/** Static contract regressions for the workflow text and bundled checkpoint. */
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const skill = readFileSync(join(root, 'SKILL.md'), 'utf8')
const direction = readFileSync(join(root, 'references', '09-direction.md'), 'utf8')
const copy = readFileSync(join(root, 'references', '08-copywriting.md'), 'utf8')
const stack = readFileSync(join(root, 'references', '05-stack.md'), 'utf8')
const images = readFileSync(join(root, 'references', '07-images.md'), 'utf8')
const motionFilm = readFileSync(join(root, 'references', '11-motion-film.md'), 'utf8')
const carousel = readFileSync(join(root, 'references', '14-carousel-images.md'), 'utf8')
const leadTemplate = readFileSync(join(root, 'references', 'lead-form.template.mjs'), 'utf8')
const leadReference = readFileSync(join(root, 'references', '15-lead-magnet-pages.md'), 'utf8')
const contract = JSON.parse(readFileSync(join(root, 'skill-contract.json'), 'utf8'))
const results = []

function check(condition, description) {
  results.push([Boolean(condition), description])
}

check(
  skill.includes('pokračuj rovnou Krokem 5')
    && skill.includes('Krok 4 — Commit světa → webDNA.md → STOP (jen web / landing / funnel)'),
  'dashboard/app skips the scenic world-commit step',
)
check(
  skill.includes('outputLanguage')
    && skill.includes('podle jazyka klienta/SOUL')
    && copy.includes('České tvary, vykání a metriky níže platí pouze pro `cs`'),
  'copy workflow binds output language and scopes Czech rules to cs',
)
check(
  direction.includes('skillVersion: "1.3.4"')
    && skill.includes('s frontmatterem `skillVersion: "1.3.4"'),
  'webDNA and COPY templates carry a machine-readable skill version',
)
check(
  stack.includes('"skillVersion": "1.3.4"')
    && images.includes('skillVersion: "1.3.4"')
    && skill.includes('Soubor vždy začni YAML frontmatterem `skillVersion: "1.3.4"`'),
  'package and persistent brand-context artifacts carry the current skill version',
)

const requires = contract?.taskCheckpoints?.['site-draft-package']?.requires || []
const containsChecks = requires
  .map((entry) => entry?.fileContains)
  .filter(Boolean)
check(
  containsChecks.some((entry) => entry.path.endsWith('/webDNA.md') && entry.contains === 'skillVersion: "1.3.4"')
    && containsChecks.some((entry) => entry.path.endsWith('/COPY.md') && entry.contains === 'skillVersion: "1.3.4"'),
  'task checkpoint rejects unversioned webDNA/COPY artifacts',
)
check(
  containsChecks.some((entry) => entry.path.endsWith('/package.json') && entry.contains === '"skillVersion": "1.3.4"'),
  'task checkpoint rejects an unversioned generated package manifest',
)
check(
  containsChecks.some((entry) => entry.path.endsWith('/COPY.md') && entry.contains === 'outputLanguage:'),
  'task checkpoint requires an explicit COPY output language field',
)
check(
  skill.includes('`--dry-run`')
    && skill.includes('`--max-usd`')
    && skill.includes('Přímé `fal_client`')
    && motionFilm.includes('`--dry-run`')
    && motionFilm.includes('`--max-usd`')
    && !motionFilm.includes('fal_client.subscribe')
    && images.includes('kumulativním `--max-usd`')
    && carousel.includes('kumulativním `--max-usd`'),
  'every documented paid FAL path requires a machine cap and forbids direct calls',
)
check(
  skill.includes('Kontrakt je obrana navíc, ne náhrada vlastní kontroly')
    && skill.includes('přechod do review prochází checkpoint'),
  'workflow does not overclaim that every platform review path enforces checkpoints',
)
check(
  leadTemplate.includes('Volitelné: MAGNET_TAG')
    && !leadTemplate.includes('Povinné klíče: GHL_API_KEY, GHL_LOCATION_ID, LEAD_GUARD_SECRET, MAGNET_TAG')
    && /\| `MAGNET_TAG` \| ne \|/.test(leadReference)
    && leadReference.includes('je-li `MAGNET_TAG` nastavený')
    && leadReference.includes('bez něj se tag neočekává'),
  'lead template and reference agree that MAGNET_TAG is optional',
)

for (const [passed, description] of results) {
  console.log(`${passed ? 'PASS' : 'FAIL'}  ${description}`)
}
const failed = results.filter(([passed]) => !passed).length
console.log(`\n${results.length - failed}/${results.length} prošlo`)
process.exitCode = failed ? 1 : 0
