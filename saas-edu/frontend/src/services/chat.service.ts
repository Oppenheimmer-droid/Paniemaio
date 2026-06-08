/**
 * Chat service para el frontend.
 */

import api from '@/lib/api'
import type { ChatSession, ChatMessage } from '@/types'

export interface CreateSessionData {
  title: string
  document_id?: string
}

export interface QueryData {
  question: string
  session_id?: string
  document_id?: string
}

export interface ChatQueryResponse {
  answer: string
  session_id: string
  citations: Array<{
    source: string
    page: number | null
    document_id: string
    text: string
  }>
  tokens_used: number
  latency_ms: number
}

export const chatService = {
  /**
   * Crear sesión de chat
   */
  async createSession(data: CreateSessionData): Promise<ChatSession> {
    const response = await api.post('/chat/sessions', data)
    return response.data
  },

  /**
   * Listar sesiones
   */
  async listSessions(params?: { page?: number; page_size?: number }): Promise<{ items: ChatSession[]; total: number }> {
    const response = await api.get('/chat/sessions', { params })
    return response.data
  },

  /**
   * Obtener mensajes de sesión
   */
  async getMessages(sessionId: string): Promise<{ items: ChatMessage[]; total: number }> {
    const response = await api.get(`/chat/sessions/${sessionId}/messages`)
    return response.data
  },

  /**
   * Enviar pregunta
   */
  async query(data: QueryData): Promise<ChatQueryResponse> {
    const response = await api.post('/chat/query', data)
    return response.data
  }
}

export default chatService