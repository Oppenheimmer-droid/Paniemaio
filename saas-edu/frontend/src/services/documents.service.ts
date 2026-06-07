/**
 * Servicio de documentos para el frontend.
 */

import api from '@/lib/api'
import type { Document, DocumentListResponse, DocumentStatusResponse } from '@/types'

export interface UploadDocumentData {
  file: File
  title: string
  subject_id?: string
  topic_id?: string
  description?: string
  difficulty?: number
}

export const documentsService = {
  /**
   * Subir documento
   */
  async upload(data: UploadDocumentData): Promise<{ id: string; status: string }> {
    const formData = new FormData()
    formData.append('file', data.file)
    formData.append('title', data.title)
    if (data.subject_id) formData.append('subject_id', data.subject_id)
    if (data.topic_id) formData.append('topic_id', data.topic_id)
    if (data.description) formData.append('description', data.description)
    if (data.difficulty) formData.append('difficulty', data.difficulty.toString())

    const response = await api.post('/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  /**
   * Listar documentos
   */
  async list(params?: {
    page?: number
    page_size?: number
    status?: string
  }): Promise<DocumentListResponse> {
    const response = await api.get('/documents', { params })
    return response.data
  },

  /**
   * Obtener documento
   */
  async get(documentId: string): Promise<Document> {
    const response = await api.get(`/documents/${documentId}`)
    return response.data
  },

  /**
   * Obtener estado de procesamiento
   */
  async getStatus(documentId: string): Promise<DocumentStatusResponse> {
    const response = await api.get(`/documents/${documentId}/status`)
    return response.data
  },

  /**
   * Eliminar documento
   */
  async delete(documentId: string): Promise<void> {
    await api.delete(`/documents/${documentId}`)
  },

  /**
   * Descargar documento
   */
  async download(documentId: string): Promise<Blob> {
    const response = await api.get(`/documents/${documentId}/download`, {
      responseType: 'blob'
    })
    return response.data
  }
}

export default documentsService