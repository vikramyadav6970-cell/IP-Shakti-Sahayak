/** Auth types */
export interface User {
  id: string
  email: string
  name: string
  role: UserRole
}

export type UserRole =
  | 'USER'
  | 'ADMIN'
  | 'IP_FACILITATOR'
  | 'CONTENT_MANAGER'
  | 'RESEARCHER'
