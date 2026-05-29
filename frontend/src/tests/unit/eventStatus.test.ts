import { describe, it, expect } from "vitest"
import type { EventStatus } from "../../types"

function getStatusLabel(status: EventStatus): string {
  const map: Record<EventStatus, string> = {
    not_open:    "尚未開始報名",
    registering: "報名中",
    waitlist:    "候補登記",
    closed:      "報名截止",
    ended:       "活動結束",
  }
  return map[status] ?? status
}

function getStatusColor(status: EventStatus): string {
  const map: Record<EventStatus, string> = {
    not_open:    "text-zinc-400",
    registering: "text-emerald-400",
    waitlist:    "text-amber-400",
    closed:      "text-red-400",
    ended:       "text-zinc-500",
  }
  return map[status]
}

function isActive(status: EventStatus): boolean {
  return status === "registering"
}

function canRegister(status: EventStatus): boolean {
  return status === "registering" || status === "waitlist"
}

describe("getStatusLabel", () => {
  it("應該回傳「報名中」", () => {
    expect(getStatusLabel("registering")).toBe("報名中")
  })

  it("應該回傳「尚未開始報名」", () => {
    expect(getStatusLabel("not_open")).toBe("尚未開始報名")
  })

  it("應該回傳「候補登記」", () => {
    expect(getStatusLabel("waitlist")).toBe("候補登記")
  })

  it("應該回傳「報名截止」", () => {
    expect(getStatusLabel("closed")).toBe("報名截止")
  })

  it("應該回傳「活動結束」", () => {
    expect(getStatusLabel("ended")).toBe("活動結束")
  })
})

describe("getStatusColor", () => {
  it("registering 應該是綠色", () => {
    expect(getStatusColor("registering")).toBe("text-emerald-400")
  })

  it("waitlist 應該是琥珀色", () => {
    expect(getStatusColor("waitlist")).toBe("text-amber-400")
  })

  it("closed 應該是紅色", () => {
    expect(getStatusColor("closed")).toBe("text-red-400")
  })

  it("ended 應該是灰色", () => {
    expect(getStatusColor("ended")).toBe("text-zinc-500")
  })

  it("not_open 應該是灰色", () => {
    expect(getStatusColor("not_open")).toBe("text-zinc-400")
  })
})

describe("isActive", () => {
  it("registering 應該是 active", () => {
    expect(isActive("registering")).toBe(true)
  })

  it("ended 不應該是 active", () => {
    expect(isActive("ended")).toBe(false)
  })

  it("not_open 不應該是 active", () => {
    expect(isActive("not_open")).toBe(false)
  })

  it("waitlist 不應該是 active", () => {
    expect(isActive("waitlist")).toBe(false)
  })

  it("closed 不應該是 active", () => {
    expect(isActive("closed")).toBe(false)
  })
})

describe("canRegister", () => {
  it("registering 可以報名", () => {
    expect(canRegister("registering")).toBe(true)
  })

  it("waitlist 可以加入候補", () => {
    expect(canRegister("waitlist")).toBe(true)
  })

  it("not_open 不能報名", () => {
    expect(canRegister("not_open")).toBe(false)
  })

  it("closed 不能報名", () => {
    expect(canRegister("closed")).toBe(false)
  })

  it("ended 不能報名", () => {
    expect(canRegister("ended")).toBe(false)
  })
})