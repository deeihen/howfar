import type { View } from '../types'

// Mirrors percent() and eta() in howfar.py, so the band says what `howfar line` says.
const roundHalfEven = (x: number) => {
  const r = Math.round(x)
  return Math.abs(x % 1) === 0.5 && r % 2 !== 0 ? r - 1 : r
}

export const fmtDuration = (seconds: number) => {
  const s = Math.floor(seconds)
  const pad = (n: number) => String(n).padStart(2, '0')
  if (s < 60) return `${s}s`
  if (s < 3600) return `${Math.floor(s / 60)}m ${pad(s % 60)}s`
  return `${Math.floor(s / 3600)}h ${pad(Math.floor((s % 3600) / 60))}m`
}

export const eta = (elapsed: number, pct: number) => {
  if (pct <= 0) return 'estimating...'
  if (pct >= 100) return 'done'
  return `~${fmtDuration((elapsed * (100 - pct)) / pct)} left`
}

// Returns null for no plan, an unreadable file, or a plan started before `since` (seconds).
export const toView = (text: string, now: number, since: number): View | null => {
  let state
  try {
    state = JSON.parse(text)
  } catch {
    return null
  }
  if (!Array.isArray(state?.steps) || state.steps.length === 0 || !(state.started >= since)) return null
  const steps = state.steps as { weight: number; done: boolean }[]
  const total = steps.reduce((sum, s) => sum + s.weight, 0)
  const done = steps.filter(s => s.done).reduce((sum, s) => sum + s.weight, 0)
  const pct = state.override ?? roundHalfEven((done * 100) / total)
  return { task: String(state.task), current: String(state.current), pct, eta: eta(now - state.started, pct) }
}
