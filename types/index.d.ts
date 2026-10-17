export type View = { task: string; current: string; pct: number; eta: string }

declare module 'claude-code' {
  interface PluginState {
    howfar: { view: View | null }
  }
}
