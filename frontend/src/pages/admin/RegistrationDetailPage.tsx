import { useState, useEffect } from "react"
import { useParams } from "react-router-dom"
import { getEventRegistrations } from "../../api/events"
import PageTransition from "../../components/PageTransition"

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  confirmed: { label: "正取", color: "text-emerald-400", bg: "bg-emerald-900/30" },
  waitlist:  { label: "候補", color: "text-amber-400",   bg: "bg-amber-900/30" },
  cancelled: { label: "取消", color: "text-zinc-500",    bg: "bg-zinc-800" },
}

function getDietLabel(diet: string | null) {
  if (!diet) return "無需求"
  return diet === "veg" ? "素食" : "葷食"
}

function RegistrationDetailPage() {
  const { eventId } = useParams<{ eventId: string }>()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState("")

  useEffect(() => {
    if (!eventId) return
    getEventRegistrations(eventId)
      .then(res => {
        setData(res)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [eventId])

  if (loading) return (
    <div className="text-center py-16 text-zinc-500">載入中...</div>
  )

  if (!data) return (
    <div className="text-center py-16 text-zinc-500">載入失敗</div>
  )

  const { summary, registrations } = data
  const filtered = registrations.filter((r: any) => {
    if (statusFilter && r.status !== statusFilter) return false
    return true
  })

  return (
    <PageTransition>
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">報名詳情</h1>

      <div className="grid grid-cols-3 gap-3 mb-6">
        {[
          { label: "正取",   value: summary.totalConfirmed, color: "text-emerald-400" },
          { label: "候補",   value: summary.totalWaitlist,  color: "text-amber-400" },
          { label: "已取消", value: summary.totalCancelled, color: "text-zinc-500" },
        ].map(item => (
          <div key={item.label} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 text-center">
            <p className="text-zinc-500 text-xs mb-1">{item.label}</p>
            <p className={`text-3xl font-bold ${item.color}`}>{item.value}</p>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between mb-4">
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="bg-zinc-900 border border-zinc-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-zinc-600"
        >
          <option value="">所有狀態</option>
          <option value="confirmed">正取</option>
          <option value="waitlist">候補</option>
          <option value="cancelled">已取消</option>
        </select>
        <span className="text-zinc-500 text-sm">{filtered.length} 筆</span>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden">
        {filtered.length === 0 ? (
          <div className="text-center py-12 text-zinc-500">沒有報名紀錄</div>
        ) : (
          <div className="divide-y divide-zinc-800">
            {filtered.map((reg: any) => {
              const config = STATUS_CONFIG[reg.status] ?? STATUS_CONFIG.cancelled
              return (
                <div key={reg.transactionId} className="flex items-center gap-4 px-5 py-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium">{reg.username}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-zinc-500">
                      <span>{getDietLabel(reg.dietType)}</span>
                      <span>開車：{reg.selfDriving ? "是" : "否"}</span>
                      {reg.guestCount > 0 && <span>家屬 {reg.guestCount} 人</span>}
                    </div>
                  </div>
                  <span className={`text-xs font-medium px-3 py-1 rounded-full flex-shrink-0 ${config.bg} ${config.color}`}>
                    {config.label}
                  </span>
                  <span className="text-zinc-600 text-xs flex-shrink-0">
                    {new Date(reg.registeredAt).toLocaleDateString("zh-TW")}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
    </PageTransition>
  )
}

export default RegistrationDetailPage