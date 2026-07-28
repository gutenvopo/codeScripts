import { Outlet } from 'react-router-dom'
import { BrandLogo } from './BrandLogo'

export function AppLayout() {
  return (
    <div className="app-shell min-h-screen text-ink">
      <header className="border-b border-white/20 bg-gradient-to-r from-canvas/86 via-brand/58 to-white/28 backdrop-blur-xl">
        <div className="mx-auto flex min-h-40 w-full max-w-6xl flex-col items-center justify-center gap-4 px-4 py-5 sm:flex-row sm:justify-between sm:px-6">
          <BrandLogo />
          <span className="hidden rounded-full border border-white/25 bg-white/12 px-5 py-2 text-xs font-semibold uppercase text-white/84 shadow-glow sm:block">
            Maintenance operations
          </span>
        </div>
      </header>
      <main className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 sm:py-12">
        <Outlet />
      </main>
    </div>
  )
}
