#!/usr/bin/env node

import {
  createReadStream,
  existsSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  renameSync,
  rmSync,
  statSync,
  writeFileSync,
} from 'node:fs'
import { createServer } from 'node:http'
import { createRequire } from 'node:module'
import { createHash } from 'node:crypto'
import { basename, dirname, extname, isAbsolute, join, relative, resolve, sep } from 'node:path'

const require = createRequire(import.meta.url)

function usage() {
  console.log('Použití: node visual-gate.mjs <out-dir> --evidence <dir>')
}

function parseArgs(argv) {
  if (argv.includes('--help') || argv.includes('-h')) {
    usage()
    process.exit(0)
  }
  const root = argv[0]
  const evidenceIndex = argv.indexOf('--evidence')
  const evidence = evidenceIndex >= 0 ? argv[evidenceIndex + 1] : ''
  if (!root || !evidence) {
    usage()
    process.exit(2)
  }
  return { root: resolve(root), evidence: resolve(evidence) }
}

function assertNoSymlinkComponents(target, label) {
  let current = target
  while (true) {
    if (existsSync(current) && lstatSync(current).isSymbolicLink()) {
      throw new Error(`${label} nesmí obsahovat symlink: ${current}`)
    }
    const parent = dirname(current)
    if (parent === current) break
    current = parent
  }
}

function isWithin(parent, child) {
  const rel = relative(parent, child)
  return rel === '' || (!rel.startsWith(`..${sep}`) && rel !== '..' && !isAbsolute(rel))
}

function publishEvidence(staging, evidence) {
  const backup = `${evidence}.previous-${process.pid}-${Date.now()}`
  let movedOld = false
  try {
    if (existsSync(evidence)) {
      renameSync(evidence, backup)
      movedOld = true
    }
    renameSync(staging, evidence)
    if (movedOld) rmSync(backup, { recursive: true, force: true })
  } catch (error) {
    if (movedOld && !existsSync(evidence) && existsSync(backup)) renameSync(backup, evidence)
    throw error
  }
}

function walkHtml(root, current = root, acc = []) {
  for (const entry of readdirSync(current, { withFileTypes: true })) {
    const path = join(current, entry.name)
    if (entry.isSymbolicLink()) throw new Error(`Symlink není povolen ve vizuální bráně: ${path}`)
    if (entry.isDirectory()) walkHtml(root, path, acc)
    else if (entry.isFile() && entry.name.endsWith('.html')) acc.push(path)
  }
  return acc
}

function routeFor(root, file) {
  const rel = relative(root, file).split(sep).join('/')
  if (rel === 'index.html') return '/'
  if (rel.endsWith('/index.html')) return `/${rel.slice(0, -'index.html'.length)}`
  return `/${rel}`
}

function contentType(path) {
  return ({
    '.css': 'text/css; charset=utf-8',
    '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
    '.woff2': 'font/woff2',
  })[extname(path).toLowerCase()] || 'application/octet-stream'
}

function resolveRequest(root, requestUrl) {
  let pathname
  try {
    pathname = decodeURIComponent(new URL(requestUrl || '/', 'http://127.0.0.1').pathname)
  } catch {
    return null
  }
  const clean = pathname.replace(/^\/+/, '')
  let candidate = resolve(root, clean || 'index.html')
  if (candidate !== root && !candidate.startsWith(`${root}${sep}`)) return null
  if (existsSync(candidate) && statSync(candidate).isDirectory()) candidate = join(candidate, 'index.html')
  if (!existsSync(candidate) && !extname(candidate)) candidate = `${candidate}.html`
  if (!existsSync(candidate) || !statSync(candidate).isFile()) return null
  return candidate
}

async function listen(root) {
  const server = createServer((request, response) => {
    const file = resolveRequest(root, request.url)
    if (!file) {
      response.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' })
      response.end('Not found')
      return
    }
    response.writeHead(200, { 'content-type': contentType(file) })
    createReadStream(file).pipe(response)
  })
  await new Promise((resolveListen, reject) => {
    server.once('error', reject)
    server.listen(0, '127.0.0.1', resolveListen)
  })
  const address = server.address()
  if (!address || typeof address === 'string') throw new Error('Lokální QA server nezískal port')
  return { server, origin: `http://127.0.0.1:${address.port}` }
}

function safeName(route) {
  const normalized = route.replace(/^\/+|\/+$/g, '').replace(/[^a-z0-9-]+/gi, '-')
  const suffix = createHash('sha256').update(route).digest('hex').slice(0, 8)
  return `${normalized || 'home'}-${suffix}`
}

