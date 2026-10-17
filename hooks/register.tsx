import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import { toView } from './progress'

const view = atom({ plugin: 'howfar', key: 'view' } as const, null)

const instructions = (root: string) => `# Progress reporting (howfar)

The howfar plugin shows a progress bar above the prompt. Report your progress on every task with more than one step by running howfar.py from the project root, so progress.json lands there. Use \`python3\`, or \`python\` on Windows.

1. Before any work, run \`python3 "${root}/howfar.py" plan "<task>" "<Milestone>:<weight>" ...\` with 4 to 8 milestones whose weights add up to 100, weighted by expected effort.
2. Run \`python3 "${root}/howfar.py" start "<Milestone>"\` before you begin a milestone.
3. Run \`python3 "${root}/howfar.py" done "<Milestone>"\` after it is finished. Only mark a milestone done when it works (code runs, tests pass), not when it is merely written.
4. If the scope changes, run \`plan\` again with the new milestones.
5. Use \`python3 "${root}/howfar.py" set <percent> "<text>"\` only for a rough manual correction; the next \`done\` clears it.`

// Seconds since the epoch; a plan started before the latest prompt is stale and not shown.
let since = Infinity
let last = ''

async function refresh($: EngineInterface) {
  const text = await $.fs.read('progress.json').catch(() => '')
  const next = toView(text, (await $.clock.now()) / 1000, since)
  const key = JSON.stringify(next)
  if (key !== last) {
    last = key
    await update($, view, () => next)
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const result = await next(e)
    since = (await $.clock.now()) / 1000
    $.clock.every(1000, () => refresh($))
    return result
  })

  on('prompt.submit', ($, e, next) => {
    if (!e.command && !e.isMeta) {
      $.clock
        .now()
        .then(now => {
          since = now / 1000
          return refresh($)
        })
        .catch(() => {})
    }
    return next(e)
  })

  on('prompt.compose', async ($, e, next) => {
    const { sections } = await next(e)
    return { sections: [...sections, { id: 'howfar:instructions', text: instructions($.plugin.root), scope: 'session' }] }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const v = await read($, view)
    if (e.props.hasSurvey || v === null) {
      return next(e)
    }
    const { Box, Text } = $.ui.resolve(e)
    const width = Math.max(10, Math.min(30, e.props.bodyColumns - 50))
    const filled = Math.round((width * v.pct) / 100)
    const color = v.pct >= 100 ? 'success' : 'claude'

    return (
      <Box>
        <Text color={color}>{'█'.repeat(filled)}</Text>
        <Text dimColor>{'░'.repeat(width - filled)}</Text>
        <Text wrap="truncate-end">
          {' '}
          <Text bold>{v.pct}%</Text> · {v.current} · <Text dimColor>{v.eta}</Text>
        </Text>
      </Box>
    )
  })
}
