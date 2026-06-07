/**
 * Servicio de autenticación para el frontend.
 */

import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import type { AuthResponse, UserLogin, RegisterTenantRequest } from '@/types'

export const authService = {
  /**
   * Login de usuario
   */
  async login(data: UserLogin): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/login', data)
    const authData = response.data
    
    // Guardar en store
    const { login } = useAuthStore.getState()
    login({
      user: authData.user,
      token: authData.access_token,
      refresh_token: authData.refresh_token,
      tenant: authData.tenant as any
    })
    
    return authData
  },

  /**
   * Registro de nuevo tenant
   */
  async register(data: RegisterTenantRequest): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/register', data)
    const authData = response.data
    
    // Guardar en store
    const { login } = useAuthStore.getState()
    login({
      user: authData.user,
      token: authData.access_token,
      refresh_token: authData.refresh_token,
      tenant: authData.tenant as any
    })
    
    return authData
  },

  /**
   * Refrescar token
   */
  async refresh(refreshToken: string): Promise<{ access_token: string; refresh_token: string }> {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken })
    return response.data
  },

  /**
   * Logout
   */
  async logout(): Promise<void> {
    const { refreshToken } = useAuthStore.getState()
    
    try {
      await api.post('/auth/logout', { refresh_token: refreshToken })
    } finally {
      useAuthStore.getState().logout()
    }
  },

  /**
   * Obtener usuario actual
   */
  async getMe(): Promise<AuthResponse['user']> {
    const response = await api.get('/auth/me')
    return response.data
  },

  /**
   * Verificar si el usuario está autenticado
   */
  async checkAuth(): Promise<boolean> {
    try {
      await this.getMe()
      return true
    } catch {
      return false
    }
  }
}

export default authService