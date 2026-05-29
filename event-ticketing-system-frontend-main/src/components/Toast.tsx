interface ToastProps {
  message: string
  type: "success" | "error" | "info"
  visible: boolean
}

const TYPE_CONFIG = {
  success: "bg-emerald-900/90 border-emerald-700 text-emerald-300",
  error:   "bg-red-900/90 border-red-700 text-red-300",
  info:    "bg-zinc-800/90 border-zinc-700 text-zinc-300",
}

function Toast({ message, type, visible }: ToastProps) {
  return (
    <div className={`
      fixed bottom-6 right-6 z-50
      px-4 py-3 rounded-xl border backdrop-blur
      text-sm font-medium
      transition-all duration-300
      ${TYPE_CONFIG[type]}
      ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4 pointer-events-none"}
    `}>
      <div className="flex items-center gap-2">
        {type === "success" && <span>✓</span>}
        {type === "error" && <span>✕</span>}
        {type === "info" && <span>ℹ</span>}
        {message}
      </div>
    </div>
  )
}

export default Toast