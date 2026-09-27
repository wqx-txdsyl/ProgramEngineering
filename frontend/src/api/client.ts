import axios, { type AxiosRequestConfig } from 'axios'

// token 存在模块变量里（内存），页面刷新后丢失，需要重新登录
let token: string | null = null
export function setToken(t: string | null) {
  token = t
}

// 401 时的回调，由 AuthContext 注册（用于自动登出）
let onUnauthorized: (() => void) | null = null
export function setOnUnauthorized(fn: (() => void) | null) {
  onUnauthorized = fn
}

const instance = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// 请求拦截器：每个请求自动带上 token
instance.interceptors.request.use((config) => {
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一处理 401；成功时直接返回 data
instance.interceptors.response.use(
  (res) => res.data,
  (err) => {
    // 登录接口的 401 表示「账号或密码错」，不要触发登出
    if (err.response?.status === 401 && !err.config?.url?.includes('/auth/login')) {
      onUnauthorized?.()
    }
    return Promise.reject(err)
  },
)

// 类型安全的请求方法（拦截器返回的是 data，这里用 as 告诉 TS）
export const api = {
  get: <T>(url: string, config?: AxiosRequestConfig) => instance.get(url, config) as Promise<T>,
  post: <T>(url: string, body?: unknown, config?: AxiosRequestConfig) => instance.post(url, body, config) as Promise<T>,
  put: <T>(url: string, body?: unknown, config?: AxiosRequestConfig) => instance.put(url, body, config) as Promise<T>,
  patch: <T>(url: string, body?: unknown, config?: AxiosRequestConfig) => instance.patch(url, body, config) as Promise<T>,
}

// 从后端错误里提取可读信息；detail 可能是字符串，也可能是数组
export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const status = err.response?.status
    const detail = err.response?.data?.detail
    if (typeof detail === 'string' && detail) return detail
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0]
      if (typeof first === 'string') return first
      if (first && typeof first === 'object' && 'msg' in first) {
        return String((first as { msg: unknown }).msg)
      }
    }
    if (status === 403) return '没有权限执行此操作'
    if (status === 404) return '对象不存在或已被删除'
    if (status === 409) return '操作冲突，请刷新后重试'
    if (status === 422) return '提交的内容不符合要求'
    return err.message || '请求失败'
  }
  return '请求失败'
}
