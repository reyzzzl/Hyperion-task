import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '@/services/api'

interface User {
  id: string
  email: string
  name: string
  role: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setToken: (token: string) => void
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setToken: (token) => set({ token, isAuthenticated: true }),
      login: async (email, password) => {
        const response = await api.post('/auth/login', { email, password })
        const { access_token, user } = response.data
        set({ user, token: access_token, isAuthenticated: true })
      },
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false })
      },
    }),
    {
      name: 'hyperion-auth',
      partialize: (state) => ({ user: state.user }),
    }
  )
)