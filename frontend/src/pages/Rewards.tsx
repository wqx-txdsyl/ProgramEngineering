import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import Pagination from '../components/Pagination'
import type { PointBalance, Redemption, Reward } from '../types'

const LIMIT = 20

export default function Rewards() {
  const { user } = useAuth()
  const isStudent = user?.role === 'student'

  const [items, setItems] = useState<Reward[]>([])
  const [balance, setBalance] = useState<number | null>(null)
  const [offset, setOffset] = useState(0)
  const [version, setVersion] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [redeeming, setRedeeming] = useState<number | null>(null)

  useEffect(() => {
    if (isStudent) {
      api.get<PointBalance>('/points/me').then((b) => setBalance(b.balance)).catch(() => {})
    }
  }, [isStudent, version])

  useEffect(() => {
    setLoading(true)
    setError('')
    api.get<Reward[]>('/rewards', { params: { offset, limit: LIMIT } })
      .then(setItems)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [offset, version])

  async function redeem(reward: Reward) {
    if (!window.confirm(`确定用 ${reward.cost} 积分兑换「${reward.name}」吗？`)) return
    setRedeeming(reward.id)
    setError('')
    setSuccess('')
    try {
      // 幂等键：前端生成 UUID，网络重试时复用同一个，防止重复扣费
      const requestKey = crypto.randomUUID()
      await api.post<Redemption>(`/rewards/${reward.id}/redeem`, { request_key: requestKey })
      setSuccess('兑换成功！')
      setVersion((v) => v + 1)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setRedeeming(null)
    }
  }

  return (
    <div className="page">
      <div className="page-head">
        <h1>奖励商店</h1>
        {isStudent && balance !== null && <span className="chip">我的积分：{balance}</span>}
      </div>
      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}
      {loading ? (
        <p className="empty">加载中…</p>
      ) : items.length === 0 ? (
        <p className="empty">暂无奖励</p>
      ) : (
        <div className="reward-grid">
          {items.map((r) => (
            <div key={r.id} className="card reward-card">
              <div className="reward-name">{r.name}</div>
              <div className="muted reward-desc">{r.description || '（无描述）'}</div>
              <div className="reward-meta">
                <span className="chip">{r.cost} 积分</span>
                <span className="chip">库存 {r.stock}</span>
              </div>
              {isStudent && (
                <button
                  className="btn btn-primary"
                  disabled={redeeming === r.id || r.stock <= 0}
                  onClick={() => redeem(r)}
                >
                  {r.stock <= 0 ? '已售罄' : '兑换'}
                </button>
              )}
            </div>
          ))}
        </div>
      )}
      <Pagination offset={offset} limit={LIMIT} count={items.length} onChange={setOffset} />
    </div>
  )
}
