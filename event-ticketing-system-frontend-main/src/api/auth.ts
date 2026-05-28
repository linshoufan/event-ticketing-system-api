import type { User } from "../types"
import { APP_CONFIG } from "../config/app.config"

const BASE_URL = APP_CONFIG.api.baseUrl
const { useMock, mockDelayMs } = APP_CONFIG.development

const MOCK_ACCOUNTS = [
  { employeeId: "admin",    password: "1234", role: "welfare_member" },
  { employeeId: "employee", password: "1234", role: "employee" },
  { employeeId: "hr",       password: "1234", role: "hr" },
]

function getToken(): string | null {
  return localStorage.getItem("token")
}

export function saveToken(token: string): void {
  localStorage.setItem("token", token)
}

export function removeToken(): void {
  localStorage.removeItem("token")
}

export function getAuthHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getToken()}`,
  }
}

export async function login(body: {
  employeeId: string
  password: string
  role: string | null
}): Promise<{ token: string; role: string }> {
  if (useMock) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const account = MOCK_ACCOUNTS.find(
          a => a.employeeId === body.employeeId && a.password === body.password
        )
        if (!account) {
          reject({ code: "INVALID_CREDENTIALS" })
          return
        }
        if (body.role && body.role !== account.role) {
          reject({ code: "ROLE_MISMATCH" })
          return
        }
        resolve({ token: "mock-jwt-token-123456789", role: account.role })
      }, mockDelayMs)
    })
  }

  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      employeeId: body.employeeId,
      password: body.password,
      role: body.role,
    }),
  })
  const json = await res.json()
  if (!res.ok) throw json.error
  return json.data
}

export async function logout(): Promise<void> {
  if (useMock) {
    removeToken()
    return
  }
  await fetch(`${BASE_URL}/auth/logout`, {
    method: "POST",
    headers: getAuthHeaders(),
  })
  removeToken()
}

export async function getMe(): Promise<User> {
  if (useMock) {
    const { MOCK_USERS } = await import("../mock/users")
    return new Promise(resolve =>
      setTimeout(() => resolve(MOCK_USERS[0] as User), mockDelayMs)
    )
  }
  const res = await fetch(`${BASE_URL}/me`, {
    headers: getAuthHeaders(),
  })
  const json = await res.json()
  return {
    userId: json.data.userId,
    username: json.data.username,
    email: json.data.email,
    role: json.data.role,
    registrationStatus: json.data.registrationStatus,
    unlockAt: json.data.unlockAt,
    dietType: json.data.autofill?.dietType ?? null,
    selfDriving: json.data.autofill?.selfDriving ?? null,
    tags: json.data.preferences ?? [],
    preferences: [],
  }
}