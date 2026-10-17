import { expect, test } from 'claude-code/testing'

import { eta, toView } from './progress'

const plan = (started: number, override: number | null = null) =>
  JSON.stringify({
    task: 'Add login page',
    steps: [
      { name: 'Read code', weight: 15, done: true },
      { name: 'Write form', weight: 30, done: true },
      { name: 'Add tests', weight: 55, done: false },
    ],
    current: 'Add tests',
    started,
    override,
  })

test('percent and ETA match howfar line', async () => {
  // 45% done after 450s: 450 * 55 / 45 = 550s left, as howfar.py computes it.
  expect(toView(plan(1000), 1450, 0)).toEqual({ task: 'Add login page', current: 'Add tests', pct: 45, eta: '~9m 10s left' })
})

test('manual override wins', async () => {
  expect(toView(plan(1000, 80), 1450, 0)?.pct).toBe(80)
})

test('plans from before the latest prompt are hidden', async () => {
  expect(toView(plan(1000), 1450, 1001)).toBeNull()
  expect(toView(plan(1000), 1450, 1000)).not.toBeNull()
})

test('missing or broken progress.json shows nothing', async () => {
  expect(toView('', 1450, 0)).toBeNull()
  expect(toView('{"task": "x", "steps": []}', 1450, 0)).toBeNull()
})

test('ETA edges', async () => {
  expect(eta(100, 0)).toBe('estimating...')
  expect(eta(100, 100)).toBe('done')
  expect(eta(3600, 50)).toBe('~1h 00m left')
})
