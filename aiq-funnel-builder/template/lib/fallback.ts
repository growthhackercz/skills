import { spec, Temperature } from "./spec";

/**
 * Statické fallback texty — použijí se, když LLM generace selže
 * (i po retry) nebo když persona pole v GHL zatím nejsou naplněná.
 *
 * GENERICKÁ verze (v0.5): texty se skládají ze spec (produkt, název magnetu,
 * garance) — ŽÁDNÉ funnel-specific formulace natvrdo. Díky tomu je soubor
 * součástí sdíleného template a funguje pro libovolný funnel/produkt.
 *
 * Pravidla: vykání, klidný poradenský tón, žádné URL (linky vkládá kód),
 * žádná čísla/ceny/garance mimo spec.offer, žádné zdravotní sliby.
 */

export interface FallbackEmail {
  id: string;
  subject: string;
  body_html: string;
}

const PRODUCT = spec.offer.product;
const GUARANTEE = spec.offer.guarantee;
// Pozn.: název magnetu se do fallback textů ZÁMĚRNĚ nevkládá doprostřed vět —
// otázkové názvy („Test: Jak dobře…?") by češtinu rozbily. Když ho někde chceš
// zmínit, dej ho v uvozovkách jako celek na okraj věty, ne dovnitř.

/* ---------- Persona pole (obecná, ale slušná) ---------- */

export const FALLBACK_PERSONA: Record<string, string> = {
  main_headline: `doporučení připravené podle Vašich odpovědí`,
  magnet_headline: `Vaše analýza na míru`,
  sub_headline: `Připravili jsme přehled na míru Vaší situaci, který vychází přímo z Vašich odpovědí.`,
  // Párovací metadata — prázdné: render spáruje citace podle pořadí.
  problem1_source: "",
  problem2_source: "",
  problem3_source: "",
  problem4_source: "",
  problem5_source: "",

  // problem4/5 (diagnostické yes/no) jsou volitelné — ve fallbacku prázdné,
  // render kartu bez dopadu jen s verbatim odpovědí (nikdy vata navíc).
  problem4_question: "",
  problem4_impact: "",
  problem5_question: "",
  problem5_impact: "",

  problem1_question: "Vaše situace má konkrétní rezervy",
  problem1_impact:
    "Z Vašich odpovědí vyplývá, že současný stav není takový, jaký byste si přáli. Čím déle to trvá, tím víc se to sčítá.",
  problem2_question: "Dosavadní řešení nestačí",
  problem2_impact:
    "To, co jste zatím zkoušeli, funguje jen nárazově. Bez pravidelného přístupu se situace rychle vrací.",
  problem3_question: "Chybí přehled a systém",
  problem3_impact:
    "Rozhodujete se podle pocitu, ne podle jasného plánu. Srozumitelný postup šetří čas i peníze a dává výsledkům šanci.",

  benefit_1_title: "Pravidelný přístup místo nárazových pokusů",
  benefit_1_description: `${PRODUCT} pracuje pravidelně, ne až když si na problém vzpomenete.`,
  benefit_2_title: "Přehled o tom, co se děje",
  benefit_2_description:
    "Postupujete podle jasného režimu a změny sledujete průběžně. Víte, co děláte a proč.",
  benefit_3_title: "Řešení, které vydrží",
  benefit_3_description: `${PRODUCT} slouží dlouhodobě: jedna investice, ze které máte užitek opakovaně.`,

  objection_1_title: "Bude to fungovat právě u nás?",
  objection_1_response: `${GUARANTEE} Nejdřív si v klidu ověříme, jestli řešení dává smysl právě pro Vaši situaci.`,
  objection_2_title: "Musím se rozhodnout hned?",
  objection_2_response:
    "Ne. Doporučení máte k dispozici a rozhodnout se můžete, až budete připraveni. Poradenství je nezávazné.",

  magnet_rozbor:
    "Vaše odpovědi ukazují konkrétní situaci s jasnými prioritami. Kombinace toho, co Vás trápí nejvíc, jak dlouho to trvá a co jste už zkoušeli, napovídá, kde má pravidelný přístup největší šanci pomoci.\n\nJe to běžná situace. Většina lidí řeší věci nárazově, když je problém nejvíc vidět, ale právě pravidelnost dělá rozdíl.",
  magnet_dobre:
    "Už jen to, že jste si udělali čas na vyplnění, znamená, že svou situaci vnímáte a řešíte. To je nejdůležitější první krok.\n\nZ Vašich odpovědí je vidět, že o situaci přemýšlíte. Víte, co Vás trápí a kde by zlepšení pomohlo nejvíc.",
  magnet_rizika:
    "Hlavní rezervou je nepravidelnost. Situace se řeší jen tehdy, když se připomene sama, a mezi tím se postupně vrací a sčítá.\n\nDruhou rezervou je chybějící systém: bez jasného postupu se rozhodujete podle pocitu a výsledky se pak těžko vyhodnocují.",
  magnet_akce:
    "1. Stanovte si jednu prioritu. Řešit všechno najednou nefunguje, vyberte oblast s největším dopadem.\n2. Nastavte si pravidelnost. Krátce a pravidelně funguje lépe než dlouho a nárazově.\n3. Sledujte změny. Poznamenejte si výchozí stav, ať za dva týdny vidíte posun.\n4. Odstraňte, co prokazatelně nefunguje. Šetří to čas, peníze i motivaci.\n5. Kdykoli si nejste jistí, poraďte se. Nezávazná konzultace je rychlejší než měsíce zkoušení.",
  predpis_config:
    "Pro Vaši situaci existuje konkrétní doporučená konfigurace. Sestavili jsme ji z Vašich odpovědí a najdete ji ve svém doporučení na míru.",
  // Punch list je čistě per-lead (konstatování jeho ANO/NE) — bez AI nemá smysl,
  // sekce se prostě skryje. Prázdný fallback (render filtruje prázdné).
  magnet_problem_list: "",
  // Fáze 4 Shrnutí — per-lead (jeho problémy/cíle/pointa). Bez AI se sekce skryje.
  souhrn_ted: "",
  souhrn_chci: "",
  pointa: "",
  // Fáze 5 urgence — per-lead (proč teď, z Product DNA). Bez AI se blok skryje.
  nalehavost: "",
  // Fáze 5 obraz „potom" — per-lead (future pacing, emoční vrchol). Bez AI skryto.
  obraz_potom: "",
  // Fáze 3 flexibilní STŘED (render `cards`) — per-lead. Bez AI se blok skryje.
  magnet_prostor: "",
};

