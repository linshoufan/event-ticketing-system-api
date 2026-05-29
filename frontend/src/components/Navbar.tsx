import { useState } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { removeToken } from "../api/auth"

function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()
  const role = localStorage.getItem("role")
  const [leaving, setLeaving] = useState(false)

  if (!role) return null

  function handleLogout() {
    setLeaving(true)
    setTimeout(() => {
      removeToken()
      localStorage.removeItem("role")
      navigate("/")
    }, 400)
  }

  function isActive(path: string) {
    return location.pathname.startsWith(path)
  }

  const mainPages = ["/events", "/admin/events", "/admin/hr", "/my-transactions", "/my-tickets", "/profile", "/admin/users"]
  const isMainPage = mainPages.some(p => location.pathname === p)

  const linkClass = (path: string) =>
    `px-2 sm:px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-colors cursor-pointer whitespace-nowrap ${
      isActive(path)
        ? "bg-zinc-700 text-white"
        : "text-zinc-400 hover:text-white hover:bg-zinc-800"
    }`

  return (
    <nav className={`sticky top-0 z-50 bg-zinc-950/80 backdrop-blur border-b border-zinc-800 transition-all duration-400 ${leaving ? "opacity-0 -translate-y-2" : "opacity-100 translate-y-0"}`}>
      <div className="max-w-6xl mx-auto px-3 sm:px-4 h-12 sm:h-14 flex items-center justify-between gap-2">

        <div className="flex items-center gap-2 flex-shrink-0">
          {!isMainPage && (
            <button
              onClick={() => window.history.back()}
              className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors flex items-center justify-center text-sm"
            >
              ←
            </button>
          )}
          <span className="text-white font-semibold text-xs sm:text-sm whitespace-nowrap">
            企業活動訂票系統
          </span>
        </div>

        <div className="flex items-center gap-0.5 sm:gap-1 overflow-x-auto no-scrollbar">
          {role === "employee" && (
            <>
              <span className={linkClass("/events")} onClick={() => navigate("/events")}>活動</span>
              <span className={linkClass("/my-transactions")} onClick={() => navigate("/my-transactions")}>報名</span>
              <span className={linkClass("/my-tickets")} onClick={() => navigate("/my-tickets")}>票券</span>
            </>
          )}
          {role === "welfare_member" && (
            <>
              <span className={linkClass("/admin/events")} onClick={() => navigate("/admin/events")}>活動管理</span>
              <span className={linkClass("/admin/users")} onClick={() => navigate("/admin/users")}>使用者</span>
            </>
          )}
          {role === "hr" && (
            <>
              <span className={linkClass("/events")} onClick={() => navigate("/events")}>活動</span>
              <span className={linkClass("/admin/hr")} onClick={() => navigate("/admin/hr")}>統計</span>
            </>
          )}
          <span className={linkClass("/profile")} onClick={() => navigate("/profile")}>個人</span>
          <button
            onClick={handleLogout}
            className="ml-1 px-2 sm:px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium text-zinc-400 hover:text-white border border-zinc-700 hover:border-zinc-500 transition-colors whitespace-nowrap"
          >
            登出
          </button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar