import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import type { Progress, PointBalance } from '../types'

export default function Dashboard() {
  const { user } = useAuth()
  const [progress, setProgress] = useState<Progress | null>(null)
  const [points, setPoints] = useState<PointBalance | null>(null)

  useEffect(() => {
    if (user?.role !== 'student') return
    api.get<Progress>('/submissions/me').then(setProgress).catch(() => {})
    api.get<PointBalance>('/points/me').then(setPoints).catch(() => {})
  }, [user?.role])

  if (user?.role === 'teacher') {
    return (
      <div className="page">
        <h1>欢迎，{user.username}（教师）</h1>
        <p className="muted">你可以发布任务、审核学生的成果。</p>
        <div className="actions">
          <Link className="btn btn-primary" to="/tasks">管理任务</Link>
          <Link className="btn" to="/review">查看待审核</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <h1>欢迎，{user?.username}（学生）</h1>
      <div className="stat-grid">
        <div className="card stat">
          <div className="stat-num">{progress?.submitted_count ?? 0}</div>
          <div className="stat-label">提交总数</div>
        </div>
        <div className="card stat">
          <div className="stat-num">{progress?.approved_count ?? 0}</div>
          <div className="stat-label">审核通过</div>
        </div>
        <div className="card stat">
          <div className="stat-num">{points?.balance ?? 0}</div>
          <div className="stat-label">积分余额</div>
        </div>
      </div>
      <div className="actions">
        <Link className="btn btn-primary" to="/tasks">去做任务</Link>
        <Link className="btn" to="/rewards">去兑换奖励</Link>
      </div>
    </div>
  )
}
