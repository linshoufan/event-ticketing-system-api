/**
 * 應用程式全域核心組態設定
 */
export const APP_CONFIG = {
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL ?? "https://api.your-domain.com/v1",
  },
  auth: {
    autoLogoutMinutes: 30,
    tokenKey: "token",
    roleKey: "role",
    expiryKey: "tokenExpiry",
  },
  development: {
    mockDelayMs: 800,
    mockActionDelayMs: 500,
    useMock: import.meta.env.VITE_USE_MOCK === "true",  // ← 新增
  }
} as const