"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  AlertTriangle,
  Clock,
  Target,
  ArrowRight,
  BookOpen,
  BrainCircuit,
  CheckCircle2,
  Flame,
  Award
} from "lucide-react";
import { fetchStudentProfile, fetchStudentHeatmap } from "../lib/api";
import { StudentProfile, HeatmapItem } from "../lib/types";

export default function DashboardPage() {
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapItem[]>([]);
  const [pontosCegos, setPontosCegos] = useState<HeatmapItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchStudentProfile(), fetchStudentHeatmap()])
      .then(([p, h]) => {
        setProfile(p);
        setHeatmap(h.heatmap);
        setPontosCegos(h.pontos_cegos);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Erro ao carregar dados do dashboard", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin" />
        <p className="text-slate-400 text-sm">Carregando perfil e matriz cognitiva...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Top Banner / Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-950/70 via-slate-900 to-emerald-950/50 border border-slate-800 p-6 md:p-8">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-semibold mb-3">
              <BrainCircuit className="w-3.5 h-3.5" />
              <span>Mentor IA Ativo no modo {profile?.estilo_didatico_padrao || "DIRETO"}</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Olá, {profile?.nome || "Estudante"}! 👋
            </h1>
            <p className="text-slate-300 text-sm md:text-base mt-1 max-w-2xl">
              Foco atual no vestibular seriado <span className="text-blue-400 font-bold">{profile?.certame_foco}</span>.
              O ecossistema calibrou seu plano de estudos com base em 5.771 questões históricas da UFAM e UEA.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/questoes"
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 text-white font-medium text-sm transition-all shadow-lg shadow-blue-500/20"
            >
              <BookOpen className="w-4 h-4" />
              <span>Praticar Questões</span>
            </Link>
            <Link
              href="/simulados"
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-medium text-sm transition-all"
            >
              <Flame className="w-4 h-4 text-amber-400" />
              <span>Fazer Simulado</span>
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Taxa de Acerto */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Taxa de Acerto Geral
            </span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{profile?.taxa_acerto_geral}%</span>
            <span className="text-xs text-emerald-400 flex items-center">
              <CheckCircle2 className="w-3 h-3 mr-0.5 inline" /> {profile?.total_acertos} acertos
            </span>
          </div>
          <div className="mt-2 w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-emerald-500 h-full rounded-full transition-all duration-500"
              style={{ width: `${profile?.taxa_acerto_geral || 0}%` }}
            />
          </div>
        </div>

        {/* Questões Resolvidas */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Total de Resoluções
            </span>
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400">
              <Target className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{profile?.total_tentativas}</span>
            <span className="text-xs text-slate-400">questões avaliadas</span>
          </div>
          <p className="mt-2 text-xs text-slate-400">Cadastrado no acervo canônico</p>
        </div>

        {/* Pontos Cegos */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Pontos Cegos Críticos
            </span>
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-amber-400">{profile?.pontos_cegos_count}</span>
            <span className="text-xs text-amber-400/80">tópicos exigem foco</span>
          </div>
          <p className="mt-2 text-xs text-slate-400">Domínio &lt; 50% com recorrência de erros</p>
        </div>

        {/* Tempo Médio */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Tempo Médio / Item
            </span>
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{profile?.tempo_medio_segundos}s</span>
            <span className="text-xs text-slate-400">cadência de prova</span>
          </div>
          <p className="mt-2 text-xs text-emerald-400">Ritmo excelente para o PSC/SIS (180s)</p>
        </div>
      </div>

      {/* Grid: Pontos Cegos & Recomendações + Heatmap Cognitivo */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Painel Esquerdo: Alerta de Pontos Cegos e Ação Imediata */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-900/70 border border-amber-500/30 rounded-2xl p-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/5 rounded-full blur-2xl pointer-events-none" />
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              <h2 className="text-base font-bold text-white">Alerta de Pontos Cegos</h2>
            </div>
            <p className="text-xs text-slate-300 mb-4 leading-relaxed">
              O modelo estatístico detectou tópicos onde suas chances de erro são superiores a 50%.
              Eliminar essas vulnerabilidades é a rota mais rápida para a aprovação.
            </p>

            {pontosCegos.length > 0 ? (
              <div className="space-y-3 mb-6">
                {pontosCegos.map((pc, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-950/60 border border-amber-500/20 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-xs font-semibold text-amber-300">{pc.assunto}</div>
                      <div className="text-[11px] text-slate-400">
                        {pc.disciplina} • {pc.total_erros} erros em {pc.total_tentativas} tentativas
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-extrabold text-red-400">{pc.indice_dominio}%</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-center mb-6">
                <CheckCircle2 className="w-6 h-6 text-emerald-400 mx-auto mb-2" />
                <p className="text-xs text-slate-300 font-medium">Nenhum ponto cego crítico ativo!</p>
                <p className="text-[11px] text-slate-500 mt-1">
                  Continue resolvendo simulados para mapear novos tópicos.
                </p>
              </div>
            )}

            <Link
              href="/questoes?pontoCego=true"
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 font-medium text-xs transition-all"
            >
              <span>Dissecar Questões Desses Tópicos</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Dica da IA */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-2 text-blue-400 text-xs font-semibold">
              <Award className="w-4 h-4" />
              <span>Efeito Flywheel Pedagógico</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Sabia que o <span className="text-blue-300 font-medium">PSC/UFAM</span> e o{" "}
              <span className="text-emerald-300 font-medium">SIS/UEA</span> cobram exatamente as mesmas matrizes
              de competências do Ensino Médio? Resolver questões irmãs entre as duas bancas eleva sua retenção em até 40%.
            </p>
          </div>
        </div>

        {/* Painel Direito: Heatmap Cognitivo de Domínio Curricular */}
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>Heatmap Cognitivo de Domínio</span>
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Visualização do grau de fixação por assunto curricular avaliado.
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-400">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> &gt;= 70% Domínio
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> 50-69%
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500" /> &lt; 50% (Crítico)
              </span>
            </div>
          </div>

          {heatmap.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <BrainCircuit className="w-10 h-10 mx-auto text-slate-600 mb-3" />
              <p className="text-sm">Você ainda não tem histórico de questões suficiente.</p>
              <p className="text-xs text-slate-500 mt-1">
                Resolva questões na Arena de Prática para preencher o seu Heatmap.
              </p>
            </div>
          ) : (
            <div className="space-y-4 max-h-[480px] overflow-y-auto pr-2">
              {heatmap.map((item, idx) => {
                let barColor = "bg-emerald-500";
                let textColor = "text-emerald-400";
                if (item.indice_dominio < 50) {
                  barColor = "bg-red-500";
                  textColor = "text-red-400";
                } else if (item.indice_dominio < 70) {
                  barColor = "bg-amber-500";
                  textColor = "text-amber-400";
                }

                return (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800/80 hover:border-slate-700 transition-all"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-slate-200">{item.assunto}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">
                          {item.disciplina}
                        </span>
                        {item.eh_ponto_cego && (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-red-500/10 border border-red-500/30 text-red-400 font-bold">
                            Ponto Cego
                          </span>
                        )}
                      </div>
                      <span className={`text-xs font-extrabold ${textColor}`}>
                        {item.indice_dominio}%
                      </span>
                    </div>

                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className={`${barColor} h-full rounded-full transition-all duration-500`}
                        style={{ width: `${item.indice_dominio}%` }}
                      />
                    </div>

                    <div className="flex items-center justify-between mt-2 text-[11px] text-slate-500">
                      <span>{item.total_tentativas} resoluções</span>
                      <span>{item.total_erros} erros detectados</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
