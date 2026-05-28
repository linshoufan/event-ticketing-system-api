import { useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { removeToken } from "../api/auth"
import { APP_CONFIG } from "../config/app.config"

const { autoLogoutMinutes, expiryKey, tokenKey, roleKey } = APP_CONFIG.auth

export function saveLoginTime() {
  const expiry = Date.now() + autoLogoutMinutes * 60 * 1000
  localStorage.setItem(expiryKey, String(expiry))
}

export function clearLoginTime() {
  localStorage.removeItem(expiryKey)
}

export function isTokenExpired(): boolean {
  const expiry = localStorage.getItem(expiryKey)
  if (!expiry) return false
  return Date.now() > Number(expiry)
}

export function useAutoLogout() {
  const navigate = useNavigate()

  useEffect(() => {
    const token = localStorage.getItem(tokenKey)
    if (!token) return

    if (isTokenExpired()) {
      handleLogout()
      return
    }

    const expiry = localStorage.getItem(expiryKey)
    if (!expiry) return

    const remaining = Number(expiry) - Date.now()

    const timer = setTimeout(() => {
      handleLogout()
    }, remaining)

    return () => clearTimeout(timer)

    function handleLogout() {
      removeToken()
      localStorage.removeItem(roleKey)
      clearLoginTime()
      navigate("/", { replace: true })
    }
  }, [navigate])
}