import axios from 'axios'
import { logger } from '@/lib/logger'

/**
 * Axios instance — the ONLY place HTTP calls originate.
 * See coding_conventions.md rule 6: API calls only inside src/services/.
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: attach auth token
apiClient.interceptors.request.use(
  (config) => {
    try {
      if (typeof localStorage !== 'undefined') {
        const token = localStorage.getItem('ip-sakti-auth-token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
      }
    } catch {
      // Ignore storage access errors
    }
    return config
  },
  (error: unknown) => Promise.reject(error)
)

// Response interceptor: structured error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status
      const message = (error.response?.data as Record<string, unknown>)?.detail ?? error.message

      logger.error(`API Error [${status}]:`, message)

      if (status === 401) {
        localStorage.removeItem('ip-sakti-auth-token')
        // Auth store will handle redirect
      }
    }
    return Promise.reject(error)
  }
)
