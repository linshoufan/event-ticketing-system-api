import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import EventCard from "../../components/EventCard"
import type { Event } from "../../types"

const mockEvent: Event = {
  eventId:              "ev_001",
  name:                 "夏日烤肉趴",
  description:          "部門聯誼活動",
  category:             "sport",
  location:             "台北辦公室頂樓",
  latitude:             25.0478,
  longitude:            121.5319,
  checkinRadiusMeters:  200,
  eventStartTime:       "2025-07-15T18:00:00Z",
  eventEndTime:         "2025-07-15T22:00:00Z",
  registrationStart:    "2025-06-01T00:00:00Z",
  registrationEnd:      "2025-07-01T23:59:59Z",
  status:               "registering",
  ticketLimit:          50,
  remainingTickets:     12,
  cancellationDeadline: "2025-07-10T00:00:00Z",
  guestAllowed:         false,
  guestCount:           0,
  updatedAt:            "2025-05-18T10:00:00Z",
  isDraft:              false,
}

describe("EventCard 顯示內容", () => {
  it("應該顯示活動名稱", () => {
    render(<EventCard event={mockEvent} onClick={() => {}} />)
    expect(screen.getByText("夏日烤肉趴")).toBeInTheDocument()
  })

  it("應該顯示活動地點", () => {
    render(<EventCard event={mockEvent} onClick={() => {}} />)
    expect(screen.getByText("台北辦公室頂樓")).toBeInTheDocument()
  })

  it("registering 狀態應該顯示「報名中」", () => {
    render(<EventCard event={mockEvent} onClick={() => {}} />)
    expect(screen.getByTestId("event-status")).toHaveTextContent("報名中")
  })

  it("not_open 狀態應該顯示「尚未開始報名」", () => {
    render(<EventCard event={{ ...mockEvent, status: "not_open" }} onClick={() => {}} />)
    expect(screen.getByTestId("event-status")).toHaveTextContent("尚未開始報名")
  })

  it("waitlist 狀態應該顯示「候補登記」", () => {
    render(<EventCard event={{ ...mockEvent, status: "waitlist" }} onClick={() => {}} />)
    expect(screen.getByTestId("event-status")).toHaveTextContent("候補登記")
  })

  it("closed 狀態應該顯示「報名截止」", () => {
    render(<EventCard event={{ ...mockEvent, status: "closed" }} onClick={() => {}} />)
    expect(screen.getByTestId("event-status")).toHaveTextContent("報名截止")
  })

  it("ended 狀態應該顯示「活動結束」", () => {
    render(<EventCard event={{ ...mockEvent, status: "ended" }} onClick={() => {}} />)
    expect(screen.getByTestId("event-status")).toHaveTextContent("活動結束")
  })

  it("有票數限制時應該顯示剩餘名額", () => {
    render(<EventCard event={mockEvent} onClick={() => {}} />)
    expect(screen.getByText("12")).toBeInTheDocument()
  })

  it("沒有票數限制時不應該顯示剩餘名額", () => {
    render(<EventCard event={{ ...mockEvent, ticketLimit: null }} onClick={() => {}} />)
    expect(screen.queryByText("12")).not.toBeInTheDocument()
  })
})

describe("EventCard 樣式", () => {
  it("registering 狀態卡片不應該有 opacity-50", () => {
    render(<EventCard event={mockEvent} onClick={() => {}} />)
    expect(screen.getByTestId("event-card")).not.toHaveClass("opacity-50")
  })

  it("ended 狀態卡片應該有 opacity-50", () => {
    render(<EventCard event={{ ...mockEvent, status: "ended" }} onClick={() => {}} />)
    expect(screen.getByTestId("event-card")).toHaveClass("opacity-50")
  })

  it("not_open 狀態卡片應該有 opacity-50", () => {
    render(<EventCard event={{ ...mockEvent, status: "not_open" }} onClick={() => {}} />)
    expect(screen.getByTestId("event-card")).toHaveClass("opacity-50")
  })

  it("closed 狀態卡片應該有 opacity-50", () => {
    render(<EventCard event={{ ...mockEvent, status: "closed" }} onClick={() => {}} />)
    expect(screen.getByTestId("event-card")).toHaveClass("opacity-50")
  })
})

describe("EventCard 互動", () => {
  it("點擊卡片應該觸發 onClick", async () => {
    const handleClick = vi.fn()
    render(<EventCard event={mockEvent} onClick={handleClick} />)
    await userEvent.click(screen.getByTestId("event-card"))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it("點擊兩次應該觸發 onClick 兩次", async () => {
    const handleClick = vi.fn()
    render(<EventCard event={mockEvent} onClick={handleClick} />)
    await userEvent.click(screen.getByTestId("event-card"))
    await userEvent.click(screen.getByTestId("event-card"))
    expect(handleClick).toHaveBeenCalledTimes(2)
  })
})

describe("EventCard category emoji", () => {
  it("sport 類別應該顯示跑步 emoji", () => {
    render(<EventCard event={{ ...mockEvent, category: "sport" }} onClick={() => {}} />)
    expect(screen.getByText("🏃")).toBeInTheDocument()
  })

  it("food 類別應該顯示餐盤 emoji", () => {
    render(<EventCard event={{ ...mockEvent, category: "food" }} onClick={() => {}} />)
    expect(screen.getByText("🍽️")).toBeInTheDocument()
  })

  it("music 類別應該顯示音符 emoji", () => {
    render(<EventCard event={{ ...mockEvent, category: "music" }} onClick={() => {}} />)
    expect(screen.getByText("🎵")).toBeInTheDocument()
  })

  it("未知類別應該顯示預設 emoji", () => {
    render(<EventCard event={{ ...mockEvent, category: "unknown" }} onClick={() => {}} />)
    expect(screen.getByText("📅")).toBeInTheDocument()
  })
})