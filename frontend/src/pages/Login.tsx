import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, setToken, getErrorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import type { LoginResponse, User } from '../types'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      // 1. 登录拿 token
      const res = await api.post<LoginResponse>('/auth/login', { username, password })
      // 2. 把 token 存进请求层，才能调 /me
      setToken(res.access_token)
      // 3. 用 token 查自己的身份（含 role）
      const me = await api.get<User>('/auth/me')
      // 4. 存进登录态
      login(res.access_token, me)
      navigate('/')
    } catch (err) {
      const msg = getErrorMessage(err)
      setError(msg === 'Invalid username or password' ? '账号或密码错误' : msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <form className="card login-card" onSubmit={handleSubmit}>
        <h1>登录</h1>
        <p className="muted">学习激励与协作平台</p>
        <label>
          用户名
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="teacher 或 student" autoFocus />
        </label>
        <label>
          密码
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="你的密码" />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="btn btn-primary" type="submit" disabled={loading || !username || !password}>
          {loading ? '登录中…' : '登录'}
        </button>
      </form>
    </div>
  )
}
