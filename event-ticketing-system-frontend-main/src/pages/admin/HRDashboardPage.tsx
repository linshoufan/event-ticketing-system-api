import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import PageTransition from "../../components/PageTransition"
import { StatCardSkeleton } from "../../components/Skeleton"
import { APP_CONFIG } from "../../config/app.config"

const MOCK_HR_STATS = [
  {
    eventId: "ev_001",
    eventName: "夏日烤肉趴",
    ticketLimit: 50,
    totalConfirmed: 38,
    totalWaitlist: 5,
    totalCancelled: 4,
    totalCheckedIn: 20,
  },
  {
    eventId: "ev_002",
    eventName: "音樂欣賞之夜",
    ticketLimit: null,
    totalConfirmed: 120,
    totalWaitlist: 0,
    totalCancelled: 10,
    totalCheckedIn: 98,
  },
  {
    eventId: "ev_003",
    eventName: "家庭日活動",
    ticketLimit: 100,
    totalConfirmed: 100,
    totalWaitlist: 15,
    totalCancelled: 8,
    totalCheckedIn: 0,
  },
]

function StatBar({ value, total, color }: { value: number; total: number; color: string }) {
  const pct = total > 0 ? Math.min(Math.round((value / total) * 100), 100) : 0
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-zinc-500 w-8 text-right">{pct}%</span>
    </div>
  )
}

function HRDashboardPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<typeof MOCK_HR_STATS>([])
  const [search, setSearch] = useState("")

  useEffect(() => {
    setTimeout(() => {
      setStats(MOCK_HR_STATS)
      setLoading(false)
    }, APP_CONFIG.development.mockDelayMs)
  }, [])

  const totalEvents = stats.length
  const totalConfirmed = stats.reduce((sum, s) => sum + s.totalConfirmed, 0)
  const totalCheckedIn = stats.reduce((sum, s) => sum + s.totalCheckedIn, 0)
  const avgCheckinRate = totalConfirmed > 0
    ? Math.round((totalCheckedIn / totalConfirmed) * 100)
    : 0

  const filtered = stats.filter(s => s.eventName.includes(search))

  return (
    <PageTransition>
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-white mb-6">統計報表</h1>

        <div className="grid grid-cols-4 gap-3 mb-8">
          {[
            { label: "活動總數", value: totalEvents, color: "text-white" },
            { label: "總報名人數", value: totalConfirmed, color: "text-emerald-400" },
            { label: "總出席人數", value: totalCheckedIn, color: "text-blue-400" },
            { label: "平均出席率", value: `${avgCheckinRate}%`, color: "text-amber-400" },
          ].map(item => (
            <div key={item.label} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4">
              <p className="text-zinc-500 text-xs mb-1">{item.label}</p>
              <p className={`text-2xl font-bold ${item.color}`}>{item.value}</p>
            </div>
          ))}
        </div>

        <input
          placeholder="搜尋活動..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-2.5 text-white text-sm placeholder-zinc-500 focus:outline-none focus:border-zinc-600 mb-4"
        />

        {loading ? (
          <div className="flex flex-col gap-3">
            {[1, 2, 3].map(i => <StatCardSkeleton key={i} />)}
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {filtered.map(stat => {
              const cap = stat.ticketLimit ?? stat.totalConfirmed

              const waitlistColor = stat.ticketLimit && stat.totalWaitlist > stat.ticketLimit
                ? "text-red-400"
                : "text-amber-400"

              const cancelRate = stat.totalConfirmed > 0
                ? stat.totalCancelled / stat.totalConfirmed
                : 0
              const cancelColor = cancelRate > 0.25
                ? "text-red-400"
                : cancelRate < 0.05
                ? "text-emerald-400"
                : "text-zinc-500"

              const checkinRate = stat.totalConfirmed > 0
                ? stat.totalCheckedIn / stat.totalConfirmed
                : 0
              const checkinColor = checkinRate >= 0.95
                ? "text-emerald-400"
                : checkinRate < 0.5
                ? "text-red-400"
                : "text-blue-400"

              const confirmedColor = cap > 0 && stat.totalConfirmed / cap < 0.5
                ? "text-red-400"
                : "text-emerald-400"

              return (
                <div key={stat.eventId} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-white font-semibold">{stat.eventName}</h2>
                    <button
                      onClick={() => navigate(`/admin/events/${stat.eventId}/registrations`)}
                      className="text-xs px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors"
                    >
                      詳細名單
                    </button>
                  </div>

                  <div className="grid grid-cols-4 gap-4 mb-4">
                    {[
                      { label: "正取", value: stat.totalConfirmed, color: confirmedColor },
                      { label: "候補", value: stat.totalWaitlist,  color: waitlistColor },
                      { label: "取消", value: stat.totalCancelled, color: cancelColor },
                      { label: "出席", value: stat.totalCheckedIn, color: checkinColor },
                    ].map(item => (
                      <div key={item.label}>
                        <p className="text-zinc-500 text-xs mb-0.5">{item.label}</p>
                        <p className={`text-xl font-bold ${item.color}`}>{item.value}</p>
                      </div>
                    ))}
                  </div>

                  <div className="flex flex-col gap-2">
                    <div>
                      <div className="flex justify-between text-xs text-zinc-500 mb-1">
                        <span>報名率</span>
                        <span>{stat.totalConfirmed} / {cap} 人</span>
                      </div>
                      <StatBar value={stat.totalConfirmed} total={cap} color="bg-emerald-500" />
                    </div>
                    <div>
                      <div className="flex justify-between text-xs text-zinc-500 mb-1">
                        <span>出席率</span>
                        <span>{stat.totalCheckedIn} / {stat.totalConfirmed} 人</span>
                      </div>
                      <StatBar
                        value={stat.totalCheckedIn}
                        total={stat.totalConfirmed}
                        color={checkinRate >= 0.95 ? "bg-emerald-500" : checkinRate < 0.5 ? "bg-red-500" : "bg-blue-500"}
                      />
                    </div>
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

export default HRDashboardPage