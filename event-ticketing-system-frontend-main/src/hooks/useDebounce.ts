import { useRef, useCallback } from "react"

export function useDebounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 500
): (...args: Parameters<T>) => void {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  return useCallback((...args: Parameters<T>) => {
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => {
      fn(...args)
    }, delay)
  }, [fn, delay])
}