import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { getEvents, deleteEvent, updateEvent } from "../../api/events"
import type { Event } from "../../types"
import PageTransition from "../../components/PageTransition"
import { EventRowSkeleton } from "../../components/Skeleton"

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  not_open:    { label: "尚未開始報名", color: "text-zinc-400",   bg: "bg-zinc-800" },
  registering: { label: "報名中",       color: "text-emerald-400", bg: "bg-emerald-900/30" },
  waitlist:    { label: "候補登記",     color: "text-amber-400",   bg: "bg-amber-900/30" },
  closed:      { label: "報名截止",     color: "text-red-400",     bg: "bg-red-900/30" },
  ended:       { label: "活動結束",     color: "text-zinc-500",    bg: "bg-zinc-800" },
}

function EventManagePage() {
  const navigate = useNavigate()
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getEvents()
      .then(res => {
        setEvents(res.data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  async function handleDelete(eventId: string) {
    if (!confirm("確定要刪除這個活動嗎？")) return
    try {
      await deleteEvent(eventId)
      setEvents(prev => prev.filter(e => e.eventId !== eventId))
    } catch {
      alert("刪除失敗，請稍後再試")
    }
  }

  async function handlePublish(eventId: string) {
    try {
      await updateEvent(eventId, { isDraft: false })
      setEvents(prev =>
        prev.map(e => e.eventId === eventId ? { ...e, isDraft: false } : e)
      )
    } catch {
      alert("發布失敗，請稍後再試")
    }
  }

  return (
    <PageTransition>
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-white">活動管理</h1>
          <div className="flex gap-2">
            <button
              onClick={() => navigate("/admin/events/new")}
              className="px-4 py-2 rounded-xl bg-white hover:bg-zinc-100 text-zinc-900 text-sm font-semibold transition-colors"
            >
              + 新增活動
            </button>
            <button
              onClick={() => navigate("/admin/users")}
              className="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-white text-sm font-medium transition-colors"
            >
              使用者管理
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex flex-col gap-3">
            {[1, 2, 3].map(i => <EventRowSkeleton key={i} />)}
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-16 text-zinc-500">
            <p className="text-4xl mb-3">📅</p>
            <p>沒有活動</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {events.map(event => {
              const config = STATUS_CONFIG[event.status] ?? { label: event.status, color: "text-zinc-400", bg: "bg-zinc-800" }
              return (
                <div
                  key={event.eventId}
                  className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 flex items-center gap-4"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h2 className="text-white font-semibold truncate">{event.name}</h2>
                      {event.isDraft && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-amber-900/30 text-amber-400 flex-shrink-0">
                          草稿
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-sm text-zinc-500">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${config.bg} ${config.color}`}>
                        {config.label}
                      </span>
                      <span>截止：{event.registrationEnd ? new Date(event.registrationEnd).toLocaleDateString("zh-TW") : "-"}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    {event.isDraft && (
                      <button
                        onClick={() => handlePublish(event.eventId)}
                        className="px-3 py-1.5 rounded-lg bg-emerald-900/30 hover:bg-emerald-900/50 text-emerald-400 text-xs font-medium transition-colors"
                      >
                        發布
                      </button>
                    )}
                    <button
                      onClick={() => navigate(`/admin/events/${event.eventId}/registrations`)}
                      className="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-medium transition-colors"
                    >
                      報名詳情
                    </button>
                    <button
                      onClick={() => navigate(`/admin/events/${event.eventId}/checkin`)}
                      className="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-medium transition-colors"
                    >
                      核銷
                    </button>
                    <button
                      onClick={() => handleDelete(event.eventId)}
                      className="px-3 py-1.5 rounded-lg bg-red-900/30 hover:bg-red-900/50 text-red-400 text-xs font-medium transition-colors"
                    >
                      刪除
                    </button>
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

export default EventManagePage