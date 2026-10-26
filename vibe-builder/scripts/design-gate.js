#!/usr/bin/env node
/* design-gate.js — deterministická brána vibe-builderu. Zero-dep, žádný model.
 *
 * Použití: node design-gate.js <dir-nebo-soubory...> [--dna <webDNA.md>]
 *                              [--seed-slug <slug>] [--reroll N]
 * Projde .tsx/.jsx/.html/.css zdroje a hledá vady, které model sám nad sebou
 * neodchytí. P1 = blokuje (exit 1). P2 = varování (exit 0).
 *
 * --dna: cesta k webDNA.md — brána z něj čte MOTION_TIER. Pravidla vrstvy
 *   „Text v pohybu" jsou P1 jen při tier ≥ 1; bez --dna se hlásí jako P2
 *   (tier nelze ověřit); tier 0 (dashboard/klidný web) je vypíná úplně.
 * --seed-slug: volitelná explicitní kontrola slugu. Běžně brána načte slug i
 *   reroll z řádku `concept_seed: slug|purpose|reroll=N` ve webDNA.md a ověří,
 *   že lib/motion.config.ts nese odpovídající lock.
 *
 * Zásada: brána smí zabít VADU, nikdy ROZHODNUTÍ. Všechna pravidla tady jsou
 * objektivní vady (klišé, placeholder, nečitelnost, rozbitá struktura) —
 * nikdy vkus. Pravidla nikdy nezměkčuj, aby build prošel; oprav build.
 */
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const EXT = new Set([".tsx", ".jsx", ".html", ".css", ".ts", ".js"]);
const SKIP_DIRS = new Set(["node_modules", ".next", "out", ".git", "public"]);

function collect(p, acc) {
  const st = fs.lstatSync(p);
  if (st.isSymbolicLink()) {
    throw new Error(`symbolický odkaz není povolen ve vstupu: ${p}`);
  }
  if (st.isDirectory()) {
    if (SKIP_DIRS.has(path.basename(p))) return;
    for (const f of fs.readdirSync(p)) collect(path.join(p, f), acc);
  } else if (EXT.has(path.extname(p))) acc.push(p);
}

