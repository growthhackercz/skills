import SalesPage from "./[contactId]/page";
import { BRAND } from "../../lib/spec";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export const metadata = {
  title: `Doporučení na míru | ${BRAND.name}`,
  robots: { index: false, follow: false },
};

/**
 * Čisté `/online` bez ID → generický (nepersonalizovaný) render prodejní
 * stránky. Route `/online/[contactId]` sama `/online` nechytá (bez segmentu),
 * proto tahle explicitní stránka. Renderuje TÝŽ `SalesPage` v generickém
 * režimu (neplatné id → bundle null → personalized=false) — stejně jako
 * `/doporuceni`. (Dřív redirect na `/`, což znamenalo, že čisté /online
 * neukázalo prodejku.)
 */
export default async function OnlineGenericPage() {
  return SalesPage({ params: Promise.resolve({ contactId: "_generic" }) });
}
