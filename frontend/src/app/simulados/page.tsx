"use client";

import React, { useState, useEffect } from "react";
import {
  FileText,
  Clock,
  CheckCircle2,
  AlertCircle,
  BarChart3,
  Award,
  ArrowRight,
  ArrowLeft,
  Flame,
  Brain,
  RotateCcw
} from "lucide-react";
import { createSimulado, submitSimulado } from "../../lib/api";
import { SimuladoSummary, SimuladoResult } from "../../lib/types";
import { MathRenderer } from "../../components/MathRenderer";

export default function SimuladosPage() {
  // Estados de configuração
  const [certame, setCertame] = useState<"PSC" | "SIS">("PSC");
  const [etapa, setEtapa] = useState("1");
  const [tipo, setTipo] = useState<"GERAL" | "TEMATICO">("GERAL");
  const [disciplinaFoco, setDisciplinaFoco] = useState("Física");
  const [qtdQuestoes, setQtdQuestoes] = useState(15);
  const [loadingCreate, setLoadingCreate] = useState(false);

  // Estados de execução da prova
  const [simulado, setSimulado] = useState<SimuladoSummary | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [respostas, setRespostas] = useState<Record<string, string>>({});
  const [tempoRestanteSegundos, setTempoRestanteSegundos] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  // Estado de resultado pós-prova
  const [resultado, setResultado] = useState<SimuladoResult | null>(null);

  // Efeito do cronômetro da prova
  useEffect(() => {
    if (!simulado || resultado) return;
    const interval = setInterval(() => {
      setTempoRestanteSegundos((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          handleFinalizarProva();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [simulado, resultado]);

  const handleIniciarSimulado = async () => {
    setLoadingCreate(true);
    try {
      const data = await createSimulado({
        certame,
        etapa,
        tipo,
        disciplinaFoco: tipo === "TEMATICO" ? disciplinaFoco : undefined,
        quantidadeQuestoes: qtdQuestoes,
      });
      setSimulado(data);
      setCurrentIdx(0);
      setRespostas({});
      setResultado(null);
      setTempoRestanteSegundos(data.tempo_limite_minutos * 60);
    } catch (err) {
      console.error("Falha ao gerar simulado", err);
    } finally {
      setLoadingCreate(false);
    }
  };

  const handleSelecionarAlternativa = (letra: string) => {
    if (!simulado) return;
    const currentQ = simulado.questoes[currentIdx];
    setRespostas((prev) => ({
      ...prev,
      [currentQ.questao_id]: letra,
    }));
  };

  const handleFinalizarProva = async () => {
    if (!simulado || submitting) return;
    setSubmitting(true);
    try {
      const tempoUsado = simulado.tempo_limite_minutos * 60 - tempoRestanteSegundos;
      const res = await submitSimulado({
        simuladoId: simulado.simulado_id,
        respostas,
        tempoGastoSegundos: Math.max(10, tempoUsado),
      });
      setResultado(res);
    } catch (err) {
      console.error("Erro ao submeter simulado", err);
    } finally {
      setSubmitting(false);
    }
  };

  const formatTempo = (segundos: number) => {
    const m = Math.floor(segundos / 60);
    const s = segundos % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  // --- TELA DE RESULTADO PÓS-PROVA ---
  if (resultado) {
    return (
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="p-8 rounded-2xl bg-gradient-to-r from-blue-950/80 via-slate-900 to-emerald-950/70 border border-slate-800 text-center relative overflow-hidden">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold mb-3">
            <CheckCircle2 className="w-4 h-4" />
            <span>Simulado Finalizado com Sucesso</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white">Relatório Diagnóstico de Desempenho</h1>
          <p className="text-slate-300 text-sm mt-2 max-w-xl mx-auto">
            Diagnóstico emitido pelo Agente Profiler com base nas suas respostas e na matriz curricular do certame.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-xs text-slate-400 font-medium">Aproveitamento</span>
              <div className="text-3xl font-extrabold text-emerald-400 mt-1">
                {resultado.aproveitamento_percentual}%
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-xs text-slate-400 font-medium">Acertos Oficiais</span>
              <div className="text-3xl font-extrabold text-white mt-1">
                {resultado.total_acertos} / {resultado.total_questoes}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-xs text-slate-400 font-medium">Tempo Utilizado</span>
              <div className="text-3xl font-extrabold text-blue-400 mt-1">
                {formatTempo(resultado.tempo_gasto_segundos)}
              </div>
            </div>
          </div>
        </div>

        {/* Parecer do Agente Profiler */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-blue-500/30">
          <div className="flex items-center gap-2 mb-2 text-blue-400 text-xs font-bold uppercase tracking-wider">
            <Brain className="w-4 h-4 text-emerald-400" />
            <span>Parecer Pedagógico do Mentor IA</span>
          </div>
          <MathRenderer content={resultado.diagnostico_ia} className="text-slate-200 text-sm" />
        </div>

        {/* Desempenho por Disciplina */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <span>Rendimento por Disciplina</span>
          </h2>
          <div className="space-y-3">
            {Object.entries(resultado.desempenho_por_disciplina).map(([disc, stats]) => {
              const perc = Math.round((stats.acertos / stats.total) * 100);
              return (
                <div key={disc} className="p-3 rounded-xl bg-slate-950/50 border border-slate-800">
                  <div className="flex items-center justify-between text-xs mb-1.5 font-medium">
                    <span className="text-slate-200">{disc}</span>
                    <span className={perc >= 70 ? "text-emerald-400" : perc >= 50 ? "text-amber-400" : "text-red-400"}>
                      {stats.acertos}/{stats.total} ({perc}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        perc >= 70 ? "bg-emerald-500" : perc >= 50 ? "bg-amber-500" : "bg-red-500"
                      }`}
                      style={{ width: `${perc}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Botão Novo Simulado */}
        <div className="text-center pt-4">
          <button
            onClick={() => {
              setSimulado(null);
              setResultado(null);
            }}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition-all"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Configurar Outro Simulado</span>
          </button>
        </div>
      </div>
    );
  }

  // --- TELA DE EXECUÇÃO DA PROVA ---
  if (simulado) {
    const qAtual = simulado.questoes[currentIdx];
    const totalQ = simulado.questoes.length;
    const alternativaAtual = respostas[qAtual.questao_id] || "";
    const respondidasCount = Object.keys(respostas).length;

    return (
      <div className="space-y-6">
        {/* Barra Superior do Simulado */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4 backdrop-blur-md sticky top-20 z-40">
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 rounded-lg bg-blue-600 text-white font-extrabold text-xs">
              {simulado.certame} • ETAPA {simulado.etapa}
            </span>
            <span className="text-xs text-slate-300 font-medium">
              Questão {currentIdx + 1} de {totalQ}
            </span>
          </div>

          {/* Cronômetro */}
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs font-mono font-bold">
            <Clock className="w-4 h-4 text-amber-400" />
            <span>{formatTempo(tempoRestanteSegundos)}</span>
          </div>

          <button
            onClick={handleFinalizarProva}
            disabled={submitting}
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-all shadow-md shadow-emerald-500/20"
          >
            {submitting ? "Corrigindo..." : "Entregar Prova"}
          </button>
        </div>

        {/* Grade de Navegação das Questões (Pills) */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-3 flex flex-wrap gap-1.5 items-center justify-center">
          {simulado.questoes.map((item, idx) => {
            const foiMarcada = !!respostas[item.questao_id];
            const isSelected = idx === currentIdx;
            return (
              <button
                key={item.questao_id}
                onClick={() => setCurrentIdx(idx)}
                className={`w-8 h-8 rounded-lg text-xs font-bold transition-all ${
                  isSelected
                    ? "bg-blue-600 text-white ring-2 ring-blue-400/50"
                    : foiMarcada
                    ? "bg-emerald-950 border border-emerald-500/40 text-emerald-400"
                    : "bg-slate-950 border border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                {idx + 1}
              </button>
            );
          })}
        </div>

        {/* Card da Questão Ativa */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 sm:p-8 backdrop-blur-sm shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-xs text-slate-400 mb-4">
            <span className="font-bold text-slate-200">{qAtual.disciplina}</span>
            <span>Tópico: {qAtual.assunto}</span>
          </div>

          {qAtual.texto_base && (
            <div className="mb-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300 leading-relaxed">
              <span className="font-bold text-slate-400 block mb-1">TEXTO BASE:</span>
              <MathRenderer content={qAtual.texto_base} />
            </div>
          )}

          <div className="text-sm md:text-base text-slate-100 font-normal leading-relaxed mb-6">
            <MathRenderer content={qAtual.enunciado} />
          </div>

          {/* Alternativas */}
          <div className="space-y-3 mb-6">
            {Object.entries(qAtual.alternativas).map(([letra, texto]) => {
              const isChecked = alternativaAtual === letra;
              return (
                <button
                  key={letra}
                  onClick={() => handleSelecionarAlternativa(letra)}
                  className={`w-full text-left p-4 rounded-xl border flex items-start gap-3.5 transition-all text-sm ${
                    isChecked
                      ? "bg-blue-600/15 border-blue-500 text-blue-200 shadow-md shadow-blue-500/10"
                      : "bg-slate-950/50 border-slate-800 hover:border-slate-700 text-slate-200"
                  }`}
                >
                  <span
                    className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 ${
                      isChecked
                        ? "bg-blue-600 text-white"
                        : "bg-slate-800 border border-slate-700 text-slate-300"
                    }`}
                  >
                    {letra}
                  </span>
                  <div className="flex-1 pt-0.5">
                    <MathRenderer content={texto} />
                  </div>
                </button>
              );
            })}
          </div>

          {/* Botões de Navegação Anterior / Próxima */}
          <div className="flex items-center justify-between pt-4 border-t border-slate-800">
            <button
              onClick={() => setCurrentIdx((prev) => Math.max(0, prev - 1))}
              disabled={currentIdx === 0}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-xs text-slate-300 transition-all"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Anterior</span>
            </button>

            <span className="text-xs text-slate-500">
              {respondidasCount} de {totalQ} respondidas
            </span>

            <button
              onClick={() => setCurrentIdx((prev) => Math.min(totalQ - 1, prev + 1))}
              disabled={currentIdx === totalQ - 1}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-xs text-slate-300 transition-all"
            >
              <span>Próxima</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --- TELA DE CONFIGURAÇÃO DE SIMULADO ---
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white flex items-center gap-3">
          <FileText className="w-7 h-7 text-blue-400" />
          <span>Configurador de Simulados Seriados</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Gere cadernos oficiais cronometrados calibrados com a distribuição curricular real do PSC/UFAM ou SIS/UEA.
        </p>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
        {/* Escolha do Certame */}
        <div>
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-3">
            1. Escolha o Vestibular Seriado Alvo
          </label>
          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setCertame("PSC")}
              className={`p-4 rounded-xl border text-left transition-all ${
                certame === "PSC"
                  ? "bg-blue-600/15 border-blue-500 shadow-md shadow-blue-500/10"
                  : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="font-bold text-sm text-blue-400">PSC (UFAM)</div>
              <p className="text-xs text-slate-400 mt-1">
                Processo Seletivo Contínuo • 54 questões com pesos específicos por etapa.
              </p>
            </button>

            <button
              type="button"
              onClick={() => setCertame("SIS")}
              className={`p-4 rounded-xl border text-left transition-all ${
                certame === "SIS"
                  ? "bg-emerald-600/15 border-emerald-500 shadow-md shadow-emerald-500/10"
                  : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="font-bold text-sm text-emerald-400">SIS (UEA)</div>
              <p className="text-xs text-slate-400 mt-1">
                Sistema de Ingresso Seriado • 60 questões (padrão Vunesp com 8 questões por disciplina).
              </p>
            </button>
          </div>
        </div>

        {/* Escolha da Etapa */}
        <div>
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-3">
            2. Selecione a Etapa Escolar
          </label>
          <div className="grid grid-cols-3 gap-3">
            {(["1", "2", "3"] as const).map((e) => (
              <button
                key={e}
                type="button"
                onClick={() => setEtapa(e)}
                className={`py-3 rounded-xl border text-center font-bold text-xs transition-all ${
                  etapa === e
                    ? "bg-blue-600 text-white border-blue-500"
                    : "bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700"
                }`}
              >
                {e}ª Etapa ({e}º Ano EM)
              </button>
            ))}
          </div>
        </div>

        {/* Tipo de Simulado */}
        <div>
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-3">
            3. Formato do Simulado
          </label>
          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setTipo("GERAL")}
              className={`p-4 rounded-xl border text-left transition-all ${
                tipo === "GERAL"
                  ? "bg-blue-600/15 border-blue-500 shadow-sm"
                  : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="font-bold text-xs text-slate-200">Geral Multi-Disciplinar</div>
              <p className="text-[11px] text-slate-400 mt-1">
                Caderno balanceado cobrindo todas as áreas de conhecimento.
              </p>
            </button>

            <button
              type="button"
              onClick={() => setTipo("TEMATICO")}
              className={`p-4 rounded-xl border text-left transition-all ${
                tipo === "TEMATICO"
                  ? "bg-blue-600/15 border-blue-500 shadow-sm"
                  : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="font-bold text-xs text-slate-200">Temático Específico</div>
              <p className="text-[11px] text-slate-400 mt-1">
                Foco concentrado em uma única disciplina para eliminar deficiências.
              </p>
            </button>
          </div>
        </div>

        {/* Quantidade de Questões */}
        <div>
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-3">
            4. Quantidade de Questões
          </label>
          <div className="flex gap-3">
            {[5, 10, 15, 30].map((qtd) => (
              <button
                key={qtd}
                type="button"
                onClick={() => setQtdQuestoes(qtd)}
                className={`flex-1 py-2.5 rounded-xl border font-bold text-xs transition-all ${
                  qtdQuestoes === qtd
                    ? "bg-emerald-600 text-white border-emerald-500"
                    : "bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700"
                }`}
              >
                {qtd} Itens
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={handleIniciarSimulado}
          disabled={loadingCreate}
          className="w-full py-3.5 rounded-xl bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 disabled:opacity-40 text-white font-bold text-sm transition-all shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2"
        >
          {loadingCreate ? (
            <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          ) : (
            <>
              <Flame className="w-4 h-4 text-amber-300" />
              <span>Gerar Caderno & Iniciar Prova</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
