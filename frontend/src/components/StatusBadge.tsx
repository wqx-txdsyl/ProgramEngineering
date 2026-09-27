export function SubmissionBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已退回',
  }
  return <span className={`badge badge-${status}`}>{map[status] ?? status}</span>
}

export function RedemptionBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    active: '有效',
    cancelled: '已取消',
  }
  return <span className={`badge badge-${status}`}>{map[status] ?? status}</span>
}