/* ---------- Fallback e-maily per větev ---------- */

const HOT_EMAILS: FallbackEmail[] = [
  {
    id: "E1",
    subject: "Vaše doporučení na míru je připravené",
    body_html: `<p>Vaše odpovědi ukázaly, že situace si zaslouží pozornost, a dokonce že na ni existuje konkrétní řešení.</p><p>Připravili jsme pro Vás doporučení na míru: co Vaše odpovědi říkají, kde je největší rezerva a jaká konfigurace k Vám sedí. Najdete ho pod tlačítkem níže.</p>`,
  },
  {
    id: "E2",
    subject: "Jak to řeší lidé v podobné situaci",
    body_html: `<p>lidé v podobné situaci si nejčastěji kladou stejnou otázku: opravdu to pomůže právě u nás?</p><p>Proto stavíme na pravidelném přístupu a jasném režimu. Vidíte, co děláte a proč. A pokud si nejste jistí, nejdřív to spolu v klidu probereme.</p>`,
  },
  {
    id: "E3",
    subject: "Poslední krok je na Vás",
    body_html: `<p>Vaše doporučení na míru je stále připravené. Nechceme na Vás tlačit, jen připomínáme, že rezervy, které se ukázaly, se samy nevyřeší.</p><p>Pokud chcete, podíváme se na to spolu. ${GUARANTEE}</p>`,
  },
];

