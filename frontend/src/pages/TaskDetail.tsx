import { useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, getErrorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { SubmissionBadge } from '../components/StatusBadge'
import type { Submission, Task } from '../types'

export default function TaskDetail() {
  const { id } = useParams()
  const taskId = Number(id)
  const { user } = useAuth()
  const isTeacher = user?.role === 'teacher'
  const isStudent = user?.role === 'student'

  const [task, setTask] = useState<Task | null>(null)
  const [submission, setSubmission] = useState<Submission | null>(null)
  const [content, setContent] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)

  // 教师编辑
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')

  async function load() {
    setLoading(true)
    setError('')
    try {
      const t = await api.get<Task>(`/tasks/${taskId}`)
      setTask(t)
      setTitle(t.title)
      setDescription(t.description)
      if (isStudent) {
        const mine = await api.get<Submission[]>('/submissions/mine', { params: { limit: 100 } })
        const found = mine.find((s) => s.task_id === taskId) ?? null
        setSubmission(found)
        if (found) setContent(found.content)
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId, isStudent])

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    try {
      const s = await api.post<Submission>('/submissions', { task_id: taskId, content })
      setSubmission(s)
      setSuccess('提交成功，等待老师审核')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function resubmit(e: FormEvent) {
    e.preventDefault()
    if (!submission) return
    setError('')
    setSuccess('')
    try {
      const s = await api.put<Submission>(`/submissions/${submission.id}`, { content })
      setSubmission(s)
      setSuccess('已重新提交，恢复待审核状态')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function saveTitle() {
    setError('')
    setSuccess('')
    try {
      const t = await api.patch<Task>(`/tasks/${taskId}`, { title })
      setTask(t)
      setSuccess('标题已更新')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function saveDescription() {
    setError('')
    setSuccess('')
    try {
      const t = await api.patch<Task>(`/tasks/${taskId}/description`, { description })
      setTask(t)
      setSuccess('描述已更新')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  if (loading) return <div className="page"><p className="empty">加载中…</p></div>
  if (!task) return <div className="page"><p className="empty">任务不存在或已删除</p></div>

  return (
    <div className="page">
      <Link to="/tasks" className="back">← 返回任务列表</Link>
      <div className="card">
        <h1>{task.title}</h1>
        <p className="muted">{task.description || '（无描述）'}</p>
      </div>

      {isTeacher && (
        <div className="card form">
          <h2>编辑任务（教师）</h2>
          <label>标题<input value={title} onChange={(e) => setTitle(e.target.value)} maxLength={100} /></label>
          <button className="btn" onClick={saveTitle} disabled={!title.trim()}>保存标题</button>
          <label>描述<textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} maxLength={2000} /></label>
          <button className="btn" onClick={saveDescription} disabled={!description.trim()}>保存描述</button>
        </div>
      )}

      {isStudent && !submission && (
        <form className="card form" onSubmit={submit}>
          <h2>提交成果</h2>
          <label>
            内容
            <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={5} required maxLength={2000} placeholder="写下你的学习成果" />
          </label>
          {error && <p className="error">{error}</p>}
          {success && <p className="success">{success}</p>}
          <button className="btn btn-primary" type="submit" disabled={!content.trim()}>提交</button>
        </form>
      )}

      {isStudent && submission && (
        <div className="card">
          <h2>我的提交 <SubmissionBadge status={submission.status} /></h2>
          <div className="content-box">{submission.content}</div>
          {submission.feedback && (
            <div className="feedback-box"><strong>老师反馈：</strong>{submission.feedback}</div>
          )}
          {submission.status === 'rejected' && (
            <form className="form" onSubmit={resubmit}>
              <label>
                修改后重新提交
                <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={5} required maxLength={2000} />
              </label>
              {error && <p className="error">{error}</p>}
              {success && <p className="success">{success}</p>}
              <button className="btn btn-primary" type="submit" disabled={!content.trim()}>重新提交</button>
            </form>
          )}
        </div>
      )}
      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}
    </div>
  )
}
