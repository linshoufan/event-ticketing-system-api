import type { Transaction } from "../types"

export const MOCK_TRANSACTIONS: Transaction[] = [
  {
    transactionId: "tx_001",
    eventId: "ev_001",
    eventName: "夏日烤肉趴",
    eventStartTime: "2025-07-15T18:00:00Z",
    status: "confirmed",
    waitlistNumber: null,
    guestCount: 0,
    dietType: null,
    selfDriving: true,
    registeredAt: "2025-05-18T09:00:00Z",
    ticketId: "tk_001",
  },
  {
    transactionId: "tx_002",
    eventId: "ev_003",
    eventName: "家庭日活動",
    eventStartTime: "2025-09-01T10:00:00Z",
    status: "waitlist",
    waitlistNumber: 3,
    guestCount: 0,
    dietType: null,
    selfDriving: false,
    registeredAt: "2025-05-19T10:00:00Z",
    ticketId: null,
  },
]

export const MOCK_REGISTRATIONS = {
  summary: {
    totalConfirmed: 38,
    totalWaitlist: 5,
    totalCancelled: 4,
  },
  registrations: [
    {
      transactionId: "tx_001",
      userId: "u_abc123",
      username: "john.doe",
      status: "confirmed",
      guestCount: 0,
      dietType: "non-veg",
      selfDriving: true,
      registeredAt: "2025-05-18T09:00:00Z",
    },
    {
      transactionId: "tx_002",
      userId: "u_xyz789",
      username: "jane.smith",
      status: "waitlist",
      guestCount: 2,
      dietType: "veg",
      selfDriving: false,
      registeredAt: "2025-05-19T10:00:00Z",
    },
  ],
}