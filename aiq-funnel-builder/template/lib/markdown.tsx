import React from "react";

/**
 * Micro-markdown → React. BEZPEČNÁ náhrada HTML v AI polích (P2-4): žádný
 * `dangerouslySetInnerHTML`, žádný sanitizer, nulová injection plocha. Podporuje
 * jen podmnožinu, kterou prompt povoluje:
 *   - odstavce oddělené prázdným řádkem (\n\n)
 *   - `**tučně**` (inline)
 *   - řádky začínající `- ` nebo `1. ` → seznam
 *   - očíslované kroky „1. …" (magnet_akce)
 * Vše ostatní se renderuje jako plain text (escapováno Reactem automaticky).
 */

/** Rozseká inline text na React fragmenty a přeloží `**tučně**`. */
function renderInline(text: string, keyBase: string): React.ReactNode[] {
  const out: React.ReactNode[] = [];
  const re = /\*\*([^*]+)\*\*/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(text.slice(last, m.index));
    out.push(<strong key={`${keyBase}-b${i++}`}>{m[1]}</strong>);
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

type Block =
  | { kind: "p"; lines: string[] }
  | { kind: "ul"; items: string[] }
  | { kind: "ol"; items: string[] };

/** Seskupí řádky do bloků (odstavce / odrážky / číslované). */
function toBlocks(src: string): Block[] {
  const blocks: Block[] = [];
  const paras = src.replace(/\r\n/g, "\n").split(/\n{2,}/);
  for (const para of paras) {
    const lines = para.split("\n").map((l) => l.trim()).filter(Boolean);
    if (lines.length === 0) continue;
    if (lines.every((l) => /^-\s+/.test(l))) {
      blocks.push({ kind: "ul", items: lines.map((l) => l.replace(/^-\s+/, "")) });
    } else if (lines.every((l) => /^\d+[.)]\s+/.test(l))) {
      blocks.push({ kind: "ol", items: lines.map((l) => l.replace(/^\d+[.)]\s+/, "")) });
    } else {
      blocks.push({ kind: "p", lines });
    }
  }
  return blocks;
}

/**
 * Renderuje micro-markdown text jako React elementy. Pole `className` se přidá na
 * kořenový wrapper.
 */
export function Markdown({
  text,
  className,
}: {
  text: string;
  className?: string;
}) {
  const blocks = toBlocks(text ?? "");
  return (
    <div className={className}>
      {blocks.map((b, i) => {
        if (b.kind === "ul") {
          return (
            <ul key={i} className="md-list">
              {b.items.map((it, j) => (
                <li key={j}>{renderInline(it, `u${i}-${j}`)}</li>
              ))}
            </ul>
          );
        }
        if (b.kind === "ol") {
          return (
            <ol key={i} className="md-list md-list-ol">
              {b.items.map((it, j) => (
                <li key={j}>{renderInline(it, `o${i}-${j}`)}</li>
              ))}
            </ol>
          );
        }
        return (
          <p key={i}>
            {b.lines.map((ln, j) => (
              <React.Fragment key={j}>
                {j > 0 && <br />}
                {renderInline(ln, `p${i}-${j}`)}
              </React.Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
}
