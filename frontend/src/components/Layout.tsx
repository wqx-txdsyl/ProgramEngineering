import { Link, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function Layout() {
  const { user, logout } = useAuth()
  const isTeacher = user?.role === 'teacher'
  const isStudent = user?.role === 'student'

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-inner">
          <Link to="/" className="logo">学习协作平台</Link>
          <nav className="nav">
            <Link to="/tasks">任务</Link>
            {isStudent && <Link to="/my-submissions">我的成果</Link>}
            {isStudent && <Link to="/points">积分</Link>}
            {isStudent && <Link to="/rewards">奖励商店</Link>}
            {isStudent && <Link to="/my-redemptions">我的兑换</Link>}
            {isTeacher && <Link to="/review">待审核</Link>}
          </nav>
          <div className="user">
            <span>{user?.username}（{isTeacher ? '教师' : '学生'}）</span>
            <button className="btn btn-ghost" onClick={logout}>退出</button>
          </div>
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
