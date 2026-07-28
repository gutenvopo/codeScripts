export function LoadingScreen() {
  return (
    <div className="app-shell flex min-h-screen items-center justify-center text-ink">
      <div className="frosted-light flex items-center gap-3 rounded-full px-5 py-3 text-sm font-semibold text-brand" role="status">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-line border-t-accent" />
        Loading workspace
      </div>
    </div>
  )
}
