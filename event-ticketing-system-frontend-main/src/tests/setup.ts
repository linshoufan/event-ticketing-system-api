import "@testing-library/jest-dom"
import { beforeEach, vi } from "vitest"

// 每個測試前清空 localStorage
beforeEach(() => {
  localStorage.clear()
})

// Mock geolocation
Object.defineProperty(navigator, "geolocation", {
  value: {
    getCurrentPosition: vi.fn(),
    watchPosition: vi.fn(),
    clearWatch: vi.fn(),
  },
  writable: true,
})