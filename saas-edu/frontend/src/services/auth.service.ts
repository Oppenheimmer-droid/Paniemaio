// saas-edu/frontend/src/services/auth.service.ts
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'

export const authService = {
  async login(data: { email: string; password: string; tenant_slug: string }) {
    const res = await api.post('/auth/login', data)
    const d = res.data
    useAuthStore.getState().login({
      user: d.user,
      token: d.access_token,
      refresh_token: d.refresh_token,
      tenant: d.tenant,
    })
    return d
  },

  async register(data: {
    tenant_name: string; tenant_slug: string
    admin_email: string; admin_password: string
    admin_first_name: string; admin_last_name: string
  }) {
    const res = await api.post('/auth/register', data)
    const d = res.data
    useAuthStore.getState().login({
      user: d.user,
      token: d.access_token,
      refresh_token: d.refresh_token,
      tenant: d.tenant,
    })
    return d
  },

  async logout() {
    const { refreshToken } = useAuthStore.getState()
    try {
      await api.post('/auth/logout', { refresh_token: refreshToken })
    } finally {
      useAuthStore.getState().logout()
    }
  },

  async getMe() {
    const res = await api.get('/auth/me')
    return res.data
  },
}

export default authService