export type Role = "welfare_member" | "employee" | "hr"

export type EventStatus =
  | "not_open"
  | "registering"
  | "waitlist"
  | "closed"
  | "ended"

export type TicketStatus = "used" | "unused" | "invalid"

export type RegistrationStatus = "active" | "locked"

export type DietType = "veg" | "non-veg" | null

export interface User {
  userId: string
  username: string
  email: string
  role: Role
  registrationStatus: RegistrationStatus
  unlockAt: string | null
  dietType: "veg" | "non-veg" | null
  selfDriving: boolean | null
  tags: string[]
  preferences: {
    category: string
    dietType: "veg" | "non-veg" | null
    selfDriving: boolean | null
    guestCount: number | null
  }[]
}

export interface Event {
  eventId: string
  name: string
  description: string
  category: string
  location: string
  latitude: number
  longitude: number
  checkinRadiusMeters: number
  eventStartTime: string
  eventEndTime: string
  registrationStart: string
  registrationEnd: string
  status: EventStatus
  ticketLimit: number | null
  remainingTickets: number
  cancellationDeadline: string | null
  guestAllowed: boolean
  guestCount: number
  updatedAt: string
  isDraft?: boolean
  createdAt?: string
  faqs?: { question: string; answer: string }[]
}

export interface Transaction {
  transactionId: string
  eventId: string
  eventName: string
  eventStartTime: string
  status: "confirmed" | "waitlist" | "cancelled"
  waitlistNumber: number | null
  guestCount: number
  dietType: DietType
  selfDriving: boolean
  registeredAt: string
  ticketId: string | null
}

export interface Ticket {
  ticketId: string
  eventId: string
  eventName: string
  eventStartTime: string
  eventEndTime: string
  eventLocation: string
  latitude: number
  longitude: number
  checkinRadiusMeters: number
  status: TicketStatus
  checkinAvailable: boolean
  qrPayload?: string
}

export interface Notification {
  notificationId: string
  type:
    | "REGISTRATION_SUCCESS"
    | "WAITLIST_PROMOTED"
    | "EVENT_REMINDER"
    | "ACCOUNT_LOCKED"
    | "ACCOUNT_UNLOCKED"
  title: string
  message: string
  eventId: string
  read: boolean
  createdAt: string
}

export interface ApiResponse<T> {
  data: T
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    limit: number
    total: number
  }
}

export interface ApiError {
  error: {
    code: string
    message: string
    unlockAt?: string
  }
}