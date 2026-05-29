import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { getTickets } from "../api/tickets"
import type { Ticket, TicketStatus } from "../types"
import PageTransition from "../components/PageTransition"
import { TicketCardSkeleton } from "../components/Skeleton"

const STATUS_CONFIG: Record<TicketStatus, { label: string; color: string; bg: string; dot: string }> = {
  unused:  { label: "可報到", color: "text-emerald-400", bg: "bg-emerald-900/30", dot: "bg-emerald-400" },
  used:    { label: "已報到", color: "text-zinc-500",    bg: "bg-zinc-800",       dot: "bg-zinc-500" },
  invalid: { label: "未開放", color: "text-zinc-500",    bg: "bg-zinc-800",       dot: "bg-zinc-600" },
}

function MyTicketsPage() {
  const navigate = useNavigate()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<TicketStatus | "">("")

  useEffect(() => {
    setLoading(true)
    getTickets(filter ? { status: filter } : undefined)
      .then(data => {
        setTickets(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [filter])

  return (
    <PageTransition>
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-white">我的票券</h1>
          <select
            value={filter}
            onChange={e => setFilter(e.target.value as TicketStatus | "")}
            className="bg-zinc-900 border border-zinc-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-zinc-600"
          >
            <option value="">所有票券</option>
            <option value="unused">可報到</option>
            <option value="used">已報到</option>
            <option value="invalid">未開放</option>
          </select>
        </div>

        {loading ? (
          <div className="flex flex-col gap-3">
            {[1, 2, 3].map(i => <TicketCardSkeleton key={i} />)}
          </div>
        ) : tickets.length === 0 ? (
          <div className="text-center py-16 text-zinc-500">
            <p className="text-4xl mb-3">🎫</p>
            <p>沒有票券</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {tickets.map((ticket: Ticket) => {
              const config = STATUS_CONFIG[ticket.status]
              return (
                <div
                  key={ticket.ticketId}
                  onClick={() => navigate(`/my-tickets/${ticket.ticketId}`)}
                  className={`
                    bg-zinc-900 border border-zinc-800 rounded-2xl p-5 cursor-pointer
                    transition-all duration-200 hover:border-zinc-600 hover:bg-zinc-800/80
                    ${ticket.status !== "unused" ? "opacity-50" : ""}
                  `}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${config.dot}`} />
                        <h2 className="text-white font-semibold truncate">{ticket.eventName}</h2>
                      </div>
                      <p className="text-zinc-400 text-sm flex items-center gap-1 mt-1">
                        <span>📍</span>{ticket.eventLocation}
                      </p>
                      <p className="text-zinc-500 text-sm flex items-center gap-1 mt-1">
                        <span>🕐</span>{new Date(ticket.eventStartTime).toLocaleString("zh-TW")}
                      </p>
                      {ticket.checkinAvailable && (
                        <p className="text-emerald-400 text-sm font-medium mt-3">
                          點擊進入報到
                        </p>
                      )}
                    </div>
                    <span className={`text-xs font-medium px-3 py-1 rounded-full flex-shrink-0 ${config.bg} ${config.color}`}>
                      {config.label}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </PageTransition>
  )
}

export default MyTicketsPage