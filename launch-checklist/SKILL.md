---
name: launch-checklist
description: "Připravuje checklist a koordinaci pro produktový nebo marketingový launch."
category: marketing
status: ready
version: "1.0"
publishedAt: "2026-04-25"
---

# Skill: Launch Checklist

Kompletní launch playbook. Použij ho pro product launch, větší feature release
nebo cokoliv, kolem čeho chceš udělat větší pozornost.

## Kdy použít

- Founder řekne "spouštím [X]" nebo "pojďme připravit launch"
- Launch date už je zapsaný ve shared plans/wiki nebo v aktivním workspace launch file a je do 7 dnů
- Vzniká nový produkt nebo větší feature release

## Jak to funguje

Po triggeru vytvoř launch tracker file v `memory/launch-[name]-[date].md` s
checklistem níže. Položky odškrtávej, jakmile jsou hotové. Progress průběžně
reviduj během standupů a heartbeatů.

---

## Checklist

### Phase 1: Pre-Launch (1-2 týdny před)

**Product Ready**
- [ ] Core feature funguje a je otestovaná
- [ ] Onboarding flow je plynulý (otestuj jako nový user)
- [ ] Pricing page je live a srozumitelná
- [ ] Payment flow funguje end-to-end (otestuj ve Stripe test mode)
- [ ] Transactional emails fungují (welcome, receipt atd.)
- [ ] Error tracking je nastavený a funguje
- [ ] Basic analytics trackují klíčové eventy

**Landing Page**
- [ ] Hero section: jasný value prop v jedné větě
- [ ] Social proof (testimonials, logos, numbers), pokud je dostupný
- [ ] CTA je jasné a above the fold
- [ ] Mobile-responsive
- [ ] Page loads fast (<3s)
- [ ] OG image a meta tags jsou nastavené pro social sharing
- [ ] Otestovaný sharing preview na Twitter/LinkedIn

**Content Prep**
- [ ] Launch blog post drafted
- [ ] Twitter/X launch thread drafted
- [ ] Email pro existing list drafted
- [ ] Product Hunt listing drafted (pokud používáš PH)
  - [ ] Tagline (krátká a úderná)
  - [ ] Description
  - [ ] Screenshots/GIF
  - [ ] Maker comment
  - [ ] First comment ready
- [ ] Hacker News "Show HN" post drafted

**Community & Outreach**
- [ ] Email list má aspoň [X] subscribers
- [ ] Identifikováno 5-10 lidí pro DM v launch day kvůli podpoře
- [ ] Beta users byli na launch upozorněni
- [ ] Připravené odpovědi na běžné otázky

### Phase 2: Launch Day

**Ráno (před spuštěním)**
- [ ] Poslední kontrola: site běží, payments fungují, emails se odesílají
- [ ] Vyčištěný kalendář na celý den
- [ ] Připravená URL blog postu
- [ ] Všechny social posts předem napsané v jednom docu

**Go Live**
- [ ] Product Hunt: submit (ideálně 12:01 AM PT pro celý den)
- [ ] Twitter/X: zveřejnit launch thread
- [ ] Email list: poslat announcement
- [ ] Blog post: publish
- [ ] Hacker News: postnout "Show HN" (pokud dává smysl, ideálně 8-9 AM ET)
- [ ] Indie Hackers: post v relevant groups
- [ ] Reddit: post v relevantních subredditech (podle jejich pravidel)
- [ ] LinkedIn: postnout, pokud tam publikum je

**Během dne**
- [ ] Odpovědět na každý komentář na Product Hunt
- [ ] Odpovědět na každý reply na Twitter/X
- [ ] Odpovědět na HN comments
- [ ] Rychle odpovídat na support emails (first impressions matter)
- [ ] Sdílet updates: "We just hit X upvotes!" nebo "Y signups in first hour!"
- [ ] Poslat DM support listu a požádat je, ať se na to podívají
- [ ] Monitorovat error tracking kvůli launch-day bugs

### Phase 3: Post-Launch (první týden)

**Day 1-2**
- [ ] Poděkovat všem, kdo launch podpořili
- [ ] Napsat "launch results" tweet/post (lidi to milují)
- [ ] Zalogovat skutečné metriky: signups, trials, paying customers, traffic
- [ ] Opravit bugs, které se během launch objevily

**Day 3-7**
- [ ] Follow up s lidmi, kteří se přihlásili, ale neaktivovali se
- [ ] Projít všechen feedback (support emails, comments, DMs)
- [ ] Identifikovat #1 nejčastěji požadované zlepšení
- [ ] Naplánovat další malý update (shipnout do týdne, aby momentum pokračovalo)
- [ ] Zachytit launch results a lessons v shared documents/wiki; `MEMORY.md` aktualizuj jen pokud ho tento workspace používá jako curated overlay
- [ ] Napsat retrospective: co fungovalo, co ne a co příště udělat jinak

**Metrics to Track**
- [ ] Celkové signups v launch day
- [ ] Paying customers z launch
- [ ] Traffic sources (co přivedlo nejvíc signupů?)
- [ ] Product Hunt final rank (pokud relevantní)
- [ ] Email open/click rates
- [ ] Social engagement (likes, retweets, replies)

---

## Tipy

- **Nespouštěj to v pátek.** Chceš pracovní dny kvůli engagementu. Ideální je úterý až čtvrtek.
- **Product Hunt**: Nejvíc trafficu bývá v úterý nebo ve středu. Naplánuj na 12:01 AM PT.
- **Hacker News**: Žádný marketing-speak. Buď upřímný. Ukaž, co jsi postavil a proč. Technické detaily pomáhají.
- **Twitter**: Nejlépe funguje thread. Začni hookem, ukaž produkt, řekni příběh a zakonči CTA.
- **Cíl není virality.** Cíl je získat prvních 10 paying customers. Zaměř se na conversion, ne vanity metrics.
- **Dělej follow up.** Většina výsledků nepřichází z launch itself, ale z následné práce.
