import { Construction } from 'lucide-react'
import { BackButton } from './BackButton'
import { PageHeading } from './PageHeading'

interface PlaceholderPageProps {
  title: string
  description: string
  backTo: string
}

export function PlaceholderPage({ title, description, backTo }: PlaceholderPageProps) {
  return (
    <section>
      <PageHeading title={title} action={<BackButton to={backTo} />} />
      <div className="glass-panel flex min-h-64 flex-col items-center justify-center rounded-3xl border-dashed px-6 py-12 text-center">
        <Construction aria-hidden="true" className="mb-5 text-accent" size={36} />
        <h2 className="text-lg font-semibold text-ink">Workspace reserved</h2>
        <p className="mt-2 max-w-md text-sm leading-6 text-white/76">{description}</p>
      </div>
    </section>
  )
}
