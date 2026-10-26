#!/usr/bin/env python3
"""Build machine contractu pro Viral DNA Card™ (hloubkový rozbor JEDNOHO donora).

Deterministická část (stats, formát short/long, engagement, stažení náhledu,
extrakce framů z videa, GDPR-safe surovina z komentářů) žije tady; renderer
`dnacard.py` contract jen vykresluje. **Sémantiku** (vizuální DNA, textová DNA,
kostra, destilát publika, klon-recept, překlad titulku) plní MODEL za běhu —
stejný vzor jako Viral Ad Board (build → model → render).

Vstup = normalizovaný donor z `provider.donor_meta` (organika) nebo kanonická
reklama z Ad Library (adlib donor / karta z boardu), + volitelně komentáře
(`provider.content_comments`) a přepis.

Výstup = `dna-card.json` (schéma v references/viral-dna-card.md).

Analýza podle formátu (spec §6):
  dlouhé (YouTube long / podcast / LinkedIn) → přepis + 1 náhled (žádné framy)
  krátké (reels / shorts / TikTok)           → framy + vision (thumb = first frame)

v0.1 — deterministická kostra; sémantiku doplní model.
"""
import datetime
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adboard_build import content_format, dl_thumb  # noqa: E402

TRANSCRIPT_MAX = 9000     # znaků přepisu do contractu (model potřebuje kostru, ne celý román)
COMMENTS_TOP = 45         # kolik top komentářů (podle lajků) jde do suroviny pro model
FRAMES_N = 6              # kolik framů z videa (krátký formát)


def _num(x):
    try:
        return int(float(x))
    except Exception:
        return None


def _eng_pct(likes, views):
    l, v = _num(likes), _num(views)
    if not l or not v:
        return None
    return round(l / v * 100, 1)


