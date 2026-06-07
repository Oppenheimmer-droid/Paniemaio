import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Types
export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  role: 'admin' | 'teacher' | 'student'
  tenant_id: string
  tenant_name: string
}

export interface Tenant {
  id: string
  name: string
  slug: string
}

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  tenant: Tenant | null
  isAuthenticated: boolean
  
  // Actions
  login: (data: { user: User; token: string; refresh_token: string; tenant: Tenant }) => void
  logout: () => void
  updateUser: (user: Partial<User>) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,
      tenant: null,
      isAuthenticated: false,
      
      login: (data) => set({
        user: data.user,
        token: data.token,
        refreshToken: data.refresh_token,
        tenant: data.tenant,
        isAuthenticated: true,
      }),
      
      logout: () => set({
        user: null,
        token: null,
        refreshToken: null,
        tenant: null,
        isAuthenticated: false,
      }),
      
      updateUser: (userData) => set((state) => ({
        user: state.user ? { ...state.user, ...userData } : null,
      })),
    }),
    {
      name: 'saas-edu-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        tenant: state.tenant,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

// UI Store
interface UIState {
  sidebarOpen: boolean
  loading: boolean
  
  toggleSidebar: () => void
  setLoading: (loading: boolean) => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  loading: false,
  
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setLoading: (loading) => set({ loading }),
}))