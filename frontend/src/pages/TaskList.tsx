import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api, getErrorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import Pagination from '../components/Pagination'
import type { Task } from '../types'

const LIMIT = 20

export default function TaskList() {
  const { user } = useAuth()
  const isTeacher = user?.role === 'teacher'

  const [tasks, setTasks] = useState<Task[]>([])
  const [offset, setOffset] = useState(0)
  const [version, setVersion] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [showCreate, setShowCreate] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    api.get<Task[]>('/tasks', { params: { offset, limit: LIMIT } })
      .then(setTasks)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false))
  }, [offset, version])

  async function createTask(e: FormEvent) {
    e.preventDefault()
    setError('')
    try {
      await api.post<Task>('/tasks', { title, description })
      setShowCreate(false)
      setTitle('')
      setDescription('')
      setOffset(0)
      setVersion((v) => v + 1)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="page">
      <div className="page-head">
        <h1>学习任务</h1>
        {isTeacher && (
          <button className="btn btn-primary" onClick={() => setShowCreate((v) => !v)}>新建任务</button>
        )}
      </div>

      {isTeacher && showCreate && (
        <form className="card form" onSubmit={createTask}>
          <label>标题<input value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={100} /></label>
          <label>描述<textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} maxLength={2000} /></label>
          {error && <p className="error">{error}</p>}
          <div className="actions">
            <button className="btn btn-primary" type="submit" disabled={!title.trim()}>发布</button>
            <button className="btn" type="button" onClick={() => setShowCreate(false)}>取消</button>
          </div>
        </form>
      )}

      {loading ? (
        <p className="empty">加载中…</p>
      ) : tasks.length === 0 ? (
        <p className="empty">还没有任务</p>
      ) : (
        <div className="list">
          {tasks.map((t) => (
            <Link key={t.id} to={`/tasks/${t.id}`} className="card task-card">
              <div className="task-title">{t.title}</div>
              <div className="muted task-desc">{t.description || '（无描述）'}</div>
            </Link>
          ))}
        </div>
      )}
      <Pagination offset={offset} limit={LIMIT} count={tasks.length} onChange={setOffset} />
    </div>
  )
}