// ---------- pravidla ----------
// [severity, regex, popis]  — severity: 1 = blokuje, 2 = varování
const RULES = [
  // Placeholdery a nedodělky (pozor: „Doplňte e-mail“ ve validaci je legit —
  // proto tu „doplňte“ NENÍ)
  [1, /lorem\s+ipsum/i, "lorem ipsum v obsahu"],
  [1, /\b(TODO|TBD|FIXME|XXX)\b/, "placeholder marker v kódu/copy"],
  [1, /\b(zde\s+bude|vaše\s+(nadpis|text|logo)\s+zde|text\s+doplníme)\b/i, "český placeholder v copy"],
  [1, /href="#"(?![\w-])/, "mrtvý odkaz href=\"#\""],

  // Fake brandy (AI výplně)
  [1, /\b(Acme|Nexus|Flowbit|NovaCore|Lorem\s?Corp|Globex|Initech)\b/, "fiktivní brandname"],
  [2, /\b(Apex|Vertex|Synergy|Zenith|Quantum\s?(Corp|Labs))\b/, "podezřelý generický brandname — ověř, že je reálný"],

  // Banned copy (CZ AI tells)
  [1, /revoluc\w+\s+v\b/i, "banned copy: „revoluce v X“"],
  [1, /transformac\w+\s+(vašeho|firmy|byznysu)/i, "banned copy: „transformace byznysu“"],
  [1, /posunout\s+(byznys|firmu|podnikání)\s+na\s+(další|novou)/i, "banned copy: „posunout na další úroveň“"],
  [1, /inovativní\s+řešení/i, "banned copy: „inovativní řešení“"],
  [2, /\b(seamless|next-gen|gamechanger|state-of-the-art)\b/i, "anglicismus v CZ copy"],

  // Meta-narace (stránka popisuje vlastní mechaniku)
  [1, /jak\s+(číst|procházet)\s+(tuto|tuhle)\s+stránk/i, "meta-narace: návod ke čtení stránky"],
  [1, /(scrolujte|skrolujte|rolujte)\s+(dál|dolů|níž)/i, "meta-narace: pokyn ke scrollu jako copy"],
  [1, /při\s+(scrollování|rolování)\s+(uvidíte|se\s+zobrazí)/i, "meta-narace: popis mechaniky"],
  [1, /tato\s+stránka\s+(vám\s+)?(ukazuje|ukáže|vysvětluje)/i, "meta-narace: stránka mluví o sobě"],

  // Obranné copy (agent prodává vlastní compliance místo produktu — reálný incident)
  [1, /bez\s+(přehnaných|velkých|planých)\s+(slibů|slov)/i, "obranné copy: stránka prodává opatrnost místo produktu"],
  [1, /žádn[éáý]\s+(falešn|generovan|vymyšlen|smyšlen)\w*/i, "obranné copy: vyjmenovává, co na stránce není"],
  [1, /reáln[ýáé]\s+asset/i, "obranné copy: interní žargon (asset) v klientském textu"],
  [1, /(ukazujeme|popisujeme)\s+(jen\s+)?(reáln|skutečn|opatrn)\w*/i, "obranné copy: stránka popisuje vlastní poctivost"],
  [1, /bez\s+neověřených\s+(čísel|údajů|tvrzení)/i, "obranné copy: compliance jazyk v copy"],

  // Vizuální slop
  [1, /from-(purple|indigo|violet|fuchsia)-\d+/, "purple/indigo/violet gradient (AI klišé #1)"],
  [1, /from-(blue|pink|rose)-\d+[^"]*to-(purple|indigo|violet|fuchsia|pink)-\d+/, "AI-klišé gradient pár"],
  // bg-clip-text: gradient text POVOLEN (brandový gradient z palety);
  // purple/duha klišé hlídají regexy výš, masku řeší structuralChecks
  [2, /backdrop-blur(?!-none)/, "glassmorphism — povolen jen s důvodem ve webDNA.md"],
  [1, /border-l-([2-9]|\d{2})\s+border-(blue|cyan|purple|green|red|amber)/, "barevný tlustý border-left (callout klišé)"],
  [2, /shadow-(md|lg|xl)[^"]*border\s|border[^"]*shadow-(md|lg|xl)/, "ghost card: border + výrazný stín současně"],

  // Česká diakritika: těsné řádkování klipuje háčky na verzálkách (Ř/Ý/Ž/Ů)
  [2, /leading-\[0\.\d+\]|leading-none/, "těsný line-height — česká diakritika na display se může klipovat (Ř/Ů), ověř screenshot"],
  [2, /text-transform:\s*uppercase[^}]*line-height:\s*(0\.\d+|1(\.0[0-4])?)\s*[;}]|line-height:\s*(0\.\d+|1(\.0[0-4])?)\s*;[^}]*text-transform:\s*uppercase/, "uppercase display s line-height < 1.05 — riziko kolize českých háčků, ověř screenshot s Ř/Ů"],

  // Typografie — Next.js deklaruje fonty přes next/font IMPORTY, ne font-family
  // banned-font pravidla ZRUŠENA (2026-08-05) — žádný font není zakázaný;
  // konvergenci řeší Web DNA pool (01-foundation.md „Ohranost fontů")
  [2, /tracking-tighter\b/, "tracking pod -0.04em — obvykle moc"],

  // Sekce 01/02/03
  [2, />\s*0[123]\s*</, "číslování sekcí 01/02/03 bez informační hodnoty"],

  // Pohybová doktrína (10-motion-web.md) — jen strojově jednoznačné vady.
  // Zákaz animace po písmenech se testuje na STRÁNKÁCH (structuralChecks),
  // ne tady — engine v lib/text-motion.ts helper deklaruje a nesmí padat.
  [2, /ease:\s*["'][\w.]*\.in["']/, "ease-in na tweenu — příchod nesmí mít pomalý rozjezd (rodina ease-out)"],
  [2, /(?:^|[\s"';:(])ease-in(?![-\w])/m, "ease-in v CSS/třídě — příchod jede ease-out (ease-in-out je povolený pro pohyb po obrazovce)"],
  [2, /transition:\s*all\b|\btransition-all\b/, "transition: all — vyjmenuj konkrétní vlastnosti (all animuje i to, co nemá, mimo GPU)"],
  [2, /scale\(0\)|scale:\s*0\s*[,}\n]/, "scale(0) jako stav animace — nic nevzniká z ničeho; startuj z 0.9–0.97 + opacity"],
  [2, /toggleActions:\s*["'][^"']*reverse/, "toggleActions s reverse — reveal se přehrává znovu při každém projetí; jednou nastoupí a STOJÍ (once: true)"],
];

// ---------- strukturální kontroly (nad rámec regexů) ----------
function structuralChecks(file, src, findings) {
  const isPage = /\.(tsx|jsx|html)$/.test(file);
  if (!isPage) return;

  // ZÁKAZ animace po písmenech (10-motion-web.md) — testuje se na stránkách,
  // aby deklarace helperu v lib/text-motion.ts nehlásila vadu sama o sobě.
  if (/data-motion="chars"/.test(src)) {
    findings.push([1, file, "data-motion=\"chars\" — animace po písmenech je zakázaná; použij words nebo lines"]);
  }
  if (/\bheroChars\s*\(/.test(src)) {
    findings.push([1, file, "volání heroChars() — animace po písmenech je zakázaná; použij words nebo linesMask()"]);
  }
  if (/\bdata-motion-ready\s*=/.test(src)) {
    findings.push([1, file, "data-motion-ready nesmí být zapsané v markupu — runtime marker nastavuje pouze text-motion engine"]);
  }

  // beaty/scény musí nést sdělení (Čitelnost, pravidlo 1)
  // DOM kontrakt: beat = element s className obsahujícím "beat" NEBO data-beat.
  // Detekce po TAZÍCH — element s oběma markery je JEDEN beat, ne dva.
  const beatTag = /<[a-zA-Z][^>]*(?:className="[^"]*\bbeat\b[^"]*"|data-beat)[^>]*>/g;
  const beatStarts = [...src.matchAll(beatTag)].map((m) => m.index + m[0].length);
  for (let k = 0; k < beatStarts.length; k++) {
    const end = k + 1 < beatStarts.length ? beatStarts[k + 1] : src.length;
    const seg = src.slice(beatStarts[k], end);
    if (!/<h[1-6][\s>]/.test(seg)) {
      findings.push([1, file, "beat/scéna bez nadpisu — efekt bez sdělení je zakázaný"]);
      break;
    }
  }

  // DOM kontrakt: sekce nesou data-anchor (jinak nelze kontrolovat variety)
  const sectionCount = (src.match(/<section[\s>]/g) || []).length;
  const anchors = [...src.matchAll(/data-anchor="([^"]+)"/g)].map((m) => m[1]);
  if (sectionCount >= 3 && anchors.length === 0) {
    findings.push([1, file, `${sectionCount} sekcí bez data-anchor — DOM kontrakt porušen, variety nekontrolovatelná`]);
  } else if (sectionCount > 0 && anchors.length === 0) {
    findings.push([2, file, "sekce bez data-anchor (DOM kontrakt)"]);
  }
  for (let i = 2; i < anchors.length; i++) {
    if (anchors[i] === anchors[i - 1] && anchors[i] === anchors[i - 2]) {
      findings.push([1, file, `3× stejný anchor za sebou (${anchors[i]}) — composition variety`]);
      break;
    }
  }

  // Eyebrow: nástroj (brand tag, wayfinding, kapitoly), ne reflex.
  // Slop = generický text bez informace NEBO mechanicky nad většinou sekcí.
  const eyebrowTags = [...src.matchAll(/<[a-zA-Z][^>]*class(?:Name)?="[^"]*\b(?:eyebrow|kicker)\b[^"]*"[^>]*>([^<]{0,80})</g)];
  for (const m of eyebrowTags) {
    if (/^\s*(naše\s+)?(služby|o\s+nás|o\s+firmě|náš\s+tým|proč\s+my|výhody|reference|kontakt|features|about|services|benefits|our\s+team)\s*$/i.test(m[1])) {
      findings.push([2, file, `generický eyebrow „${m[1].trim()}" — eyebrow nese značku/navigaci, ne prázdnou kategorii`]);
      break;
    }
  }
  if (sectionCount >= 4 && eyebrowTags.length >= Math.ceil(sectionCount * 0.6)) {
    findings.push([2, file, `eyebrow nad ${eyebrowTags.length}/${sectionCount} sekcemi — mechanické razítko; eyebrow patří tam, kde naviguje`]);
  }

  // Vnořené karty (Cardocalypse) — token scan hloubky <Card>
  let depth = 0;
  for (const m of src.matchAll(/<(\/?)Card[\s>]/g)) {
    if (m[1] === "/") depth = Math.max(0, depth - 1);
    else if (++depth > 1) {
      findings.push([1, file, "karta v kartě (Cardocalypse)"]);
      break;
    }
  }

  // rytmus obrazu: max 2 textové sekce po sobě, pak vizuální rozstřel
  const sections = src.match(/<section[\s\S]*?(?=<section[\s>]|<footer[\s>]|$)/g) || [];
  let textRun = 0, maxRun = 0;
  for (const s of sections) {
    const hasVisual = /<img[\s>]|<Image[\s>]|<canvas|<video|FilmHero|aspect-ratio|<svg[^>]*(viewBox="0 0 \d{3,}|width="\d{3,})/.test(s);
    textRun = hasVisual ? 0 : textRun + 1;
    maxRun = Math.max(maxRun, textRun);
  }
  if (maxRun >= 3) {
    findings.push([2, file, `${maxRun} textových sekcí po sobě bez vizuálu — rytmus obrazu (max 2, pak fotka/grafika)`]);
  }

  // ikony: delší stránka bez jediného SVG = textová zeď bez kotev
  if (sections.length >= 5 && !/<svg[\s>]|lucide/i.test(src)) {
    findings.push([2, file, "stránka bez jediné ikony/SVG — moderní ikony rozstřelují text (01-foundation.md)"]);
  }

  // typografická hra: nadpisy bez jediného zvýraznění = sterilní šablona
  const heads = src.match(/<h[12][^>]*>[\s\S]*?<\/h[12]>/g) || [];
  if (heads.length >= 3 &&
      !heads.some((h) => /<span|<em[\s>]|<i[\s>]|text-stroke/.test(h))) {
    findings.push([2, file, "nadpisy bez jediného zvýrazněného slova — typografická hra chybí (01-foundation.md)"]);
  }

  // motion ambice: GSAP bez jediného pin/scrub = stránka jede jen na reveals
  if (/gsap/.test(src) && /<section/.test(src) &&
      !/pin:\s*true|scrub:/.test(src)) {
    findings.push([2, file, "GSAP jen na reveals — žádný pin/scrub moment (motion ambice pod úrovní MotionSite základu)"]);
  }

  // hero: left-text + right-image klišé — heuristika přes první <section>.
  // Chytá i responsivní varianty (lg:grid-cols-2, md:flex-row) a custom grid;
  // okno 2600 znaků, protože hero markup bývá dlouhý (reálný únik: Bioptron).
  const firstSection = (src.match(/<section[\s\S]{0,2600}/) || [""])[0];
  const twoCol = /(^|[\s":])(?:(?:sm|md|lg|xl|2xl):)?(grid-cols-2\b|grid-cols-\[|flex-row\b)/.test(firstSection);
  if (twoCol && /(<img|<Image)/.test(firstSection) && /<h1/.test(firstSection)) {
    findings.push([2, file, "hero vypadá jako „text vlevo + obrázek vpravo“ (AI klišé #1) — ověř proti webDNA.md, archetyp musí být záměr, ne default"]);
  }

  // hero NIKDY zarovnaný vpravo (čte se zleva; pravá strana patří médiu —
  // justify-end na obrazových vrstvách je legitimní, signál je text-right)
  if (/<h1/.test(firstSection) && /text-right/.test(firstSection)) {
    findings.push([1, file, "hero text zarovnaný vpravo — zákaz; hero je centrovaný nebo levý (chrome roll)"]);
  }

  // čísla bez tabular-nums (stránka s metrikami)
  if (/\d{2,}[\s%+]/.test(src) && /className="[^"]*text-[5-9]xl/.test(src) &&
      !/tabular-nums/.test(src)) {
    findings.push([2, file, "velká čísla bez tabular-nums"]);
  }

  // bg-clip-text: gradient text je POVOLENÝ tah (rozhodnutí 2026-08-05 —
  // brandový gradient z palety, purple klišé hlídají regexy výš). Maska
  // obrazem/videem = legitimní technika; jen připomeň kontrast a fallback.
  if (/bg-clip-text/.test(src)) {
    for (const line of src.split("\n")) {
      if (!/bg-clip-text/.test(line)) continue;
      if (!/from-|via-|to-\w|linear-gradient/.test(line)) {
        findings.push([2, file, "bg-clip-text bez gradientu — text maskovaný obrazem je OK, ověř kontrast a fallback"]);
      }
      break;
    }
  }

  // h1/h2 schované v markupu: bez JS prázdný hero (SEO, a11y, no-JS probe)
  if (/<h[12][^>]*className="[^"]*\b(opacity-0|invisible)\b/.test(src)) {
    findings.push([1, file, "h1/h2 schovaný v markupu (opacity-0/invisible) — from-stav nastavuj v JS, výchozí stav = viditelný text"]);
  }
}

function writesMotionReady(src) {
  return /\.dataset(?:\.motionReady|\[\s*(["'`])motionReady\1\s*\])\s*=/.test(src)
    || /\bsetAttribute\s*\(\s*(["'`])data-motion-ready\1\s*,/.test(src);
}

// ---------- main ----------
function usage(out = console.error) {
  out("Použití: node design-gate.js <dir-nebo-soubory...> [--dna webDNA.md] [--seed-slug slug] [--reroll N]");
}

const argv = process.argv.slice(2);
const inputs = [];
let dnaPath = null, seedSlug = null, reroll = null;
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === "--help" || argv[i] === "-h") {
    usage(console.log);
    process.exit(0);
  } else if (argv[i] === "--dna" || argv[i] === "--seed-slug" || argv[i] === "--reroll") {
    const flag = argv[i];
    const value = argv[++i];
    if (!value || value.startsWith("--")) {
      console.error(`${flag}: chybí hodnota.`);
      usage();
      process.exit(2);
    }
    if (flag === "--dna") dnaPath = value;
    else if (flag === "--seed-slug") seedSlug = value;
    else {
      reroll = Number(value);
      if (!Number.isInteger(reroll) || reroll < 0) {
        console.error("--reroll musí být celé nezáporné číslo.");
        process.exit(2);
      }
    }
  } else if (argv[i].startsWith("--")) {
    console.error(`Neznámý přepínač: ${argv[i]}`);
    usage();
    process.exit(2);
  } else inputs.push(argv[i]);
}
if (!inputs.length) {
  usage();
  process.exit(2);
}
const files = [];
try {
  for (const a of inputs) collect(path.resolve(a), files);
} catch (error) {
  console.error(`Nelze projít vstup: ${error.message}`);
  process.exit(2);
}
if (!files.length) { console.error("Žádné zdrojové soubory nenalezeny."); process.exit(2); }
const resolvedInputs = inputs.map((input) => path.resolve(input));
const singleInputRoot = resolvedInputs.length === 1 && fs.lstatSync(resolvedInputs[0]).isDirectory()
  ? resolvedInputs[0]
  : null;
function commonParent(paths) {
  let candidate = path.dirname(paths[0]);
  while (paths.some((item) => item !== candidate && !item.startsWith(`${candidate}${path.sep}`))) {
    const parent = path.dirname(candidate);
    if (parent === candidate) break;
    candidate = parent;
  }
  return candidate;
}
const sourceRoot = singleInputRoot || commonParent(files);
const canonicalMotionEngine = path.join(sourceRoot, "lib", "text-motion.ts");

// MOTION_TIER z webDNA.md: tier ≥ 1 → textová pravidla P1; bez --dna → P2
// (tier neověřen); tier 0 → textová+motion pravidla vypnutá (dashboard nebo statický web).
let tier = null;
let dnaContent = null;
let seedProvenance = null;
let hasNoSeedProvenance = false;
if (dnaPath) {
  try {
    dnaContent = fs.readFileSync(dnaPath, "utf8");
  } catch {
    console.error(`--dna: nelze číst ${dnaPath}.`);
    process.exit(2);
  }

  const tierLines = [...dnaContent.matchAll(/^tier:\s*(\d+)\s*$/gm)];
  if (tierLines.length !== 1 || ![0, 1, 2, 3].includes(Number(tierLines[0]?.[1]))) {
    console.error("--dna: očekáván právě jeden samostatný řádek `tier: 0` až `tier: 3`.");
    process.exit(2);
  }
  tier = Number(tierLines[0][1]);

  const seedLines = [...dnaContent.matchAll(/^concept_seed:\s*(\S.*?)\s*$/gm)];
  if (seedLines.length !== 1) {
    console.error("--dna: očekáván právě jeden řádek `concept_seed: ...`.");
    process.exit(2);
  }
  const seedValue = seedLines[0][1];
  hasNoSeedProvenance = seedValue === "none";
  if (!hasNoSeedProvenance) {
    const seedMatch = /^([a-z0-9]+(?:-[a-z0-9]+)*)\|(web|funnel)\|reroll=(\d+)$/.exec(seedValue);
    if (!seedMatch) {
      console.error("--dna: concept_seed musí být `none` nebo `slug|purpose|reroll=N` ve formátu popsaném ve skillu.");
      process.exit(2);
    }
    seedProvenance = {
      slug: seedMatch[1],
      purpose: seedMatch[2],
      reroll: Number(seedMatch[3]),
    };
  }
}
const textActive = tier === null ? true : tier >= 1;
const textSev = tier !== null && tier >= 1 ? 1 : 2;
// servisní routy bez povinné textové vrstvy — testuje se jen KONEC cesty
// (route segment + soubor), nikdy celá absolutní cesta (např. UUID složka
// obsahující „404" by jinak vypnula pravidla celému projektu)
const TEXT_SKIP = /(not-found|error|404|dekujeme|thank|potvrzen|ochrana|osobn|podmink|obchodni|cookies|privacy|terms|gdpr)/i;
const isServiceRoute = (f) =>
  TEXT_SKIP.test(path.join(path.basename(path.dirname(f)), path.basename(f)));

const findings = [];
if (seedSlug && !dnaPath) {
  findings.push([1, files[0], "--seed-slug vyžaduje --dna s uloženým concept_seed původem"]);
} else if (seedSlug && dnaContent !== null && !seedProvenance) {
  findings.push([1, files[0], hasNoSeedProvenance
    ? "webDNA.md deklaruje concept_seed:none, ale brána dostala --seed-slug"
    : "webDNA.md postrádá platný concept_seed: slug|purpose|reroll=N"]);
}
if (seedSlug && seedProvenance && seedSlug !== seedProvenance.slug) {
  findings.push([1, files[0], `--seed-slug ${seedSlug} neodpovídá webDNA.md (${seedProvenance.slug})`]);
}
if (reroll !== null && seedProvenance && reroll !== seedProvenance.reroll) {
  findings.push([1, files[0], `--reroll ${reroll} neodpovídá webDNA.md (${seedProvenance.reroll})`]);
}
if (reroll !== null && !seedSlug && !seedProvenance) {
  findings.push([1, files[0], "--reroll nelze ověřit bez --seed-slug nebo concept_seed ve webDNA.md"]);
}
let anyAnimation = false, anyReducedMotion = false;
let projSplit = false, projLines = false, projScrub = false, h2Sections = 0, projImages = 0;
const motionVals = [];
for (const f of files) {
  const src = fs.readFileSync(f, "utf8");
  for (const [sev, re, msg] of RULES) {
    if (re.test(src)) findings.push([sev, f, msg]);
  }
  structuralChecks(f, src, findings);
  if (writesMotionReady(src) && path.resolve(f) !== canonicalMotionEngine) {
    findings.push([1, f, "runtime marker data-motion-ready smí nastavovat jen kanonický lib/text-motion.ts"]);
  }
  const hasActiveCssAnimation = [...src.matchAll(/animation\s*:\s*([^;}\n]+)/g)]
    .some((match) => !/^none(?:\s*!important)?\s*$/.test(match[1]));
  if (tier === 0 && (/gsap|ScrollTrigger|SplitText|data-motion=|@keyframes/.test(src) || hasActiveCssAnimation)) {
    findings.push([1, f, "tier 0 obsahuje scénickou animaci — povolené jsou jen stavové UI transitions"]);
  }
  // hover pohyb v ručně psaném CSS musí být za @media (hover: hover) —
  // na dotyku jinak prvek zůstane zaseknutý ve zvednutém stavu.
  // Kontroluje se JEN .css (Tailwind hover: varianty gatuje framework sám).
  if (/\.css$/.test(f) && /:hover[^{]*\{[^}]*(transform|translate|scale)/.test(src) &&
      !/\(\s*hover\s*:\s*hover\s*\)/.test(src)) {
    findings.push([2, f, ":hover s transformem bez @media (hover: hover) and (pointer: fine) — na dotyku zůstane prvek zvednutý"]);
  }
  if (/gsap|ScrollTrigger|animation:|@keyframes/.test(src)) anyAnimation = true;
  if (/prefers-reduced-motion|reduceMotion/.test(src)) anyReducedMotion = true;

  // ---- vrstva „Text v pohybu" (per soubor; agregáty níž) ----
  if (!textActive || !/\.(tsx|jsx|html)$/.test(f) || isServiceRoute(f)) continue;
  if (/SplitText|data-motion=/.test(src)) projSplit = true;
  if (/data-motion="lines"|type:\s*"lines|mask:\s*"lines|linesMask\(/.test(src)) projLines = true;
  if (/scrubText\(|data-motion="scrub"/.test(src)) projScrub = true;
  for (const s of src.match(/<section[\s\S]*?(?=<section[\s>]|<footer[\s>]|$)/g) || []) {
    if (/<h2[\s>]/.test(s)) h2Sections++;
  }
  motionVals.push(...[...src.matchAll(/data-motion="([^"]+)"/g)].map((m) => m[1]));
  projImages += (src.match(/<img[\s>]|<Image[\s>]/g) || []).length;
  // hero kontrakt: h1 nese data-motion (words/linesMask z lib/text-motion;
  // "chars" je zakázaná hodnota — hlídá structuralChecks)
  for (const tag of src.match(/<h1[^>]*>/g) || []) {
    if (!/data-motion=/.test(tag)) {
      findings.push([textSev, f, "h1 bez data-motion — hero choreografie chybí; volej words/linesMask() z lib/text-motion (10-motion-web.md)"]);
      break;
    }
  }
  // split bez choreografie = fade s extra kroky (obcházení vrstvy);
  // signál je SplitText.create (skutečné dělení), ne pouhý import/registrace
  if (/SplitText\.create/.test(src) && !/stagger/.test(src)) {
    findings.push([textSev, f, "SplitText.create bez staggeru — split bez choreografie; přítomnost tokenu není vrstva"]);
  }
}
// reduced-motion se posuzuje NA ÚROVNI PROJEKTU (sdílený hook je správný vzor,
// per-file kontrola by ho falešně trestala v každé komponentě)
if (anyAnimation && !anyReducedMotion) {
  findings.push([1, files[0], "projekt animuje, ale nikde nerespektuje prefers-reduced-motion"]);
}
// ---- projektové agregáty vrstvy „Text v pohybu" ----
if (textActive && anyAnimation) {
  if (!projSplit) {
    findings.push([textSev, files[0], "projekt s GSAP a nula SplitText — vrstva Text v pohybu chybí celá (10-motion-web.md)"]);
  }
  if (h2Sections >= 4 && !projLines) {
    findings.push([textSev, files[0], `${h2Sections} sekcí s h2 a žádný lines-mask reveal — sekční nadpisy jen fádují`]);
  }
  if (!projScrub) {
    findings.push([tier === 2 ? 1 : 2, files[0], "žádný scrub-text moment (scrubText / data-motion=\"scrub\") — 1 na stránku je standard"]);
  }
  if (motionVals.length >= 5 && new Set(motionVals).size === 1) {
    findings.push([1, files[0], `všech ${motionVals.length}× data-motion="${motionVals[0]}" — razítko; flavor variuje po sekcích`]);
  }
  if (h2Sections >= 4 && projImages <= 1) {
    findings.push([2, files[0], `${h2Sections} sekcí a ${projImages} obrázků — u fyzického produktu jsou lifestyle scény povinné (07-images.md)`]);
  }
}
if (tier !== null && tier >= 1 && projSplit) {
  if (!files.includes(canonicalMotionEngine)) {
    findings.push([1, files[0], "h1[data-motion] vyžaduje kanonický lib/text-motion.ts"]);
  } else {
    const engineSource = fs.readFileSync(canonicalMotionEngine, "utf8");
    if (!/SplitText\.create/.test(engineSource)) {
      findings.push([1, canonicalMotionEngine, "lib/text-motion.ts nepoužívá SplitText.create"]);
    }
    if (!writesMotionReady(engineSource)) {
      findings.push([1, canonicalMotionEngine, "lib/text-motion.ts nenastavuje runtime marker data-motion-ready"]);
    }
  }
}
// ---- motion podpis: config musí pocházet z concept-seed rollu ----
const effectiveSeedSlug = seedProvenance?.slug || seedSlug;
const effectiveReroll = seedProvenance?.reroll ?? reroll ?? 0;
const motionConfigs = files.filter((f) => /motion\.config\.(ts|js)$/.test(f));
const canonicalConfigCandidates = new Set([
  path.join(sourceRoot, "lib", "motion.config.ts"),
  path.join(sourceRoot, "lib", "motion.config.js"),
]);
const motionConfig = motionConfigs.find((f) => canonicalConfigCandidates.has(path.resolve(f)));
if (tier === 0 && motionConfigs.length) {
  for (const config of motionConfigs) {
    findings.push([1, config, "tier 0 nesmí obsahovat motion.config.ts"]);
  }
} else if (tier !== null && tier >= 1 && motionConfigs.length !== 1) {
  findings.push([1, files[0], `tier 1+ vyžaduje právě jeden kanonický lib/motion.config.ts; nalezeno ${motionConfigs.length}`]);
} else if (tier !== null && tier >= 1 && !motionConfig) {
  findings.push([1, motionConfigs[0] || files[0], "motion config musí být kanonický lib/motion.config.ts (ne decoy v jiné složce)"]);
} else if (tier !== null && tier >= 1 && effectiveSeedSlug) {
  const lock = crypto.createHash("sha256").update(`${effectiveSeedSlug}|motion|${effectiveReroll}`).digest("hex").slice(0, 12);
  if (!fs.readFileSync(motionConfig, "utf8").includes(lock)) {
    findings.push([1, motionConfig, "motion.config.ts nenese lock seedu — podpis přepsán tichým defaultem; vygeneruj znovu concept-seed.py"]);
  }
} else if (tier === null && textActive && anyAnimation && !motionConfig) {
  findings.push([2, files[0], "chybí lib/motion.config.ts — spusť bránu s --seed-slug pro ověření motion podpisu"]);
}

const p1 = findings.filter((x) => x[0] === 1);
const p2 = findings.filter((x) => x[0] === 2);
const rel = (f) => path.relative(process.cwd(), f);
for (const [, f, m] of p1) console.log(`P1  ${rel(f)}  ${m}`);
for (const [, f, m] of p2) console.log(`P2  ${rel(f)}  ${m}`);
console.log(`\ndesign-gate: ${files.length} souborů · P1: ${p1.length} · P2: ${p2.length}`);
if (p1.length) {
  console.log("BLOKOVÁNO — oprav P1 nálezy. Nikdy neupravuj bránu, aby prošla.");
  process.exit(1);
}
console.log(p2.length ? "PRŮCHOD s varováními (P2 posuď a rozhodni)." : "ČISTÝ PRŮCHOD.");
