import { Factory, Warehouse } from 'lucide-react'
import { ActionLink } from '../components/ActionLink'
import { BackButton } from '../components/BackButton'
import { PageHeading } from '../components/PageHeading'

export function LocationPage() {
  return (
    <section>
      <PageHeading
        eyebrow="Facility directory"
        title="Location"
        description="Choose the area where preventative maintenance is being performed."
        action={<BackButton to="/maintenance" />}
      />
      <div className="mx-auto grid max-w-3xl gap-4 md:grid-cols-2">
        <ActionLink
          to="/location/pump-house-1"
          title="Pump House 1"
          description="Record pressure and flow meter readings."
          icon={Warehouse}
        />
        <ActionLink
          to="/location/process-facility"
          title="Process Facility"
          description="Open the process facility workspace."
          icon={Factory}
        />
      </div>
    </section>
  )
}
