"use client";

import React, { useState, useEffect } from "react";
import {
  User,
  Settings,
  Brain,
  GraduationCap,
  Save,
  CheckCircle2,
  Sparkles,
  BookMarked
} from "lucide-react";
import { fetchStudentProfile, updateStudentProfile } from "../../lib/api";
import { StudentProfile } from "../../lib/types";

export default function PerfilPage() {
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [certameFoco, setCertameFoco] = useState("PSC");
  const [estiloDidatico, setEstiloDidatico] = useState("DIRETO");
  const [cursoPretendido, setCursoPretendido] = useState("Engenharia de Software");
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    fetchStudentProfile()
      .then((p) => {
        setProfile(p);
        setCertameFoco(p.certame_foco);
        setEstiloDidatico(p.estilo_didatico_padrao);
      })
      .catch((e) => console.error("Erro ao carregar perfil", e));
  }, []);

  const handleSalvarPreferencias = async () => {
    setSaving(true);
    setSavedSuccess(false);
    try {
      const updated = await updateStudentProfile(certameFoco, estiloDidatico);
      setProfile(updated);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (e) {
      console.error("Erro ao salvar", e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white flex items-center gap-3">
          <Settings className="w-7 h-7 text-blue-400" />
          <span>Perfil & Preferências Cognitivas</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Ajuste as diretrizes de aprendizagem do sistema para que a IA adapte a linguagem e a dificuldade.
        </p>
      </div>

      {/* Cartão de Identificação */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 flex flex-col sm:flex-row items-center gap-5">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 to-emerald-500 flex items-center justify-center text-white text-xl font-black shadow-lg shadow-blue-500/20 shrink-0">
          {profile?.nome ? profile.nome[0] : "L"}
        </div>
        <div className="flex-1 text-center sm:text-left">
          <h2 className="text-lg font-bold text-white">{profile?.nome || "Lucas Eduardo"}</h2>
          <p className="text-xs text-slate-400">{profile?.email || "estudante.demo@lg2m.edu.br"}</p>
          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 mt-2">
            <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-blue-600/20 border border-blue-500/30 text-blue-300 font-semibold">
              Plano Hackathon AKCIT
            </span>
            <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold">
              {profile?.total_tentativas || 0} questões respondidas
            </span>
          </div>
        </div>
      </div>

      {/* Formulário de Calibração */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
        {/* Certame Foco */}
        <div>
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-2">
            Vestibular Seriado de Foco Prioritário
          </label>
          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setCertameFoco("PSC")}
              className={`p-4 rounded-xl border text-left transition-all ${
                certameFoco === "PSC"
                  ? "bg-blue-600/15 border-blue-500 shadow-sm"
                  : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="font-bold text-sm text-blue-400">PSC (UFAM)</div>
              <p className="text-xs text-slate-400 mt-1">
                Foco no Processo Seletivo Contínuo da Universidade Federal do Amazonas.
              </p>
            </button>

            <button
              type="button"
              onClick={() => setCertameFoco("SIS")}
              className={`p-4 rounded-xl border text-left transition-all ${
                certameFoco === "SIS"
                  ? "bg-emerald-600/15 border-emerald-500 shadow-sm"
                  : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="font-bold text-sm text-emerald-400">SIS (UEA)</div>
              <p className="text-xs text-slate-400 mt-1">
                Foco no Sistema de Ingresso Seriado da Universidade do Estado do Amazonas.
              </p>
            </button>
          </div>
        </div>

        {/* Estilo Didático Padrão */}
        <div>
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-2">
            Estilo Didático Preferido do Mentor IA
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              {
                id: "DIRETO",
                title: "⚡ Direto & Objetivo",
                desc: "Explica a pegadinha e a resposta imediatamente sem rodeios.",
              },
              {
                id: "SOCRATICO",
                title: "🤔 Socrático (Guiado)",
                desc: "Faz perguntas norteadoras para estimular seu próprio raciocínio.",
              },
              {
                id: "TEORICO",
                title: "📚 Teórico Formal",
                desc: "Aprofunda com axiomas, demonstrações e rigor conceitual.",
              },
            ].map((estilo) => (
              <button
                key={estilo.id}
                type="button"
                onClick={() => setEstiloDidatico(estilo.id)}
                className={`p-4 rounded-xl border text-left transition-all ${
                  estiloDidatico === estilo.id
                    ? "bg-blue-600/15 border-blue-500 shadow-sm"
                    : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
                }`}
              >
                <div className="font-bold text-xs text-slate-200">{estilo.title}</div>
                <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{estilo.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Curso Alvo */}
        <div>
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-2">
            Curso Pretendido na UFAM / UEA
          </label>
          <input
            type="text"
            value={cursoPretendido}
            onChange={(e) => setCursoPretendido(e.target.value)}
            className="w-full bg-slate-950/80 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Botão Salvar */}
        <div className="pt-2 flex items-center justify-between">
          <div>
            {savedSuccess && (
              <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" /> Preferências salvas com sucesso!
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={handleSalvarPreferencias}
            disabled={saving}
            className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white font-semibold text-xs flex items-center gap-2 transition-all shadow-md shadow-blue-500/20"
          >
            {saving ? (
              <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <Save className="w-3.5 h-3.5" />
                <span>Salvar Alterações</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Dossiê Cognitivo Vivo (Memória do Profiler Agent) */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-white font-bold text-base">
            <Brain className="w-5 h-5 text-emerald-400" />
            <span>Dossiê Cognitivo & Memória Evolutiva (Profiler Agent)</span>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Versão {profile?.versao_perfil || 1}
          </span>
        </div>
        <p className="text-xs text-slate-400">
          Este dossiê reflete a memória epistêmica de longo prazo que o Agente Profiler atualiza a cada bateria de questões respondidas.
        </p>
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 text-slate-300 font-mono text-xs whitespace-pre-wrap leading-relaxed max-h-80 overflow-y-auto">
          {profile?.dossie_cognitivo_markdown || (
            "Dossiê em fase de calibração inicial. Responda a questões ou simulados para que o Profiler registre seus padrões cognitivos."
          )}
        </div>
      </div>
    </div>
  );
}
