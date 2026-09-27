import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import { RedemptionBadge } from '../components/StatusBadge'
import Pagination from '../components/Pagination'
import type { Redemption } from '../types'

const LIMIT = 20

export default function MyRedemptions() {
  const [items, setItems] = useState<Redemption[]>([])
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [cancelling, setCancelling] = useState<number | null>(null)

  useEffect(() => {
    setLoading(true)
    setError('')
    api.get<Redemption[]>('/rewards/redemptions/mine', { params: { offset, limit: LIMIT } })
      .then(setItems)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [offset])

  async function cancel(id: number) {
    if (!window.confirm('确定取消这个兑换吗？积分会退回。')) return
    setCancelling(id)
    setError('')
    setSuccess('')
    try {
      await api.post<Redemption>(`/rewards/redemptions/${id}/cancel`)
      setSuccess('已取消，积分已退回')
      setItems((prev) => prev.map((r) => (r.id === id ? { ...r, status: 'cancelled' } : r)))
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setCancelling(null)
    }
  }

  return (
    <div className="page">
      <h1>我的兑换</h1>
      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}
      {loading ? (
        <p className="empty">加载中…</p>
      ) : items.length === 0 ? (
        <p className="empty">暂无兑换记录</p>
      ) : (
        <div className="list">
          {items.map((r) => (
            <div key={r.id} className="card">
              <div className="submission-head">
                <span>兑换单 #{r.id} · 奖励 #{r.reward_id} · {r.cost} 积分</span>
                <RedemptionBadge status={r.status} />
              </div>
              <div className="muted">时间：{new Date(r.created_at).toLocaleString()}</div>
              {r.status === 'active' && (
                <div className="submission-actions">
                  <button className="btn btn-danger btn-sm" disabled={cancelling === r.id} onClick={() => cancel(r.id)}>
                    {cancelling === r.id ? '取消中…' : '取消兑换'}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      <Pagination offset={offset} limit={LIMIT} count={items.length} onChange={setOffset} />
    </div>
  )
}
