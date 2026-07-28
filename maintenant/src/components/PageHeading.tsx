import type { ReactNode } from 'react'

interface PageHeadingProps {
  eyebrow?: string
  title: string
  description?: string
  action?: ReactNode
}

export function PageHeading({ eyebrow, title, description, action }: PageHeadingProps) {
  return (
    <div className="mb-8 flex flex-col gap-5 border-b border-white/22 pb-7 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow ? (
          <p className="mb-2 text-xs font-semibold uppercase text-accent">{eyebrow}</p>
        ) : null}
        <h1 className="text-3xl font-bold text-white sm:text-4xl">{title}</h1>
        {description ? (
          <p className="mt-3 max-w-2xl text-sm leading-6 text-white/78 sm:text-base">
            {description}
          </p>
        ) : null}
      </div>
      {action}
    </div>
  )
}
