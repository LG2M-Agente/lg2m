import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "../components/Navbar";

export const metadata: Metadata = {
  title: "Cognitio.ia — Agente de apoio para estudo de vestibulares e concursos",
  description: "Plataforma com IA Multiagente, RAG e Heatmap Cognitivo para os vestibulares seriados do Amazonas.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col selection:bg-emerald-500 selection:text-slate-950">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-slate-900 bg-slate-950/60 py-6 text-center text-xs text-slate-500">
          <p>Cognitio.ia • 5.771 Questões Homologadas PSC/UFAM & SIS/UEA</p>
        </footer>
      </body>
    </html>
  );
}
