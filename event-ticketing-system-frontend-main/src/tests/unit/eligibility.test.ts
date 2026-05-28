import { describe, it, expect } from "vitest"

interface Eligibility {
  eligible: boolean
  reason: string | null
  remainingTickets: number
  isWaitlist: boolean
  unlockAt?: string | null
}

function canRegister(eligibility: Eligibility): boolean {
  return eligibility.eligible && !eligibility.isWaitlist
}

function canWaitlist(eligibility: Eligibility): boolean {
  return eligibility.eligible && eligibility.isWaitlist
}

function getEligibilityMessage(eligibility: Eligibility): string {
  if (eligibility.eligible) return ""
  switch (eligibility.reason) {
    case "LOCKED":
      return `帳號已鎖定，解鎖時間：${eligibility.unlockAt}`
    case "ALREADY_REGISTERED":
      return "您已報名此活動"
    case "NO_TICKETS":
      return "名額已滿"
    default:
      return "無法報名"
  }
}

function getRemainingTicketsStatus(remainingTickets: number, ticketLimit: number): "plenty" | "limited" | "full" {
  if (remainingTickets === 0) return "full"
  if (remainingTickets / ticketLimit <= 0.2) return "limited"
  return "plenty"
}

describe("canRegister", () => {
  it("eligible 且不是候補，可以報名", () => {
    expect(canRegister({
      eligible: true, reason: null, remainingTickets: 12, isWaitlist: false,
    })).toBe(true)
  })

  it("eligible 但是候補，不能直接報名", () => {
    expect(canRegister({
      eligible: true, reason: null, remainingTickets: 0, isWaitlist: true,
    })).toBe(false)
  })

  it("不 eligible，不能報名", () => {
    expect(canRegister({
      eligible: false, reason: "LOCKED", remainingTickets: 12, isWaitlist: false,
    })).toBe(false)
  })
})

describe("canWaitlist", () => {
  it("eligible 且是候補，可以加入候補", () => {
    expect(canWaitlist({
      eligible: true, reason: null, remainingTickets: 0, isWaitlist: true,
    })).toBe(true)
  })

  it("不 eligible，不能加入候補", () => {
    expect(canWaitlist({
      eligible: false, reason: "LOCKED", remainingTickets: 0, isWaitlist: false,
    })).toBe(false)
  })

  it("eligible 但不是候補，不能加入候補", () => {
    expect(canWaitlist({
      eligible: true, reason: null, remainingTickets: 5, isWaitlist: false,
    })).toBe(false)
  })
})

describe("getEligibilityMessage", () => {
  it("eligible 應該回傳空字串", () => {
    expect(getEligibilityMessage({
      eligible: true, reason: null, remainingTickets: 12, isWaitlist: false,
    })).toBe("")
  })

  it("LOCKED 應該回傳鎖定訊息", () => {
    expect(getEligibilityMessage({
      eligible: false, reason: "LOCKED", remainingTickets: 12,
      isWaitlist: false, unlockAt: "2025-06-18T00:00:00Z",
    })).toBe("帳號已鎖定，解鎖時間：2025-06-18T00:00:00Z")
  })

  it("ALREADY_REGISTERED 應該回傳已報名訊息", () => {
    expect(getEligibilityMessage({
      eligible: false, reason: "ALREADY_REGISTERED", remainingTickets: 12, isWaitlist: false,
    })).toBe("您已報名此活動")
  })

  it("NO_TICKETS 應該回傳名額已滿訊息", () => {
    expect(getEligibilityMessage({
      eligible: false, reason: "NO_TICKETS", remainingTickets: 0, isWaitlist: false,
    })).toBe("名額已滿")
  })

  it("未知 reason 應該回傳預設訊息", () => {
    expect(getEligibilityMessage({
      eligible: false, reason: "UNKNOWN", remainingTickets: 0, isWaitlist: false,
    })).toBe("無法報名")
  })
})

describe("getRemainingTicketsStatus", () => {
  it("名額為 0 應該回傳 full", () => {
    expect(getRemainingTicketsStatus(0, 50)).toBe("full")
  })

  it("名額不足 20% 應該回傳 limited", () => {
    expect(getRemainingTicketsStatus(5, 50)).toBe("limited")
  })

  it("名額充足應該回傳 plenty", () => {
    expect(getRemainingTicketsStatus(30, 50)).toBe("plenty")
  })
})