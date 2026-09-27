import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import TaskList from './pages/TaskList'
import TaskDetail from './pages/TaskDetail'
import MySubmissions from './pages/MySubmissions'
import Review from './pages/Review'
import Points from './pages/Points'
import Rewards from './pages/Rewards'
import MyRedemptions from './pages/MyRedemptions'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          {/* 登录后才能进的区域：Layout 提供顶部导航，页面渲染在 <Outlet /> 里 */}
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/tasks" element={<TaskList />} />
            <Route path="/tasks/:id" element={<TaskDetail />} />
            <Route path="/my-submissions" element={<ProtectedRoute roles={['student']}><MySubmissions /></ProtectedRoute>} />
            <Route path="/points" element={<ProtectedRoute roles={['student']}><Points /></ProtectedRoute>} />
            <Route path="/rewards" element={<Rewards />} />
            <Route path="/my-redemptions" element={<ProtectedRoute roles={['student']}><MyRedemptions /></ProtectedRoute>} />
            <Route path="/review" element={<ProtectedRoute roles={['teacher']}><Review /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
