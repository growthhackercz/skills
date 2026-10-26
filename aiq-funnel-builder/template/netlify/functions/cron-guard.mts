// Netlify SCHEDULED function — běží @hourly, spouští ho Netlify (ne server).
// Rozvrh se registruje při deployi z `config` níže; v Netlify UI se objeví
// v Functions se štítkem „Scheduled". Per-web: každý funnel má svůj vlastní cron
// scoped na svoje namespacnuté tagy (`[prefix] - converted` / `[prefix] - active`, lowercase).
//
// Guard: `converted` (klient přidal) → zruš zbývající naplánované e-maily +
// sundej `active`; `active` s prošlým Sequence End → přirozený konec → `completed`.
import { runGuard } from "../../lib/guard-core";

const handler = async () => {
  const result = await runGuard();
  return new Response(JSON.stringify(result), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
};

export default handler;
export const config = { schedule: "@hourly" };
