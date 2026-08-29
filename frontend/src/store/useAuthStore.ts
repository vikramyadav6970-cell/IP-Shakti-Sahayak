import { create } from 'zustand'
import type { User } from '@/types'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (user: User, token: string) => void
  logout: () => void
}

const getInitialAuth = () => {
  try {
    const token = localStorage.getItem('ip-sakti-auth-token')
    const userStr = localStorage.getItem('ip-sakti-auth-user')
    if (token && userStr) {
      return { token, user: JSON.parse(userStr) as User, isAuthenticated: true }
    }
  } catch {
    // Ignore localStorage parse errors
  }
  return { token: null, user: null, isAuthenticated: false }
}

const initial = getInitialAuth()

export const useAuthStore = create<AuthState>((set) => ({
  user: initial.user,
  token: initial.token,
  isAuthenticated: initial.isAuthenticated,

  login: (user, token) => {
    try {
      localStorage.setItem('ip-sakti-auth-token', token)
      localStorage.setItem('ip-sakti-auth-user', JSON.stringify(user))
    } catch {
      // Ignore storage errors
    }
    set({ user, token, isAuthenticated: true })
  },

  logout: () => {
    try {
      localStorage.removeItem('ip-sakti-auth-token')
      localStorage.removeItem('ip-sakti-auth-user')
    } catch {
      // Ignore storage errors
    }
    set({ user: null, token: null, isAuthenticated: false })
  },
}))
