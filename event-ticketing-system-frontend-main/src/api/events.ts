import type { Event, PaginatedResponse } from "../types"
import { getAuthHeaders } from "./auth"
import { APP_CONFIG } from "../config/app.config"

const BASE_URL = APP_CONFIG.api.baseUrl
const { useMock, mockDelayMs } = APP_CONFIG.development

function delay<T>(data: T): Promise<T> {
  return new Promise(resolve => setTimeout(() => resolve(data), mockDelayMs))
}

export async function getEvents(params?: {
  page?: number
  limit?: number
  keyword?: string
  category?: string
  status?: string
}): Promise<PaginatedResponse<Event>> {
  if (useMock) {
    const { MOCK_EVENTS } = await import("../mock/events")
    let data = [...MOCK_EVENTS]
    if (params?.keyword) {
      data = data.filter(e =>
        e.name.includes(params.keyword!) || e.description.includes(params.keyword!)
      )
    }
    if (params?.category) {
      data = data.filter(e => e.category === params.category)
    }
    return delay({ data, pagination: { page: 1, limit: data.length, total: data.length } })
  }

  const query = new URLSearchParams(
    Object.entries(params ?? {})
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => [k, String(v)])
  )
  const res = await fetch(`${BASE_URL}/events?${query}`, { headers: getAuthHeaders() })
  return res.json()
}

export async function getEventById(eventId: string): Promise<Event> {
  if (useMock) {
    const { MOCK_EVENTS } = await import("../mock/events")
    const event = MOCK_EVENTS.find(e => e.eventId === eventId)
    if (!event) throw new Error("Event not found")
    return delay(event)
  }

  const res = await fetch(`${BASE_URL}/events/${eventId}`, { headers: getAuthHeaders() })
  const json = await res.json()
  return json.data
}

export async function checkEligibility(eventId: string) {
  if (useMock) {
    const { MOCK_ELIGIBILITY } = await import("../mock/events")
    return delay(MOCK_ELIGIBILITY)
  }

  const res = await fetch(`${BASE_URL}/events/${eventId}/eligibility`, {
    headers: getAuthHeaders(),
  })
  const json = await res.json()
  return json.data
}

export async function createEvent(body: Partial<Event>) {
  if (useMock) {
    return delay({ eventId: `ev_${Date.now()}`, isDraft: body.isDraft ?? true, createdAt: new Date().toISOString() })
  }

  const res = await fetch(`${BASE_URL}/events`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  })
  const json = await res.json()
  return json.data
}

export async function updateEvent(eventId: string, body: Partial<Event>) {
  if (useMock) {
    return delay({ updated: true, updatedAt: new Date().toISOString() })
  }

  const res = await fetch(`${BASE_URL}/events/${eventId}`, {
    method: "PATCH",
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  })
  const json = await res.json()
  return json.data
}

export async function deleteEvent(eventId: string) {
  if (useMock) {
    return delay({ deleted: true })
  }

  const res = await fetch(`${BASE_URL}/events/${eventId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  })
  const json = await res.json()
  return json.data
}

export async function getEventRegistrations(
  eventId: string,
  params?: { page?: number; limit?: number; status?: string }
) {
  if (useMock) {
    const { MOCK_REGISTRATIONS } = await import("../mock/transactions")
    return delay(MOCK_REGISTRATIONS)
  }

  const query = new URLSearchParams(
    Object.entries(params ?? {})
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => [k, String(v)])
  )
  const res = await fetch(`${BASE_URL}/events/${eventId}/registrations?${query}`, {
    headers: getAuthHeaders(),
  })
  return res.json()
}