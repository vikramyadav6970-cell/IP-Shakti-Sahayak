import { apiClient } from './apiClient'
import type { User, UserRole } from '@/types'

interface LoginResponse {
  user: {
    id: string
    name: string
    email: string
    role: UserRole
    created_at: string
  }
  token: {
    access_token: string
    refresh_token: string
    token_type: string
  }
}

interface RegisterRequest {
  name: string
  email: string
  password: string
}

/**
 * Login via backend auth API.
 * Backend uses OAuth2PasswordRequestForm (form-data, not JSON).
 */
export async function loginUser(email: string, password: string): Promise<{ user: User; token: string }> {
  // Backend /auth/login expects x-www-form-urlencoded with 'username' and 'password'
  const formData = new URLSearchParams()
  formData.append('username', email)
  formData.append('password', password)

  const response = await apiClient.post<LoginResponse>('/api/v1/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })

  const { user: u, token } = response.data

  // Store token in localStorage for the API interceptor to pick up
  localStorage.setItem('ip-sakti-auth-token', token.access_token)

  return {
    user: {
      id: u.id,
      name: u.name,
      email: u.email,
      role: u.role,
    },
    token: token.access_token,
  }
}

/**
 * Register a new user via backend auth API.
 */
export async function registerUser(data: RegisterRequest): Promise<{ user: User; token: string }> {
  // Register the user
  await apiClient.post('/api/v1/auth/register', data)

  // Then login to get a token
  return await loginUser(data.email, data.password)
}

/**
 * Logout — clear token from localStorage.
 */
export function logoutUser(): void {
  localStorage.removeItem('ip-sakti-auth-token')
}

/**
 * Check if there's a stored token and try to validate it.
 * Returns null if no valid session exists.
 */
export function getStoredToken(): string | null {
  return localStorage.getItem('ip-sakti-auth-token')
}
