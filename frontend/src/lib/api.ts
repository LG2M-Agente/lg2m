/**
 * Cliente de API tipado para integração com o backend LG2M FastAPI.
 */

import {
  QuestionDetail,
  QuestionAttemptResult,
  StudentProfile,
  HeatmapItem,
  SimuladoSummary,
  SimuladoResult,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchStudentProfile(): Promise<StudentProfile> {
  const res = await fetch(`${API_BASE}/student/profile`, { cache: "no-store" });
  if (!res.ok) throw new Error("Erro ao carregar perfil do estudante");
  return res.json();
}

export async function updateStudentProfile(certameFoco?: string, estiloDidatico?: string): Promise<StudentProfile> {
  const res = await fetch(`${API_BASE}/student/profile`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      certame_foco: certameFoco,
      estilo_didatico_padrao: estiloDidatico,
    }),
  });
  if (!res.ok) throw new Error("Erro ao atualizar perfil");
  return res.json();
}

export async function fetchStudentHeatmap(): Promise<{
  perfil_id: string;
  total_assuntos_avaliados: number;
  pontos_cegos_count: number;
  pontos_cegos: HeatmapItem[];
  heatmap: HeatmapItem[];
}> {
  const res = await fetch(`${API_BASE}/student/heatmap`, { cache: "no-store" });
  if (!res.ok) throw new Error("Erro ao carregar heatmap");
  return res.json();
}

export async function searchQuestions(params: {
  query?: string;
  certame?: string;
  etapa?: string;
  disciplina?: string;
  ano?: number;
  limit?: number;
}): Promise<QuestionDetail[]> {
  const q = new URLSearchParams();
  q.set("query", params.query || "vestibular");
  if (params.certame && params.certame !== "ALL") q.set("certame", params.certame);
  if (params.etapa && params.etapa !== "ALL") q.set("etapa", params.etapa);
  if (params.disciplina && params.disciplina !== "ALL") q.set("disciplina", params.disciplina);
  if (params.ano) q.set("ano", String(params.ano));
  if (params.limit) q.set("limit", String(params.limit));

  const res = await fetch(`${API_BASE}/questions/search?${q.toString()}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Erro na busca de questões");
  return res.json();
}

export async function fetchQuestionDetail(id: string): Promise<QuestionDetail> {
  const res = await fetch(`${API_BASE}/questions/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Questão não encontrada");
  return res.json();
}

export async function fetchSimilarQuestions(id: string): Promise<any[]> {
  const res = await fetch(`${API_BASE}/questions/${id}/similar`, { cache: "no-store" });
  if (!res.ok) return [];
  return res.json();
}

export async function submitQuestionAttempt(params: {
  questionId: string;
  alternativa: string;
  tempoSegundos: number;
  estiloDidatico: string;
}): Promise<QuestionAttemptResult> {
  const res = await fetch(`${API_BASE}/attempts/${params.questionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      alternativa_marcada: params.alternativa,
      tempo_gasto_segundos: params.tempoSegundos,
      estilo_didatico: params.estiloDidatico,
    }),
  });
  if (!res.ok) throw new Error("Erro ao registrar tentativa");
  return res.json();
}

export async function sendMentorMessage(params: {
  questionId: string;
  mensagem: string;
  estiloDidatico: string;
  historico?: { role: string; content: string }[];
}): Promise<{ resposta: string; estilo_didatico: string; guardrail_status: string }> {
  const res = await fetch(`${API_BASE}/mentor/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      questao_id: params.questionId,
      mensagem: params.mensagem,
      estilo_didatico: params.estiloDidatico,
      historico: params.historico || [],
    }),
  });
  if (!res.ok) throw new Error("Erro no diálogo com mentor");
  return res.json();
}

export async function createSimulado(params: {
  certame: string;
  etapa: string;
  tipo: "GERAL" | "TEMATICO";
  disciplinaFoco?: string;
  quantidadeQuestoes: number;
}): Promise<SimuladoSummary> {
  const res = await fetch(`${API_BASE}/simulados/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      certame_sigla: params.certame,
      etapa: params.etapa,
      tipo: params.tipo,
      disciplina_foco: params.disciplinaFoco,
      quantidade_questoes: params.quantidadeQuestoes,
    }),
  });
  if (!res.ok) throw new Error("Erro ao criar simulado");
  return res.json();
}

export async function submitSimulado(params: {
  simuladoId: string;
  respostas: Record<string, string>;
  tempoGastoSegundos: number;
}): Promise<SimuladoResult> {
  const res = await fetch(`${API_BASE}/simulados/${params.simuladoId}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      respostas: params.respostas,
      tempo_utilizado_segundos: params.tempoGastoSegundos,
    }),
  });
  if (!res.ok) throw new Error("Erro ao finalizar simulado");
  return res.json();
}
