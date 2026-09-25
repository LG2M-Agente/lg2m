/**
 * Tipagens TypeScript do ecossistema LG2M.
 */

export interface QuestionDetail {
  id: string;
  codigo_referencia: string;
  certame: "PSC" | "SIS" | string;
  ano: number;
  etapa: string;
  numero_questao: number;
  disciplina: string;
  area_conhecimento: string;
  assunto: string;
  texto_base?: string | null;
  enunciado: string;
  alternativas: Record<string, string>;
  tem_imagem: boolean;
  imagens?: any[];
  possui_formula_matematica: boolean;
  tags: string[];
}

export interface QuestionAttemptResult {
  acertou: boolean;
  gabarito_oficial: string;
  alternativa_marcada: string;
  explicacao_mentor: string;
  estilo_didatico: string;
  causa_erro?: string | null;
  novo_score_assunto?: number | null;
  ponto_cego_detectado: boolean;
}

export interface HeatmapItem {
  assunto: string;
  disciplina: string;
  area: string;
  total_tentativas: number;
  total_erros: number;
  indice_dominio: number;
  eh_ponto_cego: boolean;
}

export interface StudentProfile {
  usuario_id: string;
  perfil_id: string;
  nome: string;
  email: string;
  certame_foco: string;
  estilo_didatico_padrao: string;
  total_tentativas: number;
  total_acertos: number;
  taxa_acerto_geral: number;
  pontos_cegos_count: number;
  tempo_medio_segundos: number;
  dossie_cognitivo_markdown?: string | null;
  versao_perfil?: number;
}

export interface SimuladoSummary {
  simulado_id: string;
  certame: string;
  etapa: string;
  tipo: string;
  total_questoes: number;
  tempo_limite_minutos: number;
  status: string;
  questoes: {
    ordem: number;
    questao_id: string;
    disciplina: string;
    assunto: string;
    enunciado: string;
    texto_base?: string | null;
    alternativas: Record<string, string>;
    tem_imagem: boolean;
  }[];
}

export interface SimuladoResult {
  simulado_id: string;
  total_questoes: number;
  total_acertos: number;
  acertos: number;
  aproveitamento_percentual: number;
  tempo_gasto_segundos: number;
  desempenho_por_disciplina: Record<string, { total: number; acertos: number }>;
  diagnostico_ia: string;
  itens: {
    ordem: number;
    questao_id: string;
    disciplina: string;
    assunto: string;
    alternativa_marcada: string;
    gabarito_oficial: string;
    acertou: boolean;
  }[];
}
