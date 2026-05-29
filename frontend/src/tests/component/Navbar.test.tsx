import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import Navbar from "../../components/Navbar"

// mock useNavigate
const mockNavigate = vi.fn()
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom")
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

function renderNavbar(role: string, path = "/events") {
  localStorage.setItem("role", role)
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Navbar />
    </MemoryRouter>
  )
}

describe("Navbar - employee", () => {
  it("應該看到活動", () => {
    renderNavbar("employee")
    expect(screen.getByText("活動")).toBeInTheDocument()
  })

  it("應該看到報名", () => {
    renderNavbar("employee")
    expect(screen.getByText("報名")).toBeInTheDocument()
  })

  it("應該看到票券", () => {
    renderNavbar("employee")
    expect(screen.getByText("票券")).toBeInTheDocument()
  })

  it("不應該看到活動管理", () => {
    renderNavbar("employee")
    expect(screen.queryByText("活動管理")).not.toBeInTheDocument()
  })

  it("不應該看到統計", () => {
    renderNavbar("employee")
    expect(screen.queryByText("統計")).not.toBeInTheDocument()
  })
})

describe("Navbar - welfare_member", () => {
  it("應該看到活動管理", () => {
    renderNavbar("welfare_member")
    expect(screen.getByText("活動管理")).toBeInTheDocument()
  })

  it("應該看到使用者", () => {
    renderNavbar("welfare_member")
    expect(screen.getByText("使用者")).toBeInTheDocument()
  })

  it("不應該看到報名", () => {
    renderNavbar("welfare_member")
    expect(screen.queryByText("報名")).not.toBeInTheDocument()
  })

  it("不應該看到票券", () => {
    renderNavbar("welfare_member")
    expect(screen.queryByText("票券")).not.toBeInTheDocument()
  })
})

describe("Navbar - hr", () => {
  it("應該看到統計", () => {
    renderNavbar("hr")
    expect(screen.getByText("統計")).toBeInTheDocument()
  })

  it("應該看到活動", () => {
    renderNavbar("hr")
    expect(screen.getByText("活動")).toBeInTheDocument()
  })

  it("不應該看到活動管理", () => {
    renderNavbar("hr")
    expect(screen.queryByText("活動管理")).not.toBeInTheDocument()
  })

  it("不應該看到使用者", () => {
    renderNavbar("hr")
    expect(screen.queryByText("使用者")).not.toBeInTheDocument()
  })
})

describe("Navbar - 所有角色共用", () => {
  it("employee 應該看到個人", () => {
    renderNavbar("employee")
    expect(screen.getByText("個人")).toBeInTheDocument()
  })

  it("welfare_member 應該看到個人", () => {
    renderNavbar("welfare_member")
    expect(screen.getByText("個人")).toBeInTheDocument()
  })

  it("hr 應該看到個人", () => {
    renderNavbar("hr")
    expect(screen.getByText("個人")).toBeInTheDocument()
  })

  it("所有角色都應該看到登出按鈕", () => {
    renderNavbar("employee")
    expect(screen.getByText("登出")).toBeInTheDocument()
  })

  it("role 為空時不應該顯示 navbar", () => {
    localStorage.removeItem("role")
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    )
    expect(screen.queryByText("登出")).not.toBeInTheDocument()
  })
})

describe("Navbar - 導航功能", () => {
  it("點擊個人應該導航到 /profile", async () => {
    renderNavbar("employee")
    await userEvent.click(screen.getByText("個人"))
    expect(mockNavigate).toHaveBeenCalledWith("/profile")
  })

  it("employee 點擊活動應該導航到 /events", async () => {
    renderNavbar("employee")
    await userEvent.click(screen.getByText("活動"))
    expect(mockNavigate).toHaveBeenCalledWith("/events")
  })

  it("welfare_member 點擊活動管理應該導航到 /admin/events", async () => {
    renderNavbar("welfare_member")
    await userEvent.click(screen.getByText("活動管理"))
    expect(mockNavigate).toHaveBeenCalledWith("/admin/events")
  })
})