import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { setToken, setOnUnauthorized } from '../api/client'
import type { User } from '../types'

interface AuthValue {
  user: User | null
  login: (token: string, user: User) => void
  logout: () => void
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)

  function login(token: string, u: User) {
    setToken(token) // 同步给请求层，之后自动带 Authorization 头
    setUser(u)      // 存用户信息，触发界面更新
  }

  function logout() {
    setToken(null)
    setUser(null)   // user 变 null 后，ProtectedRoute 会自动重定向到登录页
  }

  // 请求层碰到 401 时，回调这里的 logout
  useEffect(() => {
    setOnUnauthorized(logout)
    return () => setOnUnauthorized(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth 必须在 AuthProvider 内使用')
  return ctx
}
