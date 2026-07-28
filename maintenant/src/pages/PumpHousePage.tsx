import { CheckCircle2, Gauge, Save } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { BackButton } from '../components/BackButton'
import { Button } from '../components/Button'
import { PageHeading } from '../components/PageHeading'
import { useAuth } from '../context/useAuth'
import { supabase } from '../lib/supabase'

interface ReadingFieldProps {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
}

function ReadingField({ id, label, value, onChange }: ReadingFieldProps) {
  return (
    <div className="grid grid-cols-[minmax(8.5rem,1fr)_minmax(7rem,1fr)] items-center gap-4 border-b border-white/18 px-4 py-5 last:border-b-0 sm:grid-cols-[minmax(14rem,1.4fr)_minmax(12rem,1fr)] sm:px-6">
      <label htmlFor={id} className="text-sm font-semibold leading-5 text-ink sm:text-base">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type="number"
          inputMode="decimal"
          step="any"
          required
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="field-control min-h-12 w-full rounded-2xl px-4 py-3 pr-11 text-right text-base font-semibold text-ink outline-none transition-colors placeholder:font-normal placeholder:text-muted/60 focus:border-accent focus:ring-1 focus:ring-accent"
          placeholder="0.00"
        />
        <Gauge className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" size={18} />
      </div>
    </div>
  )
}

export function PumpHousePage() {
  const { session } = useAuth()
  const [pressure, setPressure] = useState('')
  const [flow, setFlow] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  const handleSave = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setSaved(false)

    const pressureValue = Number(pressure)
    const flowValue = Number(flow)
    if (!Number.isFinite(pressureValue) || !Number.isFinite(flowValue)) {
      setError('Enter a valid numeric value for both instruments.')
      return
    }
    if (!supabase || !session) {
      setError('The authenticated Supabase session is unavailable. Please sign in again.')
      return
    }

    setSaving(true)
    const { error: insertError } = await supabase.from('readings').insert([
      {
        user_id: session.user.id,
        location: 'Pump House 1',
        instrument_tag: 'PT1',
        value: pressureValue,
      },
      {
        user_id: session.user.id,
        location: 'Pump House 1',
        instrument_tag: 'FM1',
        value: flowValue,
      },
    ])
    setSaving(false)

    if (insertError) {
      setError(insertError.message)
      return
    }
    setPressure('')
    setFlow('')
    setSaved(true)
  }

  return (
    <section>
      <PageHeading
        eyebrow="Instrument readings"
        title="Pump House 1"
        description="Enter the current field values. Each save records both readings with your user ID and the current timestamp."
        action={<BackButton to="/location" />}
      />

      <form className="mx-auto max-w-3xl" onSubmit={handleSave}>
        <div className="glass-panel overflow-hidden rounded-[1.75rem]">
          <ReadingField id="pressure-pt1" label="Pressure Transmitter PT1" value={pressure} onChange={setPressure} />
          <ReadingField id="flow-fm1" label="Flow Meter FM1" value={flow} onChange={setFlow} />
        </div>

        <div className="mt-6 flex flex-col-reverse gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-h-6" aria-live="polite">
            {saved ? (
              <p className="flex items-center gap-2 text-sm font-medium text-success" role="status">
                <CheckCircle2 aria-hidden="true" size={18} />
                Readings saved successfully.
              </p>
            ) : null}
            {error ? <p className="text-sm text-danger" role="alert">{error}</p> : null}
          </div>
          <Button type="submit" className="sm:min-w-48" disabled={saving}>
            <Save aria-hidden="true" size={19} />
            {saving ? 'Saving...' : 'Save Readings'}
          </Button>
        </div>
      </form>
    </section>
  )
}
