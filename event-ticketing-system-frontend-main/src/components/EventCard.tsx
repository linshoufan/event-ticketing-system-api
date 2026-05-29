import type { Event } from "../types"

interface Props {
  event: Event
  onClick: () => void
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  not_open:    { label: "尚未開始報名", color: "text-zinc-400", bg: "bg-zinc-800" },
  registering: { label: "報名中",       color: "text-emerald-400", bg: "bg-emerald-900/30" },
  waitlist:    { label: "候補登記",     color: "text-amber-400", bg: "bg-amber-900/30" },
  closed:      { label: "報名截止",     color: "text-red-400", bg: "bg-red-900/30" },
  ended:       { label: "活動結束",     color: "text-zinc-500", bg: "bg-zinc-800" },
}

const CATEGORY_EMOJI: Record<string, string> = {
  sport:   "🏃",
  food:    "🍽️",
  travel:  "✈️",
  culture: "🎨",
  family:  "👨‍👩‍👧",
  contest: "🏆",
  music:   "🎵",
}

function EventCard({ event, onClick }: Props) {
  const isActive = event.status === "registering"
  const config = STATUS_CONFIG[event.status] ?? { label: event.status, color: "text-zinc-400", bg: "bg-zinc-800" }
  const emoji = CATEGORY_EMOJI[event.category] ?? "📅"

  return (
    <div
      onClick={onClick}
      data-testid="event-card"
      className={`
        group relative bg-zinc-900 border border-zinc-800 rounded-2xl p-5
        cursor-pointer transition-all duration-200
        hover:border-zinc-600 hover:bg-zinc-800/80
        ${!isActive ? "opacity-50" : ""}
      `}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4 flex-1 min-w-0">
          <div className="w-12 h-12 rounded-xl bg-zinc-800 flex items-center justify-center text-2xl flex-shrink-0">
            {emoji}
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-white font-semibold text-lg leading-tight truncate">
              {event.name}
            </h2>
            <p className="text-zinc-400 text-sm mt-1 flex items-center gap-1">
              <span>📍</span>
              {event.location}
            </p>
            <p className="text-zinc-500 text-sm mt-1 flex items-center gap-1">
              <span>🕐</span>
              {new Date(event.eventStartTime).toLocaleString("zh-TW")}
            </p>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 flex-shrink-0">
          <span
            data-testid="event-status"
            className={`text-xs font-medium px-3 py-1 rounded-full ${config.bg} ${config.color}`}
          >
            {config.label}
          </span>
          {event.ticketLimit && (
            <span className="text-xs text-zinc-500">
              剩餘 <span className="text-white font-medium">{event.remainingTickets}</span> / {event.ticketLimit} 位
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

export default EventCard