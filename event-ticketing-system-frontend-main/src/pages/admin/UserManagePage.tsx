import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { MOCK_USERS } from "../../mock/users"
import PageTransition from "../../components/PageTransition"
import { UserRowSkeleton } from "../../components/Skeleton"
import { APP_CONFIG } from "../../config/app.config"

type UserStatus = "active" | "locked"

interface User {
  userId: string
  username: string
  role: string
  registrationStatus: UserStatus
  unlockAt: string | null
}

function UserManagePage() {
  const navigate = useNavigate()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [roleFilter, setRoleFilter] = useState("")
  const [statusFilter, setStatusFilter] = useState("")

  useEffect(() => {
    setTimeout(() => {
      setUsers(MOCK_USERS)
      setLoading(false)
    }, APP_CONFIG.development.mockDelayMs)
  }, [])

  const filtered = users.filter(u => {
    if (roleFilter && u.role !== roleFilter) return false
    if (statusFilter && u.registrationStatus !== statusFilter) return false
    return true
  })

  function handleUnlock(userId: string) {
    if (!confirm("確定要解鎖這個使用者嗎？")) return
    setUsers(prev =>
      prev.map(u =>
        u.userId === userId
          ? { ...u, registrationStatus: "active" as UserStatus, unlockAt: null }
          : u
      )
    )
  }

  function handleChangeRole(userId: string, role: string) {
    setUsers(prev =>
      prev.map(u => u.userId === userId ? { ...u, role } : u)
    )
  }

  function handleDelete(userId: string) {
    if (!confirm("確定要刪除這個使用者嗎？")) return
    setUsers(prev => prev.filter(u => u.userId !== userId))
  }

  return (
    <PageTransition>
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-white">使用者管理</h1>
          <button
            onClick={() => navigate("/admin/events")}
            className="px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-white text-sm font-medium transition-colors"
          >
            活動管理
          </button>
        </div>

        <div className="flex gap-2 mb-6">
          <select
            value={roleFilter}
            onChange={e => setRoleFilter(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-zinc-600"
          >
            <option value="">所有角色</option>
            <option value="welfare_member">福委會</option>
            <option value="employee">一般員工</option>
            <option value="hr">HR</option>
          </select>
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-zinc-600"
          >
            <option value="">所有狀態</option>
            <option value="active">正常</option>
            <option value="locked">鎖定中</option>
          </select>
        </div>

        {loading ? (
          <div className="flex flex-col gap-3">
            {[1, 2, 3].map(i => <UserRowSkeleton key={i} />)}
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16 text-zinc-500">
            <p className="text-4xl mb-3">👥</p>
            <p>沒有使用者</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {filtered.map(user => (
              <div
                key={user.userId}
                className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 flex items-center gap-4"
              >
                <div className="w-10 h-10 rounded-xl bg-zinc-800 flex items-center justify-center text-lg flex-shrink-0">
                  👤
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-white font-medium">{user.username}</p>
                  {user.registrationStatus === "locked" && user.unlockAt && (
                    <p className="text-red-400 text-xs mt-0.5">
                      鎖定中，{new Date(user.unlockAt).toLocaleDateString("zh-TW")} 解鎖
                    </p>
                  )}
                </div>

                <select
                  value={user.role}
                  onChange={e => handleChangeRole(user.userId, e.target.value)}
                  className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-zinc-500"
                >
                  <option value="welfare_member">福委會</option>
                  <option value="employee">一般員工</option>
                  <option value="hr">HR</option>
                </select>

                {user.registrationStatus === "active" ? (
                  <span className="text-xs font-medium px-3 py-1 rounded-full bg-emerald-900/30 text-emerald-400 flex-shrink-0">
                    正常
                  </span>
                ) : (
                  <span className="text-xs font-medium px-3 py-1 rounded-full bg-red-900/30 text-red-400 flex-shrink-0">
                    鎖定中
                  </span>
                )}

                <div className="flex gap-2 flex-shrink-0">
                  {user.registrationStatus === "locked" && (
                    <button
                      onClick={() => handleUnlock(user.userId)}
                      className="px-3 py-1.5 rounded-lg bg-amber-900/30 hover:bg-amber-900/50 text-amber-400 text-xs font-medium transition-colors"
                    >
                      解鎖
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(user.userId)}
                    className="px-3 py-1.5 rounded-lg bg-red-900/30 hover:bg-red-900/50 text-red-400 text-xs font-medium transition-colors"
                  >
                    刪除
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PageTransition>
  )
}

export default UserManagePage