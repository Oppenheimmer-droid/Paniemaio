// saas-edu/frontend/src/lib/api.ts
import axios, { AxiosInstance } from 'axios'

const api: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request: inject token ─────────────────────────────────────────────────────
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Response: handle 401 → clear & redirect ───────────────────────────────────
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export interface ApiError { code: string; message: string; detail?: string }
export interface ApiResponse<T> { data: T; message?: string }

export default api