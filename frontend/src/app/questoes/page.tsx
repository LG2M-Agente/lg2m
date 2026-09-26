"use client";

import React, { useState, useEffect } from "react";
import {
  Search,
  BookOpen,
  Filter,
  CheckCircle,
  XCircle,
  MessageSquare,
  Sparkles,
  ArrowRight,
  Send,
  HelpCircle,
  Lightbulb,
  Layers,
  ChevronDown,
  ChevronUp,
  Brain,
  ImageIcon
} from "lucide-react";
import {
  searchQuestions,
  submitQuestionAttempt,
  sendMentorMessage,
  fetchSimilarQuestions
} from "../../lib/api";
import { QuestionDetail, QuestionAttemptResult } from "../../lib/types";
import { MathRenderer } from "../../components/MathRenderer";

export default function QuestoesPage() {
  // Estados de busca e filtros
  const [query, setQuery] = useState("Leis de Newton");
  const [certame, setCertame] = useState("ALL");
  const [etapa, setEtapa] = useState("ALL");
  const [disciplina, setDisciplina] = useState("ALL");
  const [loadingSearch, setLoadingSearch] = useState(false);

  // Lista de resultados e questão ativa
  const [questoes, setQuestoes] = useState<QuestionDetail[]>([]);
  const [selectedQuestao, setSelectedQuestao] = useState<QuestionDetail | null>(null);

  // Estado de resolução
  const [alternativaMarcada, setAlternativaMarcada] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [attemptResult, setAttemptResult] = useState<QuestionAttemptResult | null>(null);
  const [showTextoBase, setShowTextoBase] = useState(true);

  // Mentor Drawer e Chat
  const [mentorOpen, setMentorOpen] = useState(false);
  const [estiloDidatico, setEstiloDidatico] = useState<"DIRETO" | "SOCRATICO" | "TEORICO">("SOCRATICO");
  const [chatMessages, setChatMessages] = useState<Array<{ role: "user" | "mentor"; text: string }>>([]);
  const [inputChat, setInputChat] = useState("");
  const [loadingChat, setLoadingChat] = useState(false);

  // Questões Irmãs (Flywheel Cross-Banca)
  const [questoesIrmas, setQuestoesIrmas] = useState<any[]>([]);

  // Executa busca inicial
  useEffect(() => {
    handleSearch();
  }, []);

  const handleSearch = async () => {
    setLoadingSearch(true);
    try {
      const data = await searchQuestions({
        query: query.trim() || "vestibular",
        certame,
        etapa,
        disciplina,
        limit: 10,
      });
      setQuestoes(data);
      if (data.length > 0) {
        selectQuestion(data[0]);
      } else {
        setSelectedQuestao(null);
      }
    } catch (err) {
      console.error("Erro ao buscar questões", err);
    } finally {
      setLoadingSearch(false);
    }
  };

  const selectQuestion = (q: QuestionDetail) => {
    setSelectedQuestao(q);
    setAlternativaMarcada("");
    setAttemptResult(null);
    setChatMessages([]);
    setQuestoesIrmas([]);
    // Carrega questões irmãs em background
    fetchSimilarQuestions(q.id)
      .then(setQuestoesIrmas)
      .catch((e) => console.error("Falha ao buscar semelhantes", e));
  };

  const handleConfirmAnswer = async () => {
    if (!selectedQuestao || !alternativaMarcada) return;
    setSubmitting(true);
    try {
      const res = await submitQuestionAttempt({
        questionId: selectedQuestao.id,
        alternativa: alternativaMarcada,
        tempoSegundos: 45,
        estiloDidatico,
      });
      setAttemptResult(res);
      // Adiciona explicação inicial do mentor ao histórico de chat
      setChatMessages([
        {
          role: "mentor",
          text: res.explicacao_mentor,
        },
      ]);
    } catch (err) {
      console.error("Erro ao submeter resposta", err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSendChatMessage = async () => {
    if (!selectedQuestao || !inputChat.trim() || loadingChat) return;
    const userText = inputChat.trim();
    setInputChat("");
    setChatMessages((prev) => [...prev, { role: "user", text: userText }]);
    setLoadingChat(true);

    try {
      const res = await sendMentorMessage({
        questionId: selectedQuestao.id,
        mensagem: userText,
        estiloDidatico,
      });
      setChatMessages((prev) => [...prev, { role: "mentor", text: res.resposta }]);
    } catch (err) {
      console.error("Erro no chat com mentor", err);
    } finally {
      setLoadingChat(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Barra de Filtros e Busca Semântica */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 sm:p-5 backdrop-blur-md">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch();
          }}
          className="flex flex-col md:flex-row gap-3"
        >
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Pesquise por tema, conceito ou texto do enunciado (ex: Termodinâmica, Cabanagem, Ka)..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-950/80 border border-slate-700/80 rounded-xl text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 transition-all"
            />
          </div>

          <div className="flex flex-wrap sm:flex-nowrap gap-2">
            {/* Certame */}
            <select
              value={certame}
              onChange={(e) => setCertame(e.target.value)}
              className="bg-slate-950/80 border border-slate-700/80 rounded-xl px-3 py-2 text-xs font-medium text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">Todas as Bancas</option>
              <option value="PSC">PSC (UFAM)</option>
              <option value="SIS">SIS (UEA)</option>
            </select>

            {/* Etapa */}
            <select
              value={etapa}
              onChange={(e) => setEtapa(e.target.value)}
              className="bg-slate-950/80 border border-slate-700/80 rounded-xl px-3 py-2 text-xs font-medium text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">Todas as Etapas</option>
              <option value="1">1ª Etapa (1º Ano)</option>
              <option value="2">2ª Etapa (2º Ano)</option>
              <option value="3">3ª Etapa (3º Ano)</option>
            </select>

            {/* Disciplina */}
            <select
              value={disciplina}
              onChange={(e) => setDisciplina(e.target.value)}
              className="bg-slate-950/80 border border-slate-700/80 rounded-xl px-3 py-2 text-xs font-medium text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">Disciplinas</option>
              <option value="Física">Física</option>
              <option value="Química">Química</option>
              <option value="Biologia">Biologia</option>
              <option value="Matemática">Matemática</option>
              <option value="Língua Portuguesa">Língua Portuguesa</option>
              <option value="História">História</option>
              <option value="Geografia">Geografia</option>
            </select>

            <button
              type="submit"
              disabled={loadingSearch}
              className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center gap-1.5 transition-all shadow-md shadow-blue-500/20"
            >
              {loadingSearch ? (
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Filter className="w-3.5 h-3.5" />
                  <span>Filtrar</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Conteúdo Principal: Lista Lateral + Questão Ativa + Mentor Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Coluna Esquerda: Lista de Resultados */}
        <div className="lg:col-span-4 bg-slate-900/60 border border-slate-800 rounded-2xl p-4 max-h-[750px] overflow-y-auto space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-xs text-slate-400 font-medium">
            <span>Resultados ({questoes.length})</span>
            <span>Blindado até resolução 🔒</span>
          </div>

          {questoes.length === 0 && !loadingSearch && (
            <p className="text-xs text-slate-500 text-center py-8">Nenhuma questão encontrada com esses filtros.</p>
          )}

          {questoes.map((q) => {
            const isSelected = selectedQuestao?.id === q.id;
            return (
              <button
                key={q.id}
                onClick={() => selectQuestion(q)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                  isSelected
                    ? "bg-blue-600/10 border-blue-500/50 shadow-sm"
                    : "bg-slate-950/40 border-slate-800/80 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="text-[11px] font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                    {q.certame} {q.ano} • E{q.etapa} • Q{q.numero_questao}
                  </span>
                  <span className="text-[10px] text-slate-400 font-medium">{q.disciplina}</span>
                </div>
                <div className="text-xs font-semibold text-slate-200 mb-1">{q.assunto}</div>
                <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                  {q.enunciado.replace(/[\$#\*]/g, "")}
                </p>
              </button>
            );
          })}
        </div>

        {/* Coluna Central: Questão Ativa para Resolução */}
        <div className="lg:col-span-8 space-y-6">
          {selectedQuestao ? (
            <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 sm:p-8 backdrop-blur-sm shadow-xl">
              {/* Header da Questão */}
              <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-300 font-bold text-xs uppercase tracking-wide">
                    {selectedQuestao.codigo_referencia}
                  </span>
                  <span className="text-xs font-medium text-slate-400">
                    {selectedQuestao.area_conhecimento}
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  Tópico: <span className="text-slate-200 font-medium">{selectedQuestao.assunto}</span>
                </div>
              </div>

              {/* Texto Base Expansível */}
              {selectedQuestao.texto_base && (
                <div className="mt-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300 leading-relaxed">
                  <div
                    onClick={() => setShowTextoBase(!showTextoBase)}
                    className="flex items-center justify-between cursor-pointer font-bold text-slate-400 mb-1"
                  >
                    <span>TEXTO BASE ASSOCIADO</span>
                    {showTextoBase ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                  {showTextoBase && <MathRenderer content={selectedQuestao.texto_base} />}
                </div>
              )}

              {/* Enunciado */}
              <div className="my-6 text-sm md:text-base text-slate-100 font-normal leading-relaxed">
                <MathRenderer content={selectedQuestao.enunciado} />
              </div>

              {/* Figura de Apoio Original da Prova */}
              {selectedQuestao.tem_imagem && (
                <div className="mb-6 p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                  <div className="flex items-center gap-2 text-xs text-amber-400 font-medium">
                    <ImageIcon className="w-4 h-4 shrink-0" />
                    <span>Figura / Gráfico original da banca ({selectedQuestao.certame})</span>
                  </div>
                  <div className="flex justify-center bg-white/95 p-3 rounded-lg overflow-hidden max-h-80 shadow-inner">
                    <img
                      src={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/questions/${selectedQuestao.id}/image`}
                      alt={`Figura da questão ${selectedQuestao.numero_questao}`}
                      className="max-h-72 object-contain"
                      onError={(e) => {
                        const target = e.target as HTMLElement;
                        target.style.display = "none";
                        const parent = target.parentElement;
                        if (parent) {
                          parent.innerHTML = "<p class='text-slate-500 text-xs py-2'>Consulte o caderno de prova oficial para visualização em alta resolução.</p>";
                        }
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Alternativas de A a E */}
              <div className="space-y-3 mb-6">
                {Object.entries(selectedQuestao.alternativas).map(([letra, texto]) => {
                  const isChecked = alternativaMarcada === letra;
                  let altStyle = "bg-slate-950/50 border-slate-800 hover:border-slate-700 text-slate-200";

                  if (attemptResult) {
                    if (letra === attemptResult.gabarito_oficial) {
                      altStyle = "bg-emerald-500/10 border-emerald-500 text-emerald-300 shadow-md shadow-emerald-500/10";
                    } else if (isChecked && !attemptResult.acertou) {
                      altStyle = "bg-red-500/10 border-red-500 text-red-300";
                    } else {
                      altStyle = "opacity-40 bg-slate-950/20 border-slate-900 text-slate-400";
                    }
                  } else if (isChecked) {
                    altStyle = "bg-blue-600/15 border-blue-500 text-blue-200 shadow-md shadow-blue-500/10";
                  }

                  return (
                    <button
                      key={letra}
                      disabled={!!attemptResult || submitting}
                      onClick={() => setAlternativaMarcada(letra)}
                      className={`w-full text-left p-4 rounded-xl border flex items-start gap-3.5 transition-all text-sm ${altStyle}`}
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

              {/* Ações de Resolução */}
              {!attemptResult ? (
                <div className="flex items-center justify-between pt-4 border-t border-slate-800">
                  <span className="text-xs text-slate-500">
                    {alternativaMarcada
                      ? `Alternativa (${alternativaMarcada}) selecionada`
                      : "Selecione uma alternativa para responder"}
                  </span>
                  <button
                    disabled={!alternativaMarcada || submitting}
                    onClick={handleConfirmAnswer}
                    className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-40 text-white font-semibold text-sm transition-all shadow-lg shadow-emerald-600/20"
                  >
                    {submitting ? "Processando..." : "Confirmar Resposta"}
                  </button>
                </div>
              ) : (
                /* Feedback do Resultado Homologado */
                <div className="space-y-4 pt-4 border-t border-slate-800">
                  <div
                    className={`p-4 rounded-xl border flex items-start gap-3 ${
                      attemptResult.acertou
                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                        : "bg-red-500/10 border-red-500/30 text-red-300"
                    }`}
                  >
                    {attemptResult.acertou ? (
                      <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <div className="font-bold text-sm">
                        {attemptResult.acertou
                          ? "Parabéns, você acertou a questão oficial!"
                          : `Você errou. O gabarito oficial homologado é (${attemptResult.gabarito_oficial}).`}
                      </div>
                      <p className="text-xs mt-1 text-slate-300 leading-relaxed">
                        {attemptResult.explicacao_mentor}
                      </p>

                      {attemptResult.cognitive_snapshot?.vicios_cognitivos_relevantes?.length > 0 && (
                        <div className="mt-3 text-[11px] text-amber-300 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-lg flex items-center gap-2">
                          <Brain className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                          <span>Padrão mapeado no Perfil Cognitivo: <strong>{attemptResult.cognitive_snapshot.vicios_cognitivos_relevantes[0]}</strong></span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 justify-between">
                    <button
                      onClick={() => setMentorOpen(!mentorOpen)}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/40 text-blue-300 font-medium text-xs transition-all"
                    >
                      <MessageSquare className="w-4 h-4 text-blue-400" />
                      <span>{mentorOpen ? "Fechar Mentor IA" : "Dissecar com Mentor Socrático"}</span>
                    </button>

                    {attemptResult.ponto_cego_detectado && (
                      <span className="text-xs text-amber-400 font-medium bg-amber-500/10 border border-amber-500/30 px-3 py-1 rounded-lg">
                        ⚠️ Atenção: Ponto cego detectado neste tópico
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Drawer Retrátil do Mentor Socrático */}
              {mentorOpen && (
                <div className="mt-6 p-5 rounded-2xl bg-slate-950 border border-blue-500/30 space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-emerald-400" />
                      <span className="text-xs font-bold text-white uppercase tracking-wider">
                        Mentor Pedagógico Multiagente
                      </span>
                    </div>

                    {/* Seletor de Estilos Didáticos */}
                    <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-[11px]">
                      {(["DIRETO", "SOCRATICO", "TEORICO"] as const).map((style) => (
                        <button
                          key={style}
                          onClick={() => setEstiloDidatico(style)}
                          className={`px-2.5 py-1 rounded font-semibold transition-all ${
                            estiloDidatico === style
                              ? "bg-blue-600 text-white"
                              : "text-slate-400 hover:text-slate-200"
                          }`}
                        >
                          {style === "DIRETO" ? "Direto" : style === "SOCRATICO" ? "Socrático" : "Teórico"}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Contexto do Perfil Cognitivo Pt */}
                  {attemptResult?.cognitive_snapshot && (
                    <div className="p-2.5 rounded-xl bg-blue-950/40 border border-blue-900/40 text-[11px] text-slate-300 flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Brain className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                        <span>
                          Retenção em {attemptResult.cognitive_snapshot.topico_ativo}: <strong>{attemptResult.cognitive_snapshot.dominio_no_topico}%</strong> ({attemptResult.cognitive_snapshot.status_topico})
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                        Pt v{attemptResult.cognitive_snapshot.versao_perfil}
                      </span>
                    </div>
                  )}

                  {/* Histórico do Chat */}
                  <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
                    {chatMessages.map((msg, i) => (
                      <div
                        key={i}
                        className={`p-3 rounded-xl text-xs leading-relaxed ${
                          msg.role === "mentor"
                            ? "bg-blue-950/40 border border-blue-800/40 text-slate-200"
                            : "bg-slate-900 border border-slate-800 text-blue-300 ml-6"
                        }`}
                      >
                        <div className="text-[10px] font-bold text-slate-400 mb-1">
                          {msg.role === "mentor" ? "🤖 MENTOR IA" : "👤 VOCÊ"}
                        </div>
                        <MathRenderer content={msg.text} />
                      </div>
                    ))}
                    {loadingChat && (
                      <div className="p-3 rounded-xl bg-blue-950/20 text-xs text-slate-400 flex items-center gap-2">
                        <div className="w-3.5 h-3.5 border-2 border-blue-400/20 border-t-blue-400 rounded-full animate-spin" />
                        <span>O mentor está formulando sua orientação...</span>
                      </div>
                    )}
                  </div>

                  {/* Input do Chat */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={inputChat}
                      onChange={(e) => setInputChat(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleSendChatMessage()}
                      placeholder="Tire uma dúvida conceitual sobre esta questão..."
                      className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                    <button
                      onClick={handleSendChatMessage}
                      disabled={!inputChat.trim() || loadingChat}
                      className="px-3.5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white rounded-xl transition-all"
                    >
                      <Send className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )}

              {/* Bloco Flywheel: Questões Semelhantes Cross-Banca */}
              {questoesIrmas.length > 0 && (
                <div className="mt-6 pt-6 border-t border-slate-800">
                  <div className="flex items-center gap-2 mb-3">
                    <Layers className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-bold text-white uppercase tracking-wider">
                      Flywheel Cross-Banca: Questões Irmãs Recomendadas
                    </span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {questoesIrmas.map((irma: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-emerald-500/40 transition-all text-xs"
                      >
                        <div className="flex items-center justify-between text-[10px] text-emerald-400 font-bold mb-1">
                          <span>{irma.certame} • {irma.ano || "Paralelo"}</span>
                          <span>{irma.disciplina}</span>
                        </div>
                        <p className="text-slate-300 line-clamp-2 leading-relaxed mb-2">
                          {irma.enunciado}
                        </p>
                        <div className="text-[10px] text-slate-500">
                          Similaridade: <span className="text-slate-400">{irma.motivo_semelhanca || "Mesma competência estrutural"}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
              <BookOpen className="w-12 h-12 mx-auto text-slate-600 mb-3" />
              <p className="text-sm">Selecione uma questão na lista ao lado para iniciar a prática.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
