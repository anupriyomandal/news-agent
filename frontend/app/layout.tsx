import type { Metadata } from "next";
import { Inter, Playfair_Display, Source_Serif_4 } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-ui" });
const playfair = Playfair_Display({ subsets: ["latin"], variable: "--font-headline" });
const sourceSerif = Source_Serif_4({ subsets: ["latin"], variable: "--font-body" });

export const metadata: Metadata = {
  title: "Anupriyo Mandal's News Intelligence Engine",
  description: "Analytical, fact-driven reactive news synthesis",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${playfair.variable} ${sourceSerif.variable}`}>
      <body>{children}</body>
    </html>
  );
}