const WARM_EMAILS: FallbackEmail[] = [
  {
    id: "E1",
    subject: "Praktický tip k Vašemu výsledku",
    body_html: `<p>děkujeme za vyplnění. Než se pustíte do velkých změn, jeden praktický tip: největší rozdíl dělá pravidelnost. Krátce a pravidelně funguje lépe než dlouho a nárazově.</p><p>V kompletní analýze najdete další kroky sestavené podle Vašich odpovědí.</p>`,
  },
  {
    id: "E2",
    subject: "Co Váš výsledek ukázal a co s tím",
    body_html: `<p>Vaše odpovědi ukázaly několik konkrétních rezerv, které se dají řešit. Připravili jsme pro Vás doporučení na míru: co dělat hned a kde dává smysl systematický přístup.</p><p>Celé doporučení najdete pod tlačítkem níže.</p>`,
  },
  {
    id: "E3",
    subject: "Jak to vyřešili lidé v podobné situaci",
    body_html: `<p>lidé s podobnou situací nejčastěji ocení dvě věci: že řešení funguje pravidelně samo a že mají jasný přehled o postupu.</p><p>Není to o velkém rozhodnutí ze dne na den. Je to o tom, přestat zkoušet naslepo a začít postupovat podle plánu.</p>`,
  },
  {
    id: "E4",
    subject: "Nejčastější obavy a jak to je doopravdy",
    body_html: `<p>možná si říkáte, jestli se to vyplatí a jestli se musíte rozhodnout hned. Krátce: rozhodovat se nemusíte vůbec rychle.</p><p>${GUARANTEE}</p>`,
  },
  {
    id: "E5",
    subject: "Shrnutí Vašeho výsledku na jednom místě",
    body_html: `<p>krátké shrnutí: Váš výsledek ukázal konkrétní rezervy, připravili jsme doporučení na míru a kroky, které můžete udělat hned, i bez nákupu.</p><p>Vše najdete pod tlačítkem níže. Kdybyste chtěli cokoli probrat osobně, stačí odpovědět na tento e-mail. Jsme tu pro Vás.</p>`,
  },
];

const COLD_EMAILS: FallbackEmail[] = [
  {
    id: "E1",
    subject: "Malý tip k Vašemu výsledku",
    body_html: `<p>děkujeme za vyplnění. Vaše situace vypadá dobře, přesto jeden tip, který se hodí každému: pravidelnost dělá větší rozdíl než intenzita. Krátce a často funguje lépe než hodně a nárazově.</p>`,
  },
  {
    id: "E2",
    subject: `Kdy má ${PRODUCT} smysl`,
    body_html: `<p>${PRODUCT} není pro každého. Největší přínos má tam, kde se situace opakuje nebo dlouhodobě omezuje běžný den.</p><p>Pokud se u Vás něco z toho časem změní, máte v analýze přehled, podle čeho to poznat.</p>`,
  },
  {
    id: "E3",
    subject: "Kdybyste cokoli potřebovali, jsme tu",
    body_html: `<p>tímto naši sérii uzavíráme. Vaše analýza zůstává dostupná pod tlačítkem níže, kdykoli se k ní můžete vrátit.</p><p>A kdybyste si někdy chtěli svou situaci probrat osobně, stačí odpovědět na tento e-mail. Bez tlaku, jen poradenství.</p>`,
  },
];

export const FALLBACK_EMAILS: Record<Temperature, FallbackEmail[]> = {
  hot: HOT_EMAILS,
  warm: WARM_EMAILS,
  cold: COLD_EMAILS,
};

/** Fallback subject pro e-mail dané větve a id (E1…E5). */
export function fallbackEmail(temp: Temperature, id: string): FallbackEmail {
  const list = FALLBACK_EMAILS[temp] ?? FALLBACK_EMAILS.warm;
  return (
    list.find((e) => e.id === id) ?? {
      id,
      subject: `Vaše personalizovaná analýza, ${PRODUCT}`,
      body_html:
        "<p>Vaše personalizovaná analýza je připravená. Najdete ji pod tlačítkem níže.</p>",
    }
  );
}

/**
 * Neutrální fallback pro persona pole, které nemá vlastní záznam ve
 * FALLBACK_PERSONA (typicky nové/custom magnet_* pole přidané strategií).
 * Prázdný string by odpovídající magnet sekci při výpadku LLM navždy skryl.
 */
const GENERIC_PERSONA_FALLBACK =
  "Tato část se připravuje na základě Vašich odpovědí.";

/**
 * Doplní chybějící/prázdná persona pole fallback hodnotami.
 * Použití: render /online/ a /magnet/ dřív, než doběhne personalizace.
 */
export function withPersonaFallback(
  stored: Record<string, string>
): Record<string, string> {
  const out: Record<string, string> = {};
  for (const name of spec.persona_fields) {
    const v = (stored[name] ?? "").trim();
    if (v) {
      out[name] = v;
      continue;
    }
    const fb = FALLBACK_PERSONA[name];
    if (fb) {
      out[name] = fb;
      continue;
    }
    // Pole bez statického fallbacku: dej generický text (ne prázdný string),
    // ať sekce nezmizí bez stopy, a zaloguj to.
    console.warn(
      `[fallback] persona pole "${name}" nemá záznam ve FALLBACK_PERSONA — používám generický text.`
    );
    out[name] = GENERIC_PERSONA_FALLBACK;
  }
  return out;
}
