export async function fetchWithRetry(
  url: string,
  options?: RequestInit,
  retries = 3,
  delay = 1000
): Promise<Response> {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, options)
      if (res.ok || res.status < 500) return res
      throw new Error(`Server error: ${res.status}`)
    } catch (err) {
      if (i === retries - 1) throw err
      await new Promise(r => setTimeout(r, delay * (i + 1)))
    }
  }
  throw new Error("Max retries reached")
}