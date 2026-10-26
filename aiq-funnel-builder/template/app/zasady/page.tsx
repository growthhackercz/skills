import Link from "next/link";
import { spec, BRAND } from "../../lib/spec";

export const metadata = {
  title: `Zásady zpracování osobních údajů | ${BRAND.name}`,
  robots: { index: false, follow: false },
};

/**
 * Zásady zpracování OÚ — texty se skládají ze spec.brand (správce, kontakt)
 * a spec.lead_magnet_name. Builder při nasazení ověří, že spec.brand
 * obsahuje skutečné údaje klienta (deploy checklist).
 */
export default function ZasadyPage() {
  const privacyMail = BRAND.privacy_email;

  return (
    <div className="result-shell">
      <div className="result-card">
        <span className="eyebrow">
          {spec.lead_magnet_name} · {BRAND.name}
        </span>
        <h1>Zásady zpracování osobních údajů</h1>

        <h2 style={{ fontSize: 20 }}>Kdo je správcem vašich údajů</h2>
        <p>
          Správcem osobních údajů je <strong>{BRAND.name}</strong>.
          {privacyMail ? (
            <>
              {" "}
              Kontaktní e-mail pro záležitosti osobních údajů:{" "}
              <a href={`mailto:${privacyMail}`}>{privacyMail}</a>.
            </>
          ) : null}
        </p>

        <h2 style={{ fontSize: 20 }}>Jaké údaje zpracováváme a proč</h2>
        <p>
          Zpracováváme údaje, které vyplníte v dotazníku „
          {spec.lead_magnet_name}“: jméno, příjmení, e-mail, telefon (pokud
          jej uvedete) a vaše odpovědi na otázky. Pokud v odpovědích uvedete i
          citlivé údaje (například o zdraví), zpracováváme je výhradně na
          základě vašeho výslovného souhlasu.
        </p>
        <p>
          Účel zpracování: vytvoření personalizovaného vyhodnocení a
          doporučení na míru, zaslání výsledku e-mailem a případné osobní
          poradenství, pokud o něj projevíte zájem.
        </p>

        <h2 style={{ fontSize: 20 }}>Kdo nám se zpracováním pomáhá</h2>
        <p>Vaše údaje zpracovávají tito zpracovatelé:</p>
        <ul>
          <li>
            <strong>GoHighLevel</strong> — systém pro správu kontaktů a
            odesílání e-mailů,
          </li>
          <li>
            <strong>Netlify</strong> — hosting této webové aplikace,
          </li>
          <li>
            <strong>OpenRouter (LLM)</strong> — automatizované zpracování
            vašich odpovědí pro přípravu personalizovaného vyhodnocení.
          </li>
        </ul>

        <h2 style={{ fontSize: 20 }}>Jak dlouho údaje uchováváme</h2>
        <p>
          Údaje uchováváme po dobu {spec.retention_months ?? 24} měsíců od vaší
          poslední aktivity, nebo do odvolání souhlasu, podle toho, co nastane
          dříve.
        </p>

        <h2 style={{ fontSize: 20 }}>Vaše práva</h2>
        <p>
          Máte právo na přístup ke svým údajům, jejich opravu či výmaz,
          omezení zpracování, přenositelnost a právo souhlas kdykoli odvolat
          (odvoláním není dotčena zákonnost zpracování před odvoláním). Máte
          také právo podat stížnost u Úřadu pro ochranu osobních údajů.
        </p>
        {privacyMail ? (
          <p>
            Pro uplatnění práv nebo jakýkoli dotaz nás kontaktujte na{" "}
            <a href={`mailto:${privacyMail}`}>{privacyMail}</a>.
          </p>
        ) : null}

        <Link href="/" className="btn btn-ghost" style={{ marginTop: 12 }}>
          Zpět na úvodní stránku
        </Link>
      </div>
    </div>
  );
}
