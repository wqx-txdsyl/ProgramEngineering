export default function Pagination({ offset, limit, count, onChange }: {
  offset: number
  limit: number
  count: number
  onChange: (next: number) => void
}) {
  return (
    <div className="pagination">
      <button className="btn" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - limit))}>
        上一页
      </button>
      <span>第 {Math.floor(offset / limit) + 1} 页</span>
      <button className="btn" disabled={count < limit} onClick={() => onChange(offset + limit)}>
        下一页
      </button>
    </div>
  )
}
