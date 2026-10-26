import type { Metadata } from "next";
import type { CSSProperties } from "react";
import { Montserrat, Open_Sans } from "next/font/google";
import { spec, BRAND, designTokenStyle } from "../lib/spec";
import "./globals.css";

const montserrat = Montserrat({
  subsets: ["latin", "latin-ext"],
  weight: ["500", "600", "700", "800"],
  variable: "--font-head",
  display: "swap",
});

const openSans = Open_Sans({
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
  display: "swap",
});

export const metadata: Metadata = {
  title: `${spec.lead_magnet_name} | ${BRAND.name}`,
  description: `${spec.lead_magnet_name} — pár minut vyplňování, na konci přehledný výsledek a doporučení na míru.`,
  robots: { index: false, follow: false },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Barvy ze spec.design_tokens jako inline :root na <html> — přebíjí default
  // paletu v globals.css, takže design skutečně teče ze specu (brand roura).
  return (
    <html
      lang="cs"
      className={`${montserrat.variable} ${openSans.variable}`}
      style={designTokenStyle() as CSSProperties}
    >
      <body>{children}</body>
    </html>
  );
}
