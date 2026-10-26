import SalesPage from "../online/[contactId]/page";
import { BRAND } from "../../lib/spec";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export const metadata = {
  title: `Doporučení | ${BRAND.name}`,
  robots: { index: false, follow: false },
};

/**
 * Generická prodejní stránka (návštěva bez kontaktního ID). Renderuje TÝŽ nový
 * render jako `/online/[contactId]` v generickém režimu — neplatné id → bundle
 * null → `personalized = false`. Žádný samostatný (zastaralý) GenericSales.
 */
export default async function DoporuceniPage() {
  return SalesPage({ params: Promise.resolve({ contactId: "_generic" }) });
}