async function assertPage(page, url, label, { requireMotionReady = true } = {}) {
  const errors = []
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(`console: ${message.text()}`)
  })
  page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`))
  const response = await page.goto(url, { waitUntil: 'load', timeout: 30_000 })
  if (!response || response.status() >= 400) throw new Error(`${label}: HTTP ${response?.status() || 'bez odpovědi'}`)
  if (requireMotionReady) {
    try {
      await page.waitForFunction(() => {
        const hero = document.querySelector('h1')
        return !hero?.matches('[data-motion]') || Boolean(hero.getAttribute('data-motion-ready'))
      }, undefined, { timeout: 3_000 })
    } catch {
      // Stav níže vytvoří srozumitelný gate nález; čekání je jen bounded
      // tolerance pro pomalejší hydrataci, ne druhý zdroj výsledku.
    }
    // Marker potvrzuje hydrataci; krátký bounded odstup nechá prohlížeč
    // dokončit aktuální paint před měřením a screenshotem.
    await page.waitForTimeout(100)
  }
  const state = await page.evaluate(() => {
    const h1 = document.querySelector('h1')
    const style = h1 ? getComputedStyle(h1) : null
    const rect = h1?.getBoundingClientRect()
    return {
      h1Text: h1?.textContent?.trim() || '',
      h1Visible: Boolean(h1 && style && rect && style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) > 0 && rect.width > 0 && rect.height > 0),
      motionHero: Boolean(h1?.matches('[data-motion]')),
      motionReady: h1?.getAttribute('data-motion-ready') || '',
      motionFragments: h1?.querySelectorAll('*').length || 0,
      overflow: Math.max(document.documentElement.scrollWidth, document.body?.scrollWidth || 0) - window.innerWidth,
    }
  })
  if (!state.h1Text || !state.h1Visible) errors.push('hero h1 není viditelný')
  if (state.overflow > 1) errors.push(`vodorovný overflow ${state.overflow}px`)
  if (requireMotionReady && state.motionHero && !state.motionReady) errors.push('h1[data-motion] nemá runtime potvrzení data-motion-ready')
  if (requireMotionReady && state.motionHero && state.motionFragments < 2) errors.push('h1[data-motion] nemá split fragmenty')
  if (errors.length) throw new Error(`${label}: ${errors.join('; ')}`)
  return state
}

async function captureScreenshot(page, path) {
  try {
    await page.screenshot({ path, fullPage: true })
  } catch (error) {
    // Chromium může při souběžné zátěži jednou odmítnout Page.captureScreenshot.
    // Jediný bounded retry řeší jen tento transportní jev; obsahové chyby dál padají.
    if (!String(error).includes('Unable to capture screenshot')) throw error
    await page.waitForTimeout(200)
    await page.screenshot({ path, fullPage: true })
  }
}

async function main() {
  const { root, evidence } = parseArgs(process.argv.slice(2))
  assertNoSymlinkComponents(root, 'Output cesta')
  if (!existsSync(root) || !lstatSync(root).isDirectory()) throw new Error(`Output složka neexistuje nebo je symlink: ${root}`)
  const projectRoot = dirname(root)
  if (!isWithin(projectRoot, evidence) || isWithin(root, evidence) || isWithin(evidence, root)) {
    throw new Error(`Evidence musí být samostatná složka uvnitř projektu ${projectRoot}`)
  }
  assertNoSymlinkComponents(evidence, 'Evidence cesta')
  const routes = [...new Set(walkHtml(root).map((file) => routeFor(root, file)))].sort()
  if (!routes.length) throw new Error(`V ${root} není žádná HTML routa`)
  const evidenceParent = dirname(evidence)
  mkdirSync(evidenceParent, { recursive: true })
  assertNoSymlinkComponents(evidence, 'Evidence cesta')
  if (existsSync(evidence) && !lstatSync(evidence).isDirectory()) {
    throw new Error(`Evidence cesta není složka: ${evidence}`)
  }
  let chromium
  try {
    ;({ chromium } = require('playwright'))
  } catch {
    // Repository tests install @playwright/test; provider image ships the
    // standalone playwright package globally through NODE_PATH.
    ;({ chromium } = require('@playwright/test'))
  }
  const { server, origin } = await listen(root)
  let staging = ''
  let browser
  let runError
  const report = {
    skillVersion: '1.3.4',
    evidenceVersion: 1,
    root,
    evidence,
    routes,
    checks: [],
    generatedAt: new Date().toISOString(),
  }
  try {
    staging = mkdtempSync(join(evidenceParent, `.${basename(evidence)}.tmp-`))
    browser = await chromium.launch({ args: ['--no-sandbox'] })
    for (const route of routes) {
      for (const viewport of [
        { name: 'desktop', width: 1440, height: 900 },
        { name: 'mobile', width: 390, height: 844 },
      ]) {
        const page = await browser.newPage({ viewport: { width: viewport.width, height: viewport.height } })
        const state = await assertPage(page, `${origin}${route}`, `${route} ${viewport.name}`)
        const screenshotName = `${safeName(route)}-${viewport.name}.png`
        await captureScreenshot(page, join(staging, screenshotName))
        report.checks.push({ route, mode: viewport.name, screenshot: join(evidence, screenshotName), ...state })
        await page.close()
      }

      const reduced = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' })
      await assertPage(reduced, `${origin}${route}`, `${route} reduced-motion`, { requireMotionReady: false })
      report.checks.push({ route, mode: 'reduced-motion' })
      await reduced.close()

      const noJsContext = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } })
      const noJs = await noJsContext.newPage()
      await assertPage(noJs, `${origin}${route}`, `${route} no-js`, { requireMotionReady: false })
      report.checks.push({ route, mode: 'no-js' })
      await noJsContext.close()
    }
    writeFileSync(join(staging, 'report.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8')
  } catch (error) {
    runError = error
  } finally {
    try {
      if (browser) await browser.close()
    } catch (error) {
      runError ??= error
    }
    try {
      await new Promise((resolveClose, rejectClose) => server.close((error) => error ? rejectClose(error) : resolveClose()))
    } catch (error) {
      runError ??= error
    }
  }
  if (runError) {
    if (staging && existsSync(staging)) rmSync(staging, { recursive: true, force: true })
    throw runError
  }
  try {
    publishEvidence(staging, evidence)
    staging = ''
    console.log(`visual-gate: ${routes.length} rout · ${report.checks.length} kontrol · evidence ${evidence}`)
  } finally {
    if (staging && existsSync(staging)) rmSync(staging, { recursive: true, force: true })
  }
}

main().catch((error) => {
  console.error(`visual-gate: FAIL — ${error instanceof Error ? error.message : String(error)}`)
  process.exit(1)
})
