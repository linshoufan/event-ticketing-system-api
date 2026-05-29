import { useState, useEffect } from "react"
import { useParams } from "react-router-dom"
import { getEventTickets } from "../../api/tickets"
import PageTransition from "../../components/PageTransition"

interface TicketRecord {
  ticketId: string
  userId: string
  username: string
  status: "used" | "unused" | "invalid"
}

const STATUS_CONFIG = {
  unused:  { label: "未核銷", color: "text-emerald-400", bg: "bg-emerald-900/30" },
  used:    { label: "已核銷", color: "text-zinc-500",    bg: "bg-zinc-800" },
  invalid: { label: "無效",   color: "text-red-400",     bg: "bg-red-900/30" },
}

function CheckinPage() {
  const { eventId } = useParams<{ eventId: string }>()
  const [tickets, setTickets] = useState<TicketRecord[]>([])
  const [summary, setSummary] = useState({ used: 0, unused: 0, invalid: 0 })
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")

  useEffect(() => {
    if (!eventId) return
    getEventTickets(eventId)
      .then(res => {
        setTickets(res.data.tickets as TicketRecord[])
        setSummary(res.data.summary)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [eventId])

  const filtered = tickets.filter(t =>
    t.username.toLowerCase().includes(search.toLowerCase()) ||
    t.ticketId.toLowerCase().includes(search.toLowerCase())
  )

  function handleCheckin(ticketId: string) {
    if (!confirm("確定要核銷這張票券嗎？")) return
    setTickets(prev =>
      prev.map(t => t.ticketId === ticketId ? { ...t, status: "used" } : t)
    )
    setSummary(prev => ({ ...prev, used: prev.used + 1, unused: prev.unused - 1 }))
  }

  return (
    <PageTransition>
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">核銷</h1>
      </div>

      {loading ? (
        <div className="text-center py-16 text-zinc-500">載入中...</div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-3 mb-6">
            {[
              { label: "已核銷", value: summary.used,    color: "text-zinc-400" },
              { label: "未核銷", value: summary.unused,  color: "text-emerald-400" },
              { label: "無效",   value: summary.invalid, color: "text-red-400" },
            ].map(item => (
              <div key={item.label} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 text-center">
                <p className="text-zinc-500 text-xs mb-1">{item.label}</p>
                <p className={`text-3xl font-bold ${item.color}`}>{item.value}</p>
              </div>
            ))}
          </div>

          <input
            placeholder="搜尋姓名或票券 ID..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-2.5 text-white text-sm placeholder-zinc-500 focus:outline-none focus:border-zinc-600 mb-4"
          />

          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden">
            {filtered.length === 0 ? (
              <div className="text-center py-12 text-zinc-500">找不到票券</div>
            ) : (
              <div className="divide-y divide-zinc-800">
                {filtered.map(ticket => {
                  const config = STATUS_CONFIG[ticket.status]
                  return (
                    <div key={ticket.ticketId} className="flex items-center gap-4 px-5 py-4">
                      <div className="flex-1 min-w-0">
                        <p className="text-white font-medium">{ticket.username}</p>
                        <p className="text-zinc-500 text-xs font-mono mt-0.5">{ticket.ticketId}</p>
                      </div>
                      <span className={`text-xs font-medium px-3 py-1 rounded-full ${config.bg} ${config.color}`}>
                        {config.label}
                      </span>
                      <div className="w-16 text-right">
                        {ticket.status === "unused" ? (
                          <button
                            onClick={() => handleCheckin(ticket.ticketId)}
                            className="px-3 py-1.5 rounded-lg bg-white hover:bg-zinc-100 text-zinc-900 text-xs font-semibold transition-colors"
                          >
                            核銷
                          </button>
                        ) : (
                          <span className="text-zinc-600 text-xs">
                            {ticket.status === "used" ? "完成" : "無效"}
                          </span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </>
      )}
    </div>
    </PageTransition>
  )
}

export default CheckinPage