def ffprobe_dur(path):
    """Délka videa v sekundách (ffprobe). None když nejde zjistit."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path],
            capture_output=True, text=True, timeout=30).stdout.strip()
        return float(out)
    except Exception:
        return None


def extract_frames(video_path, out_dir, n=FRAMES_N):
    """Rovnoměrně rozložené framy z videa (ffmpeg, lokálně, zdarma). Vrací cesty.
    Framy = vstup pro vision analýzu MODELEM (hook, tempo, text v obraze) —
    jen k rozboru, nikdy do klientského výstupu jako rehost."""
    dur = ffprobe_dur(video_path)
    if not dur or dur <= 0:
        return []
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i in range(n):
        ts = dur * (i + 0.5) / n
        out = os.path.join(out_dir, f"frame-{i + 1:02d}.jpg")
        try:
            subprocess.run(["ffmpeg", "-y", "-ss", f"{ts:.2f}", "-i", video_path,
                            "-frames:v", "1", "-q:v", "3", out],
                           capture_output=True, timeout=60)
        except Exception:
            continue
        if os.path.isfile(out) and os.path.getsize(out) > 2000:
            paths.append(out)
    return paths


def _clean_transcript(t):
    """Očistí přepis (SRT časování, prázdné řádky) na souvislý text pro model."""
    if not t:
        return None
    t = re.sub(r"\d+\s*\n\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}\s*\n", " ", t)
    t = re.sub(r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:TRANSCRIPT_MAX] or None


def _comments_material(comments):
    """Top komentáře podle lajků → surovina pro model (destilaci dělá model).
    GDPR: provider už strhal autory; tady jen text + lajky."""
    if not comments:
        return []
    flat = []
    for c in comments:
        if isinstance(c, dict) and c.get("text"):
            flat.append({"text": str(c["text"])[:280], "likes": int(c.get("likes") or 0)})
    flat.sort(key=lambda x: -x["likes"])
    return flat[:COMMENTS_TOP]


def _donor_from_ad(ad):
    """Kanonická reklama (Ad Library / karta z boardu) → jednotný donor tvar."""
    return {
        "sit": "meta", "typ": "reklama",
        "nm": ad.get("nm") or ad.get("ad_creative_link_title") or "",
        "kdo": ad.get("inzerent") or ad.get("page_name"),
        "url": ad.get("url") or ad.get("ad_snapshot_url"),
        "thumb": ad.get("thumb") or ad.get("thumbnail"),
        "video_url": ad.get("video_url"),
        "popis": ad.get("_text") or ad.get("ad_creative_body"),
        "dur": None, "zhlednuti": None, "likes": None, "cmts": None, "shares": None,
        "dosah_eu": ad.get("dosah_eu") or ad.get("reach"),
        "dni": ad.get("dni"), "varianty": ad.get("varianty"),
        "transcript": None,
    }


def build(donor, tema=None, trh="cz", comments=None, transcript=None,
          frames_paths=None, run_dir=None):
    """Sestaví dna-card.json. `donor` = z provider.donor_meta (organika) NEBO
    {'sit':'adlib','ad':…} (reklama) NEBO karta z rich-contract.json boardu.
    Sémantické sekce nechává prázdné — plní je MODEL (viz reference)."""
    if donor.get("sit") == "adlib" or donor.get("typ") == "reklama" or "inzerent" in donor:
        d = _donor_from_ad(donor.get("ad") or donor)
    else:
        d = dict(donor)
        d["typ"] = "organika"
        d.pop("_raw", None)

    fmt = "video" if d["typ"] == "reklama" else content_format(d.get("sit"), d.get("dur"))
    if d["typ"] == "reklama":
        fmt = "short" if d.get("video_url") else "static"

    thumb = d.get("thumb")
    if run_dir and thumb and str(thumb).startswith("http"):
        thumb = dl_thumb(thumb, os.path.join(run_dir, "thumb.jpg")) or thumb
    video = d.get("video") or d.get("video_url")
    if run_dir and os.path.exists(os.path.join(run_dir, "video.mp4")):
        video = os.path.join(run_dir, "video.mp4")   # lokální kopie → play tlačítko na kartě
    tr = _clean_transcript(transcript or d.get("transcript"))

    contract = {
        "meta": {"skill": "ad-scout", "vystup": "viral-dna-card", "tema": tema, "trh": trh,
                 "sken": datetime.date.today().isoformat(), "url": d.get("url")},
        "donor": {
            "sit": d.get("sit"), "typ": d["typ"], "format": fmt,
            "nm": d.get("nm"), "orig": None,          # model: český titulek + originál
            "kdo": d.get("kdo"), "url": d.get("url"),
            "kanal_url": d.get("kanal_url"),           # profil/kanál autora (renderer umí dovodit z url)
            "thumb": thumb, "video": video,
            "dur": d.get("dur"), "zhlednuti": d.get("zhlednuti"), "likes": d.get("likes"),
            "cmts": d.get("cmts"), "shares": d.get("shares"),
            "engagement_pct": _eng_pct(d.get("likes"), d.get("zhlednuti")),
            "dosah_eu": d.get("dosah_eu"), "dni": d.get("dni"), "varianty": d.get("varianty"),
            "proc_donor": None,                        # model: proč je to dobrý donor (1–2 věty)
        },
        # 01 — vision rozbor náhledu/framů (radky {k,v}; v smí nést <b>); vzorce = chipy
        "vizualni_dna": {"radky": [], "vzorce": [], "frames": frames_paths or []},
        # 02 — hook · úhel+povědomí · formát · nabídka/CTA (radky) + kostra
        "textova_dna": {"radky": [], "kostra": None,
                        "kostra_zdroj": ("přepis" if tr else "odhad z textu")},
        "prepis": {"stav": ("ok" if tr else "chybi"), "text": tr,
                   "hook_3s": None,                    # model: mluvený hook z prvních ~3 s
                   "poznamka": None},
        # 03 — Raw Diet destilát (model z _surovina.komentare; bez jmen — GDPR)
        "publikum": {"namitky": [], "touhy": [], "fraze": [], "triggery": [],
                     "zdroj_pocet": len(comments or []), "poznamka": None},
        # → klon-recept pro makery: V (vizuál) · H (hook) · U (úhel) · F (formát+nabídka)
        "klon": [],
        # surovina JEN pro model — renderer ji NEVYKRESLUJE, do klientského výstupu nejde
        "_surovina": {"popis_raw": d.get("popis"),
                      "komentare": _comments_material(comments)},
    }
    return contract
