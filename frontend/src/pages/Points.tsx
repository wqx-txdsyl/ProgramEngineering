import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import Pagination from '../components/Pagination'
import type { PointBalance, PointTransaction } from '../types'

const LIMIT = 20

const SOURCE_LABEL: Record<string, string> = {
  review_approved: '审核奖励',
  redeem: '兑换支出',
  refund: '取消退款',
}

export default function Points() {
  const [balance, setBalance] = useState<number | null>(null)
  const [items, setItems] = useState<PointTransaction[]>([])
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get<PointBalance>('/points/me').then((b) => setBalance(b.balance)).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    setError('')
    api.get<PointTransaction[]>('/points/transactions', { params: { offset, limit: LIMIT } })
      .then(setItems)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [offset])

  return (
    <div className="page">
      <h1>我的积分</h1>
      <div className="card balance-card">
        <span className="stat-label">当前余额</span>
        <span className="balance-num">{balance ?? 0}</span>
      </div>
      <h2>积分流水</h2>
      {error && <p className="error">{error}</p>}
      {loading ? (
        <p className="empty">加载中…</p>
      ) : items.length === 0 ? (
        <p className="empty">暂无流水</p>
      ) : (
        <table className="table">
          <thead>
            <tr><th>类型</th><th>变动</th><th>时间</th></tr>
          </thead>
          <tbody>
            {items.map((t) => (
              <tr key={t.id}>
                <td>{SOURCE_LABEL[t.source_type] ?? t.source_type}</td>
                <td className={t.change > 0 ? 'pos' : 'neg'}>{t.change > 0 ? `+${t.change}` : t.change}</td>
                <td className="muted">{new Date(t.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <Pagination offset={offset} limit={LIMIT} count={items.length} onChange={setOffset} />
    </div>
  )
}
