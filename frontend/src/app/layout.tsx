// CS50 AI assistance citation: OpenAI ChatGPT and OpenAI Codex were used as
// development assistants across the LifeBoard frontend for architecture discussion,
// implementation suggestions, debugging, tests, review, and documentation. All
// accepted changes were reviewed and validated by the project author.

import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "LifeBoard",
  description: "Seu quadro semanal compartilhado.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
