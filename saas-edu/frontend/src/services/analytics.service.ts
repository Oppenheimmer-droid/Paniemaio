/**
 * Analytics service para el frontend.
 */

import api from '@/lib/api'
import type { AnalyticsOverview, StudentProgress, DocumentUsage } from '@/types'

export const analyticsService = {
  /**
   * Obtener overview
   */
  async getOverview(): Promise<AnalyticsOverview> {
    const response = await api.get('/analytics/overview')
    return response.data
  },

  /**
   * Progreso de estudiantes
   */
  async getStudentsProgress(params?: { page?: number; page_size?: number }): Promise<{ items: StudentProgress[]; total: number }> {
    const response = await api.get('/analytics/students', { params })
    return response.data
  },

  /**
   * Uso de documentos
   */
  async getDocumentsUsage(params?: { page?: number; page_size?: number }): Promise<{ items: DocumentUsage[]; total: number }> {
    const response = await api.get('/analytics/documents', { params })
    return response.data
  },

  /**
   * Mis estadísticas (student)
   */
  async getMyStats(): Promise<any> {
    const response = await api.get('/analytics/me')
    return response.data
  }
}

export default analyticsService