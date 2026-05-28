import type { Transaction, PaginatedResponse } from "../types"
import { getAuthHeaders } from "./auth"
import { APP_CONFIG } from "../config/app.config"

const BASE_URL = APP_CONFIG.api.baseUrl
const { useMock, mockDelayMs, mockActionDelayMs } = APP_CONFIG.development

function delay<T>(data: T, ms: number = mockDelayMs): Promise<T> {
  return new Promise(resolve => setTimeout(() => resolve(data), ms))
}

export async function getTransactions(params?: {
  page?: number
  limit?: number
  status?: "confirmed" | "waitlist" | "cancelled"
}): Promise<PaginatedResponse<Transaction>> {
  if (useMock) {
    const { MOCK_TRANSACTIONS } = await import("../mock/transactions")
    const data = params?.status
      ? MOCK_TRANSACTIONS.filter(t => t.status === params.status)
      : MOCK_TRANSACTIONS
    return delay({ data, pagination: { page: 1, limit: data.length, total: data.length } })
  }

  const query = new URLSearchParams(
    Object.entries(params ?? {})
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => [k, String(v)])
  )
  const res = await fetch(`${BASE_URL}/transactions?${query}`, { headers: getAuthHeaders() })
  return res.json()
}

export async function createTransaction(body: {
  eventId: string
  guestCount: number
  dietType: "veg" | "non-veg" | "none"
  selfDriving: boolean
  saveAutofill: boolean
}) {
  if (useMock) {
    return delay({
      transactionId: `tx_${Date.now()}`,
      status: "confirmed" as const,
      ticketId: `tk_${Date.now()}`,
      waitlistNumber: null,
      registeredAt: new Date().toISOString(),
    }, mockActionDelayMs)
  }

  const res = await fetch(`${BASE_URL}/transactions`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  })
  const json = await res.json()
  if (!res.ok) throw json.error
  return json.data
}

export async function cancelTransaction(transactionId: string) {
  if (useMock) {
    return delay({ cancelled: true }, mockActionDelayMs)
  }

  const res = await fetch(`${BASE_URL}/transactions/${transactionId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  })
  const json = await res.json()
  if (!res.ok) throw json.error
  return json.data
}

export async function updateTransaction(
  transactionId: string,
  body: { guestCount?: number; dietType?: "veg" | "non-veg" | "none"; selfDriving?: boolean }
) {
  if (useMock) {
    return delay({ updated: true, updatedAt: new Date().toISOString() }, mockActionDelayMs)
  }

  const res = await fetch(`${BASE_URL}/transactions/${transactionId}`, {
    method: "PATCH",
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  })
  const json = await res.json()
  if (!res.ok) throw json.error
  return json.data
}