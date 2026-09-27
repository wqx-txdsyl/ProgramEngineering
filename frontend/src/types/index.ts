// 与后端接口一一对应的数据类型
export type Role = 'student' | 'teacher'
export type SubmissionStatus = 'pending' | 'approved' | 'rejected'
export type RedemptionStatus = 'active' | 'cancelled'

export interface User {
  id: number
  username: string
  role: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface Task {
  id: number
  title: string
  description: string
}

export interface Submission {
  id: number
  task_id: number
  student_id: number
  content: string
  status: string
  feedback: string
}

export interface Progress {
  submitted_count: number
  approved_count: number
}

export interface PointBalance {
  user_id: number
  balance: number
}

export interface PointTransaction {
  id: number
  user_id: number
  change: number
  source_type: string
  source_id: number
  created_at: string
}

export interface Reward {
  id: number
  name: string
  description: string
  cost: number
  stock: number
  is_active: boolean
}

export interface Redemption {
  id: number
  user_id: number
  reward_id: number
  cost: number
  status: string
  request_key: string
  created_at: string
}
