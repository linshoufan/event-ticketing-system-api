import { useState, useEffect } from "react"
import { useParams } from "react-router-dom"
import { getTicketById, checkin } from "../api/tickets"
import type { Ticket, TicketStatus } from "../types"
import PageTransition from "../components/PageTransition"

const STATUS_CONFIG: Record<TicketStatus, { label: string; color: string; bg: string }> = {
  unused:  { label: "可報到", color: "text-emerald-400", bg: "bg-emerald-900/30" },
  used:    { label: "已報到", color: "text-zinc-500",    bg: "bg-zinc-800" },
  invalid: { label: "未開放", color: "text-zinc-500",    bg: "bg-zinc-800" },
}

function TicketDetailPage() {
  const { ticketId } = useParams<{ ticketId: string }>()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [loading, setLoading] = useState(true)
  const [checkingIn, setCheckingIn] = useState(false)
  const [message, setMessage] = useState("")

  useEffect(() => {
    if (!ticketId) return
    getTicketById(ticketId)
      .then(data => {
        setTicket(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [ticketId])

  async function handleCheckin() {
    if (!ticketId) return
    setCheckingIn(true)
    setMessage("")

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          await checkin(ticketId, {
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
          })
          setMessage("報到成功！")
          if (ticket) setTicket({ ...ticket, status: "used", checkinAvailable: false })
        } catch (err: any) {
          setMessage(err?.message ?? "報到失敗，請稍後再試")
        } finally {
          setCheckingIn(false)
        }
      },
      () => {
        setMessage("無法取得您的位置，請確認已開啟定位權限")
        setCheckingIn(false)
      }
    )
  }

  if (loading) return (
    <div className="text-center py-16 text-zinc-500">載入中...</div>
  )

  if (!ticket) return (
    <div className="text-center py-16 text-zinc-500">找不到票券</div>
  )

  const config = STATUS_CONFIG[ticket.status]

  return (
    <PageTransition>
    <div className="max-w-md mx-auto px-4 py-8">
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden">

        <div className="p-8 text-center border-b border-zinc-800">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-zinc-800 text-3xl mb-4">
            🎫
          </div>
          <h1 className="text-xl font-bold text-white mb-1">{ticket.eventName}</h1>
          <p className="text-zinc-400 text-sm flex items-center justify-center gap-1">
            <span>📍</span>{ticket.eventLocation}
          </p>
          <div className="mt-4">
            <span className={`text-sm font-medium px-4 py-1.5 rounded-full ${config.bg} ${config.color}`}>
              {config.label}
            </span>
          </div>
        </div>

        <div className="p-6 flex flex-col gap-3 border-b border-zinc-800">
          <div className="flex items-center justify-between text-sm">
            <span className="text-zinc-500">活動開始</span>
            <span className="text-white">{new Date(ticket.eventStartTime).toLocaleString("zh-TW")}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-zinc-500">活動結束</span>
            <span className="text-white">{new Date(ticket.eventEndTime).toLocaleString("zh-TW")}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-zinc-500">票券編號</span>
            <span className="text-zinc-400 font-mono text-xs">{ticket.ticketId}</span>
          </div>
        </div>

        <div className="p-6">
          {ticket.checkinAvailable ? (
            <button
              onClick={handleCheckin}
              disabled={checkingIn}
              className="w-full py-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-lg transition-colors flex items-center justify-center gap-2"
            >
              {checkingIn ? (
                <><span className="animate-spin">⏳</span>定位中...</>
              ) : (
                <><span>📍</span>報到</>
              )}
            </button>
          ) : (
            <button
              disabled
              className="w-full py-4 rounded-xl bg-zinc-800 text-zinc-500 font-bold text-lg cursor-not-allowed"
            >
              {ticket.status === "used" ? "✓ 已報到" : "尚未開放報到"}
            </button>
          )}

          {message && (
            <div className={`mt-4 px-4 py-3 rounded-xl text-sm text-center ${
              message.includes("成功")
                ? "bg-emerald-900/30 border border-emerald-800 text-emerald-400"
                : "bg-red-900/30 border border-red-800 text-red-400"
            }`}>
              {message}
            </div>
          )}
        </div>
      </div>
    </div>
    </PageTransition>
  )
}

export default TicketDetailPage