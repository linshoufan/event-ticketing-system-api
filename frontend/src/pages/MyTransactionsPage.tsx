import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { getTransactions, cancelTransaction } from "../api/transactions"
import type { Transaction } from "../types"
import PageTransition from "../components/PageTransition"
import { TransactionCardSkeleton } from "../components/Skeleton"
import Toast from "../components/Toast"
import { useToast } from "../hooks/useToast"

type TransactionStatus = "confirmed" | "waitlist" | "cancelled"

const STATUS_CONFIG: Record<TransactionStatus, { label: string; color: string; bg: string; dot: string }> = {
  confirmed: { label: "正取",   color: "text-emerald-400", bg: "bg-emerald-900/30", dot: "bg-emerald-400" },
  waitlist:  { label: "候補",   color: "text-amber-400",   bg: "bg-amber-900/30",   dot: "bg-amber-400" },
  cancelled: { label: "已取消", color: "text-zinc-500",    bg: "bg-zinc-800",       dot: "bg-zinc-600" },
}

function getDietLabel(diet: string | null) {
  if (!diet) return "無需求"
  const map: Record<string, string> = { veg: "素食", "non-veg": "葷食" }
  return map[diet] ?? diet
}

function MyTransactionsPage() {
  const navigate = useNavigate()
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<TransactionStatus | "">("")
  const { toast, showToast } = useToast()

  useEffect(() => {
    setLoading(true)
    getTransactions(statusFilter ? { status: statusFilter } : undefined)
      .then(res => {
        setTransactions(res.data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [statusFilter])

  async function handleCancel(transactionId: string) {
    try {
      await cancelTransaction(transactionId)
      setTransactions(prev => prev.filter(tx => tx.transactionId !== transactionId))
      showToast("取消報名成功", "success")
    } catch {
      showToast("取消失敗，請稍後再試", "error")
    }
  }

  return (
    <PageTransition>
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-white">我的報名紀錄</h1>
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value as TransactionStatus | "")}
            className="bg-zinc-900 border border-zinc-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-zinc-600"
          >
            <option value="">所有狀態</option>
            <option value="confirmed">正取</option>
            <option value="waitlist">候補</option>
            <option value="cancelled">已取消</option>
          </select>
        </div>

        {loading ? (
          <div className="flex flex-col gap-3">
            {[1, 2, 3].map(i => <TransactionCardSkeleton key={i} />)}
          </div>
        ) : transactions.length === 0 ? (
          <div className="text-center py-16 text-zinc-500">
            <p className="text-4xl mb-3">📋</p>
            <p>沒有報名紀錄</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {transactions.map(t => {
              const config = STATUS_CONFIG[t.status as TransactionStatus]
              return (
                <div
                  key={t.transactionId}
                  className={`bg-zinc-900 border border-zinc-800 rounded-2xl p-5 transition-all ${t.status === "cancelled" ? "opacity-50" : ""}`}
                >
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${config.dot}`} />
                      <h2 className="text-white font-semibold">{t.eventName}</h2>
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <span className={`text-xs font-medium px-3 py-1 rounded-full ${config.bg} ${config.color}`}>
                        {config.label}
                        {t.status === "waitlist" && t.waitlistNumber && (
                          <span className="ml-1">（第 {t.waitlistNumber} 號）</span>
                        )}
                      </span>
                    </div>
                  </div>

                  <p className="text-zinc-400 text-sm flex items-center gap-1 mb-3">
                    <span>🕐</span>
                    {new Date(t.eventStartTime).toLocaleString("zh-TW")}
                  </p>

                  <div className="flex gap-4 text-sm text-zinc-500 mb-4">
                    <span>飲食：{getDietLabel(t.dietType)}</span>
                    <span>自行開車：{t.selfDriving ? "是" : "否"}</span>
                    {t.guestCount > 0 && <span>家屬：{t.guestCount} 人</span>}
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-zinc-600 text-xs">
                      報名於 {new Date(t.registeredAt).toLocaleString("zh-TW")}
                    </span>
                    <div className="flex gap-2">
                      {t.ticketId && (
                        <button
                          onClick={() => navigate(`/my-tickets/${t.ticketId}`)}
                          className="text-xs px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors"
                        >
                          查看票券
                        </button>
                      )}
                      {t.status === "confirmed" && (
                        <button
                          onClick={() => handleCancel(t.transactionId)}
                          className="text-xs px-3 py-1.5 rounded-lg bg-red-900/30 hover:bg-red-900/50 text-red-400 transition-colors"
                        >
                          取消報名
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
      <Toast message={toast.message} type={toast.type} visible={toast.visible} />
    </PageTransition>
  )
}

export default MyTransactionsPage