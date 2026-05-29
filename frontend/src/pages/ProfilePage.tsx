import { useState } from "react"
import PageTransition from "../components/PageTransition"

const CATEGORIES = [
  { value: "sport",   label: "🏃 運動" },
  { value: "food",    label: "🍽️ 美食" },
  { value: "travel",  label: "✈️ 旅遊" },
  { value: "culture", label: "🎨 文藝" },
  { value: "family",  label: "👨‍👩‍👧 親子" },
  { value: "contest", label: "🏆 競賽" },
  { value: "music",   label: "🎵 音樂" },
]

const MOCK_PROFILE = {
  username: "john.doe",
  email: "john.doe@company.com",
  role: "employee",
  registrationStatus: "active",
  unlockAt: null as string | null,
  dietType: "non-veg" as "veg" | "non-veg" | null,
  selfDriving: true,
  tags: ["sport", "food"],
  preferences: [
    {
      category: "sport",
      dietType: "non-veg" as "veg" | "non-veg" | null,
      selfDriving: true,
      guestCount: 0,
    }
  ],
}

function ProfilePage() {
  const role = localStorage.getItem("role")

  const [tags, setTags] = useState<string[]>(MOCK_PROFILE.tags)
  const [dietType, setDietType] = useState(MOCK_PROFILE.dietType)
  const [selfDriving, setSelfDriving] = useState(MOCK_PROFILE.selfDriving ?? false)
  const [saved, setSaved] = useState(false)

  function toggleTag(tag: string) {
    setTags(prev =>
      prev.includes(tag)
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    )
  }

  async function handleSave() {
    localStorage.setItem("userTags", JSON.stringify(tags))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  function getRoleLabel(r: string | null) {
    if (r === "welfare_member") return "福委會"
    if (r === "hr") return "HR"
    return "一般員工"
  }

  return (
    <PageTransition>
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">個人資料</h1>

      <div className="flex flex-col gap-4">

        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-14 h-14 rounded-2xl bg-zinc-800 flex items-center justify-center text-2xl">
              👤
            </div>
            <div>
              <p className="text-white font-semibold">{MOCK_PROFILE.username}</p>
              <p className="text-zinc-400 text-sm">{MOCK_PROFILE.email}</p>
            </div>
          </div>
          <div className="flex items-center justify-between py-3 border-t border-zinc-800">
            <span className="text-zinc-500 text-sm">角色</span>
            <span className="text-white text-sm">{getRoleLabel(role)}</span>
          </div>
          <div className="flex items-center justify-between py-3 border-t border-zinc-800">
            <span className="text-zinc-500 text-sm">報名狀態</span>
            {MOCK_PROFILE.registrationStatus === "active" ? (
              <span className="text-xs font-medium px-3 py-1 rounded-full bg-emerald-900/30 text-emerald-400">正常</span>
            ) : (
              <span className="text-xs font-medium px-3 py-1 rounded-full bg-red-900/30 text-red-400">
                鎖定中（{new Date(MOCK_PROFILE.unlockAt!).toLocaleDateString("zh-TW")} 解鎖）
              </span>
            )}
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
          <h3 className="text-white font-semibold mb-1">活動偏好</h3>
          <p className="text-zinc-500 text-sm mb-4">選擇你有興趣的活動類別</p>
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map(cat => {
              const isSelected = tags.includes(cat.value)
              return (
                <button
                  key={cat.value}
                  onClick={() => toggleTag(cat.value)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                    isSelected
                      ? "bg-white text-zinc-900"
                      : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200"
                  }`}
                >
                  {cat.label}
                </button>
              )
            })}
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
          <h3 className="text-white font-semibold mb-1">報名自動填入</h3>
          <p className="text-zinc-500 text-sm mb-4">報名活動時自動帶入以下資料</p>

          <div className="flex flex-col gap-4">
            <div>
              <label className="text-zinc-400 text-sm block mb-2">飲食需求</label>
              <select
                value={dietType ?? ""}
                onChange={e => setDietType(e.target.value as "veg" | "non-veg" | null || null)}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-zinc-500"
              >
                <option value="">無需求</option>
                <option value="veg">素食</option>
                <option value="non-veg">葷食</option>
              </select>
            </div>

            <label className="flex items-center gap-3 cursor-pointer">
              <div
                onClick={() => setSelfDriving(!selfDriving)}
                className={`w-10 h-6 rounded-full transition-colors relative ${selfDriving ? "bg-emerald-500" : "bg-zinc-700"}`}
              >
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${selfDriving ? "left-5" : "left-1"}`} />
              </div>
              <span className="text-zinc-300 text-sm">自行開車</span>
            </label>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="w-full py-3 rounded-xl bg-white hover:bg-zinc-100 text-zinc-900 font-semibold transition-colors"
        >
          {saved ? "✓ 已儲存" : "儲存"}
        </button>
      </div>
    </div>
    </PageTransition>
  )
}

export default ProfilePage