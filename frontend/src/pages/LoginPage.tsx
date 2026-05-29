import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { login, saveToken } from "../api/auth"
import { saveLoginTime } from "../hooks/useAutoLogout"
import { APP_CONFIG } from "../config/app.config"
import photo1 from "../assets/photo1.jpg"
import photo2 from "../assets/photo2.jpg"
import photo3 from "../assets/photo3.jpg"

const photos = [photo1, photo2, photo3]
const { useMock } = APP_CONFIG.development

type LoginType = "first" | "employee" | "welfare_member" | "hr"

const LOGIN_OPTIONS: {
  type: LoginType
  label: string
  sublabel: string
  icon: string
  role: string | null
}[] = [
  {
    type: "employee",
    label: "員工登入",
    sublabel: "瀏覽活動、報名、查看票券",
    icon: "👤",
    role: "employee",
  },
  {
    type: "welfare_member",
    label: "福委登入",
    sublabel: "管理活動、使用者、核銷票券",
    icon: "⚙️",
    role: "welfare_member",
  },
  {
    type: "hr",
    label: "HR 登入",
    sublabel: "查看活動統計與報名數據",
    icon: "📊",
    role: "hr",
  },
  {
    type: "first",
    label: "第一次登入",
    sublabel: "使用員工編號建立帳號",
    icon: "✨",
    role: null,
  },
]

function LoginPage() {
  const navigate = useNavigate()
  const [mounted, setMounted] = useState(false)
  const [leaving, setLeaving] = useState(false)
  const [currentPhoto, setCurrentPhoto] = useState(0)
  const [fadeIn, setFadeIn] = useState(true)

  const [selectedType, setSelectedType] = useState<LoginType | null>(null)
  const [animating, setAnimating] = useState(false)
  const [employeeId, setEmployeeId] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 10)
    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      setFadeIn(false)
      setTimeout(() => {
        setCurrentPhoto(prev => (prev + 1) % photos.length)
        setFadeIn(true)
      }, 1500)
    }, 8000)
    return () => clearInterval(interval)
  }, [])

  function handleSelectType(type: LoginType) {
    setAnimating(true)
    setTimeout(() => {
      setSelectedType(type)
      setEmployeeId("")
      setPassword("")
      setError("")
      setAnimating(false)
    }, 200)
  }

  function handleBack() {
    setAnimating(true)
    setTimeout(() => {
      setSelectedType(null)
      setError("")
      setAnimating(false)
    }, 200)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!employeeId.trim() || !password.trim()) {
      setError("請填寫員工編號和密碼")
      return
    }

    const option = LOGIN_OPTIONS.find(o => o.type === selectedType)!
    setLoading(true)
    setError("")

    try {
      const { token, role } = await login({
        employeeId: employeeId.trim(),
        password,
        role: option.role,
      })

      saveToken(token)
      localStorage.setItem("role", role)
      saveLoginTime()

      setLeaving(true)
      setTimeout(() => {
        if (role === "welfare_member") navigate("/admin/events")
        else if (role === "hr") navigate("/admin/hr")
        else navigate("/events")
      }, 500)
    } catch (err: any) {
      const code = err?.code
      if (code === "INVALID_CREDENTIALS") {
        setError("員工編號或密碼錯誤")
      } else if (code === "ROLE_MISMATCH" || code === "INVALID_ROLE") {
        setError("您的帳號權限不符，請選擇正確的登入方式")
      } else if (code === "EMPLOYEE_NOT_FOUND") {
        setError("找不到此員工編號")
      } else {
        setError("登入失敗，請稍後再試")
      }
    } finally {
      setLoading(false)
    }
  }

  const selectedOption = LOGIN_OPTIONS.find(o => o.type === selectedType)

  return (
    <div className="min-h-screen relative flex items-center justify-center px-4 overflow-hidden">

      <div
        className={`absolute inset-0 bg-cover bg-center transition-opacity duration-1500 ${fadeIn ? "opacity-100" : "opacity-0"}`}
        style={{ backgroundImage: `url(${photos[currentPhoto]})` }}
      />
      <div className="absolute inset-0 bg-zinc-950/80" />

      <div className={`relative z-10 w-full max-w-md transition-all duration-500 ease-out ${
        leaving
          ? "opacity-0 -translate-y-12"
          : mounted
          ? "opacity-100 translate-y-0"
          : "opacity-0 translate-y-12"
      }`}>

        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-zinc-800/80 backdrop-blur mb-6">
            <span className="text-3xl">🎫</span>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">
            企業活動訂票系統
          </h1>
          <p className="text-zinc-400 mt-2 text-sm">
            {selectedType ? "請輸入您的員工編號與密碼" : "請選擇登入方式"}
          </p>
        </div>

        <div className="bg-zinc-900/80 backdrop-blur border border-zinc-800 rounded-2xl p-6 overflow-hidden">
          <div className={`transition-all duration-200 ease-out ${
            animating ? "opacity-0 translate-y-3" : "opacity-100 translate-y-0"
          }`}>

            {/* 選擇登入類型 */}
            {!selectedType && (
              <div className="flex flex-col gap-3">
                {LOGIN_OPTIONS.map(option => (
                  <button
                    key={option.type}
                    onClick={() => handleSelectType(option.type)}
                    className="w-full py-3 px-4 rounded-xl bg-zinc-800/80 hover:bg-zinc-700 text-white text-sm font-medium transition-colors flex items-center gap-3"
                  >
                    <span className="text-lg">{option.icon}</span>
                    <div className="text-left">
                      <p className="font-semibold">{option.label}</p>
                      <p className="text-zinc-400 text-xs">{option.sublabel}</p>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* 登入表單 */}
            {selectedType && selectedOption && (
              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div className="flex items-center gap-3 mb-2">
                  <button
                    type="button"
                    onClick={handleBack}
                    className="w-8 h-8 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors flex items-center justify-center text-sm flex-shrink-0"
                  >
                    ←
                  </button>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{selectedOption.icon}</span>
                    <span className="text-white font-semibold">{selectedOption.label}</span>
                  </div>
                </div>

                <div>
                  <label className="text-zinc-400 text-sm block mb-2">員工編號</label>
                  <input
                    type="text"
                    value={employeeId}
                    onChange={e => setEmployeeId(e.target.value)}
                    placeholder={useMock ? "employee / admin / hr" : "請輸入員工編號"}
                    autoComplete="username"
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-2.5 text-white text-sm placeholder-zinc-500 focus:outline-none focus:border-zinc-500"
                  />
                </div>

                <div>
                  <label className="text-zinc-400 text-sm block mb-2">密碼</label>
                  <input
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder={useMock ? "密碼：1234" : "請輸入密碼"}
                    autoComplete="current-password"
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-2.5 text-white text-sm placeholder-zinc-500 focus:outline-none focus:border-zinc-500"
                  />
                </div>

                {error && (
                  <div className="bg-red-900/30 border border-red-800 rounded-xl px-4 py-3 text-red-400 text-sm">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-white hover:bg-zinc-100 disabled:opacity-50 text-zinc-900 font-semibold transition-colors mt-1"
                >
                  {loading ? "登入中..." : "登入"}
                </button>
              </form>
            )}

          </div>
        </div>

        <p className="text-center text-zinc-600 text-xs mt-4">
          {useMock
            ? "測試帳號：employee / admin / hr，密碼：1234"
            : "使用公司員工帳號登入"
          }
        </p>
      </div>
    </div>
  )
}

export default LoginPage