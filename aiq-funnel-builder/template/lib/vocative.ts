/**
 * Český vokativ (5. pád) pro oslovení v e-mailech a na stránkách.
 *
 * Strategie:
 *  1. Lookup tabulka nejčastějších českých jmen (mužská i ženská).
 *  2. Koncovková pravidla jako fallback pro jména mimo tabulku.
 *  3. Když si nejsme jistí → vrací null a UI použije „Dobrý den"
 *     (NIKDY nominativ za oslovením).
 */

const TABLE: Record<string, string> = {
  // ---- Mužská jména ----
  adam: "Adame",
  aleš: "Aleši",
  alexandr: "Alexandře",
  alexej: "Alexeji",
  antonín: "Antoníne",
  bedřich: "Bedřichu",
  bohumil: "Bohumile",
  bohuslav: "Bohuslave",
  břetislav: "Břetislave",
  ctirad: "Ctirade",
  čestmír: "Čestmíre",
  dalibor: "Dalibore",
  daniel: "Danieli",
  david: "Davide",
  denis: "Denisi",
  dominik: "Dominiku",
  dušan: "Dušane",
  eduard: "Eduarde",
  emil: "Emile",
  erik: "Eriku",
  filip: "Filipe",
  františek: "Františku",
  gabriel: "Gabrieli",
  hynek: "Hynku",
  igor: "Igore",
  ivan: "Ivane",
  ivo: "Ivo",
  jakub: "Jakube",
  jan: "Jane",
  jaromír: "Jaromíre",
  jaroslav: "Jaroslave",
  jindřich: "Jindřichu",
  jiří: "Jiří",
  josef: "Josefe",
  kamil: "Kamile",
  karel: "Karle",
  kryštof: "Kryštofe",
  ladislav: "Ladislave",
  leoš: "Leoši",
  libor: "Libore",
  lubomír: "Lubomíre",
  luboš: "Luboši",
  luděk: "Luďku",
  lukáš: "Lukáši",
  marcel: "Marceli",
  marek: "Marku",
  marian: "Mariane",
  martin: "Martine",
  matěj: "Matěji",
  matouš: "Matouši",
  matyáš: "Matyáši",
  maxim: "Maxime",
  michal: "Michale",
  milan: "Milane",
  miloslav: "Miloslave",
  miloš: "Miloši",
  miroslav: "Miroslave",
  mojmír: "Mojmíre",
  nikolas: "Nikolasi",
  norbert: "Norberte",
  oldřich: "Oldřichu",
  oliver: "Olivere",
  ondřej: "Ondřeji",
  oskar: "Oskare",
  otakar: "Otakare",
  oto: "Oto",
  patrik: "Patriku",
  pavel: "Pavle",
  petr: "Petře",
  přemysl: "Přemysle",
  radek: "Radku",
  radim: "Radime",
  radomír: "Radomíre",
  radovan: "Radovane",
  rené: "René",
  richard: "Richarde",
  robert: "Roberte",
  robin: "Robine",
  roman: "Romane",
  rostislav: "Rostislave",
  rudolf: "Rudolfe",
  samuel: "Samueli",
  sebastian: "Sebastiane",
  stanislav: "Stanislave",
  svatopluk: "Svatopluku",
  šimon: "Šimone",
  štefan: "Štefane",
  štěpán: "Štěpáne",
  tadeáš: "Tadeáši",
  teodor: "Teodore",
  tobiáš: "Tobiáši",
  tomáš: "Tomáši",
  václav: "Václave",
  vasil: "Vasile",
  viktor: "Viktore",
  vilém: "Viléme",
  vít: "Víte",
  vítězslav: "Vítězslave",
  vladan: "Vladane",
  vladimír: "Vladimíre",
  vladislav: "Vladislave",
  vlastimil: "Vlastimile",
  vojtěch: "Vojtěchu",
  vratislav: "Vratislave",
  zbyněk: "Zbyňku",
  zdeněk: "Zdeňku",
  // Domácké podoby, které lidé běžně vyplňují
  honza: "Honzo",
  jirka: "Jirko",
  kuba: "Kubo",
  láďa: "Láďo",
  míra: "Míro",
  ondra: "Ondro",
  pepa: "Pepo",
  standa: "Stando",
  tonda: "Tondo",
  vašek: "Vašku",

  // ---- Ženská jména ----
  adéla: "Adélo",
  alena: "Aleno",
  alice: "Alice",
  alžběta: "Alžběto",
  andrea: "Andreo",
  aneta: "Aneto",
  anežka: "Anežko",
  anna: "Anno",
  barbora: "Barboro",
  blanka: "Blanko",
  bohumila: "Bohumilo",
  božena: "Boženo",
  dagmar: "Dagmar",
  dana: "Dano",
  daniela: "Danielo",
  denisa: "Deniso",
  diana: "Diano",
  dominika: "Dominiko",
  drahomíra: "Drahomíro",
  eliška: "Eliško",
  ema: "Emo",
  emilie: "Emilie",
  erika: "Eriko",
  eva: "Evo",
  gabriela: "Gabrielo",
  hana: "Hano",
  helena: "Heleno",
  irena: "Ireno",
  iva: "Ivo",
  ivana: "Ivano",
  iveta: "Iveto",
  jana: "Jano",
  jarmila: "Jarmilo",
  jaroslava: "Jaroslavo",
  jitka: "Jitko",
  jiřina: "Jiřino",
  julie: "Julie",
  kamila: "Kamilo",
  karolína: "Karolíno",
  kateřina: "Kateřino",
  klára: "Kláro",
  kristýna: "Kristýno",
  květa: "Květo",
  lada: "Lado",
  laura: "Lauro",
  lenka: "Lenko",
  libuše: "Libuše",
  lucie: "Lucie",
  ludmila: "Ludmilo",
  magdaléna: "Magdaléno",
  marcela: "Marcelo",
  marie: "Marie",
  markéta: "Markéto",
  marta: "Marto",
  martina: "Martino",
  michaela: "Michaelo",
  milada: "Milado",
  milena: "Mileno",
  miroslava: "Miroslavo",
  monika: "Moniko",
  naděžda: "Naděždo",
  natálie: "Natálie",
  nela: "Nelo",
  nikola: "Nikolo",
  olga: "Olgo",
  pavla: "Pavlo",
  pavlína: "Pavlíno",
  petra: "Petro",
  radka: "Radko",
  renáta: "Renáto",
  romana: "Romano",
  růžena: "Růženo",
  sabina: "Sabino",
  simona: "Simono",
  sofie: "Sofie",
  soňa: "Soňo",
  stanislava: "Stanislavo",
  šárka: "Šárko",
  tereza: "Terezo",
  vendula: "Vendulo",
  veronika: "Veroniko",
  věra: "Věro",
  vlasta: "Vlasto",
  vladimíra: "Vladimíro",
  zdeňka: "Zdeňko",
  zuzana: "Zuzano",
  žaneta: "Žaneto",
};

const VOWEL_ENDINGS = ["e", "é", "i", "í", "y", "ý", "o", "ó", "u", "ů"];
const SOFT_CONSONANTS = ["š", "č", "ř", "ž", "j", "c", "ť", "ď", "ň"];
const HARD_PLUS_E = ["b", "d", "f", "m", "n", "p", "t", "v", "w"];
const VOWELS = "aáeéěiíoóuúůyý";

/**
 * Vrátí vokativ křestního jména, nebo null když si nejsme jistí.
 * Volající při null použije neutrální „Dobrý den".
 */
export function vocative(firstName: string | undefined | null): string | null {
  if (!firstName) return null;
  const raw = firstName.trim().split(/\s+/)[0] ?? "";
  if (!raw) return null;
  // Jen písmena (včetně diakritiky) — jinak si nejsme jistí.
  if (!/^[A-Za-zÁ-Žá-ž]+$/u.test(raw)) return null;

  const lower = raw.toLocaleLowerCase("cs");
  const hit = TABLE[lower];
  if (hit) return hit;

  // ---- Koncovková pravidla (fallback) ----
  const last = lower.slice(-1);
  const beforeLast = lower.slice(-2, -1);

  // Jména na -a (ženská i mužská domácká): -a → -o (Jana→Jano, Ota→Oto)
  if (last === "a") return raw.slice(0, -1) + "o";

  // Jména končící samohláskou (Lucie, Jiří, René, Ivo…) — beze změny.
  if (VOWEL_ENDINGS.includes(last) || last === "ě") return raw;

  // -ek → -ku (Marek→Marku, Radek→Radku)
  if (lower.endsWith("ek") && lower.length > 3) return raw.slice(0, -2) + "ku";

  // Měkké souhlásky → +i (Tomáš→Tomáši, Ondřej→Ondřeji)
  if (SOFT_CONSONANTS.includes(last)) return raw + "i";

  // ch/h/g/k → +u (Jindřich→Jindřichu, Dominik→Dominiku)
  if (lower.endsWith("ch") || last === "h" || last === "g" || last === "k") {
    return raw + "u";
  }

  // -r po souhlásce → -ře (Petr→Petře); po samohlásce → +e (Libor→Libore)
  if (last === "r") {
    if (beforeLast && !VOWELS.includes(beforeLast)) return raw.slice(0, -1) + "ře";
    return raw + "e";
  }

  // Tvrdé souhlásky → +e (Jakub→Jakube, Martin→Martine, David→Davide)
  if (HARD_PLUS_E.includes(last)) return raw + "e";

  // -l, -s, -z, -x a další nejasné případy → nejisté → null.
  return null;
}
