import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import Pagination from '../components/Pagination'
import type { Submission } from '../types'

const LIMIT = 20

export default function Review() {
  const [items, setItems] = useState<Submission[]>([])
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [feedback, setFeedback] = useState<Record<number, string>>({})
  const [submitting, setSubmitting] = useState<number | null>(null)

  useEffect(() => {
    setLoading(true)
    setError('')
    api.get<Submission[]>('/reviews/pending', { params: { offset, limit: LIMIT } })
      .then(setItems)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [offset])

  async function review(id: number, decision: 'approved' | 'rejected') {
    const fb = (feedback[id] ?? '').trim()
    if (!fb) {
      setError('反馈不能为空')
      return
    }
    setSubmitting(id)
    setError('')
    try {
      await api.post<Submission>(`/reviews/${id}`, { decision, feedback: fb })
      setItems((prev) => prev.filter((s) => s.id !== id))
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(null)
    }
  }

  return (
    <div className="page">
      <h1>待审核成果</h1>
      {error && <p className="error">{error}</p>}
      {loading ? (
        <p className="empty">加载中…</p>
      ) : items.length === 0 ? (
        <p className="empty">暂无待审核成果</p>
      ) : (
        <div className="list">
          {items.map((s) => (
            <div key={s.id} className="card">
              <div className="submission-head">
                <span>成果 #{s.id} · 学生 #{s.student_id} · 任务 #{s.task_id}</span>
              </div>
              <div className="content-box">{s.content}</div>
              <textarea
                className="review-input"
                rows={3}
                placeholder="填写反馈（必填）"
                value={feedback[s.id] ?? ''}
                onChange={(e) => setFeedback((f) => ({ ...f, [s.id]: e.target.value }))}
              />
              <div className="submission-actions">
                <button className="btn btn-primary" disabled={submitting === s.id} onClick={() => review(s.id, 'approved')}>
                  通过（+10 分）
                </button>
                <button className="btn btn-danger" disabled={submitting === s.id} onClick={() => review(s.id, 'rejected')}>
                  退回
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      <Pagination offset={offset} limit={LIMIT} count={items.length} onChange={setOffset} />
    </div>
  )
}
