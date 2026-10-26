#!/usr/bin/env node
/**
 * fetch-images.mjs — Pexels API: fotky i VIDEA pro AIQ funnel + probe rozměrů.
 *
 * Použití (z rootu appky):
 *   PEXELS_API_KEY=... node scripts/fetch-images.mjs \
 *     --query "glass of water kitchen daylight" --out public/img/hero.jpg \
 *     [--orientation landscape] [--min-width 1600]
 *
 *   # video pozadí (mp4, ideálně 1280–1920 px šířka):
 *   PEXELS_API_KEY=... node scripts/fetch-images.mjs --type video \
 *     --query "water pouring glass slow motion" --out public/img/hero-video.mp4
 *
 *   # rozměry existujícího PNG/JPEG (pro aspect-ratio mockupu):
 *   node scripts/fetch-images.mjs --probe public/img/mockup.png
 *
 * Chování:
 *   - klíč čte VÝHRADNĚ z env PEXELS_API_KEY (nikdy nelogovat hodnotu)
 *   - exit 0 = OK; exit 2 = chybí PEXELS_API_KEY (→ přejdi na fallback);
 *     exit 3 = žádný výsledek pro query; exit 1 = jiná chyba
 *
 * Pexels licence: fotky i videa zdarma pro komerční použití, atribuce nepovinná.
 */

import { writeFile, mkdir, readFile } from "node:fs/promises";
import { dirname } from "node:path";

function arg(name, fallback = undefined) {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

/* ---- --probe: vypiš rozměry PNG/JPEG a skonči ---- */
const probePath = arg("probe");
if (probePath) {
  try {
    const b = await readFile(probePath);
    let w = 0, h = 0;
    if (b[0] === 0x89 && b[1] === 0x50) {
      // PNG: IHDR na offsetu 16
      w = b.readUInt32BE(16); h = b.readUInt32BE(20);
    } else if (b[0] === 0xff && b[1] === 0xd8) {
      // JPEG: najdi SOF0/SOF2 marker
      let i = 2;
      while (i < b.length - 9) {
        if (b[i] !== 0xff) { i++; continue; }
        const m = b[i + 1];
        if (m >= 0xc0 && m <= 0xcf && m !== 0xc4 && m !== 0xc8 && m !== 0xcc) {
          h = b.readUInt16BE(i + 5); w = b.readUInt16BE(i + 7); break;
        }
        i += 2 + b.readUInt16BE(i + 2);
      }
    }
    if (!w || !h) { console.error("[probe] Nerozpoznaný formát."); process.exit(1); }
    console.log(`${w}x${h} aspect-ratio: ${w} / ${h}`);
    process.exit(0);
  } catch (e) {
    console.error(`[probe] ${e?.message ?? e}`);
    process.exit(1);
  }
}

const query = arg("query");
const out = arg("out");
const type = arg("type", "photo"); // photo | video
const orientation = arg("orientation", "landscape");
const minWidth = parseInt(arg("min-width", "1600"), 10);

if (!query || !out) {
  console.error("Použití: node fetch-images.mjs --query \"...\" --out public/img/hero.jpg [--type video] | --probe <soubor>");
  process.exit(1);
}

const key = process.env.PEXELS_API_KEY;
if (!key) {
  console.error("[fetch-images] PEXELS_API_KEY není nastavený — použij fallback (browser tool / image_generate).");
  process.exit(2);
}

const isVideo = type === "video";
const url = new URL(isVideo ? "https://api.pexels.com/videos/search" : "https://api.pexels.com/v1/search");
url.searchParams.set("query", query);
url.searchParams.set("orientation", orientation);
url.searchParams.set("per_page", "10");
if (!isVideo) url.searchParams.set("size", "large");

try {
  const res = await fetch(url, { headers: { Authorization: key } });
  if (!res.ok) {
    console.error(`[fetch-images] Pexels API vrátilo ${res.status} — použij fallback.`);
    process.exit(res.status === 401 ? 2 : 1);
  }
  const data = await res.json();

  let src, label;
  if (isVideo) {
    // Vyber video s HD souborem 1280–1920 px šířky (rozumná váha pro web).
    const vids = data.videos ?? [];
    let best = null;
    for (const v of vids) {
      const files = (v.video_files ?? [])
        .filter((f) => f.file_type === "video/mp4" && f.width >= 1280 && f.width <= 1920)
        .sort((a, b) => b.width - a.width);
      if (files.length) { best = { v, f: files[0] }; break; }
    }
    if (!best) {
      console.error(`[fetch-images] Žádné vhodné video pro query "${query}" — zkus jiný dotaz nebo fallback.`);
      process.exit(3);
    }
    src = best.f.link;
    label = `video #${best.v.id} (${best.f.width}×${best.f.height}, autor: ${best.v.user?.name ?? "?"}) · ${best.v.url}`;
  } else {
    const photos = (data.photos ?? []).filter((p) => p.width >= minWidth);
    if (photos.length === 0) {
      console.error(`[fetch-images] Žádné foto ≥${minWidth}px pro query "${query}" — zkus jiný dotaz nebo fallback.`);
      process.exit(3);
    }
    photos.sort((a, b) => b.width * b.height - a.width * a.height);
    const photo = photos[0];
    src = photo.src.large2x || photo.src.original;
    label = `foto #${photo.id} (${photo.width}×${photo.height}, fotograf: ${photo.photographer}) · ${photo.url}`;
  }

  const file = await fetch(src);
  if (!file.ok) {
    console.error(`[fetch-images] Stažení selhalo (${file.status}).`);
    process.exit(1);
  }
  await mkdir(dirname(out), { recursive: true });
  const buf = Buffer.from(await file.arrayBuffer());
  await writeFile(out, buf);
  console.log(`[fetch-images] OK: ${out} (${Math.round(buf.length / 1024)} kB) ← Pexels ${label}`);
} catch (e) {
  console.error(`[fetch-images] Chyba: ${e?.message ?? e}`);
  process.exit(1);
}
