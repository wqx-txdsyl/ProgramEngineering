import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, getErrorMessage } from '../api/client'
import { SubmissionBadge } from '../components/StatusBadge'
import Pagination from '../components/Pagination'
import type { Submission } from '../types'

const LIMIT = 20

export default function MySubmissions() {
  const [tab, setTab] = useState<'all' | 'pending'>('all')
  const [items, setItems] = useState<Submission[]>([])
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    const url = tab === 'all' ? '/submissions/mine' : '/submissions/mine/pending'
    api.get<Submission[]>(url, { params: { offset, limit: LIMIT } })
      .then(setItems)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [tab, offset])

  return (
    <div className="page">
      <h1>我的成果</h1>
      <div className="tabs">
        <button className={`tab ${tab === 'all' ? 'active' : ''}`} onClick={() => { setTab('all'); setOffset(0) }}>全部</button>
        <button className={`tab ${tab === 'pending' ? 'active' : ''}`} onClick={() => { setTab('pending'); setOffset(0) }}>待审核</button>
      </div>
      {error && <p className="error">{error}</p>}
      {loading ? (
        <p className="empty">加载中…</p>
      ) : items.length === 0 ? (
        <p className="empty">暂无提交</p>
      ) : (
        <div className="list">
          {items.map((s) => (
            <div key={s.id} className="card">
              <div className="submission-head">
                <span>任务 #{s.task_id}</span>
                <SubmissionBadge status={s.status} />
              </div>
              <div className="content-box">{s.content}</div>
              {s.feedback && <div className="feedback-box"><strong>老师反馈：</strong>{s.feedback}</div>}
              <div className="submission-actions">
                <Link className="btn btn-sm" to={`/tasks/${s.task_id}`}>查看任务</Link>
                {s.status === 'rejected' && (
                  <Link className="btn btn-sm btn-primary" to={`/tasks/${s.task_id}`}>重新提交</Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      <Pagination offset={offset} limit={LIMIT} count={items.length} onChange={setOffset} />
    </div>
  )
}
