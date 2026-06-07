/**
 * Evaluations service para el frontend.
 */

import api from '@/lib/api'
import type { Evaluation, EvaluationAttempt } from '@/types'

export interface CreateEvaluationData {
  document_id: string
  title: string
  question_count?: number
  difficulty?: number
  time_limit_minutes?: number
  passing_score?: number
}

export interface SubmitAnswerData {
  question_id: string
  answer_text: string
}

export const evaluationsService = {
  /**
   * Crear evaluación
   */
  async create(data: CreateEvaluationData): Promise<{ id: string; status: string }> {
    const response = await api.post('/evaluations', data)
    return response.data
  },

  /**
   * Listar evaluaciones
   */
  async list(params?: { page?: number; page_size?: number }): Promise<{ items: Evaluation[]; total: number }> {
    const response = await api.get('/evaluations', { params })
    return response.data
  },

  /**
   * Obtener evaluación con preguntas
   */
  async get(evaluationId: string): Promise<any> {
    const response = await api.get(`/evaluations/${evaluationId}`)
    return response.data
  },

  /**
   * Publicar evaluación
   */
  async publish(evaluationId: string): Promise<void> {
    await api.patch(`/evaluations/${evaluationId}/publish`)
  },

  /**
   * Iniciar intento
   */
  async startAttempt(evaluationId: string): Promise<{ attempt_id: string; evaluation_id: string }> {
    const response = await api.post(`/evaluations/${evaluationId}/attempts`)
    return response.data
  },

  /**
   * Submit answers
   */
  async submitAnswers(attemptId: string, answers: SubmitAnswerData[]): Promise<any> {
    const response = await api.post(`/evaluations/attempts/${attemptId}/submit`, { answers })
    return response.data
  },

  /**
   * Obtener resultado
   */
  async getResult(attemptId: string): Promise<any> {
    const response = await api.get(`/evaluations/attempts/${attemptId}/result`)
    return response.data
  }
}

export default evaluationsService