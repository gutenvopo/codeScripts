import { History, LogOut, MapPin } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ActionLink } from '../components/ActionLink'
import { Button } from '../components/Button'
import { PageHeading } from '../components/PageHeading'
import { useAuth } from '../context/useAuth'

export function MaintenancePage() {
  const { signOut } = useAuth()
  const navigate = useNavigate()
  const [signingOut, setSigningOut] = useState(false)
  const [error, setError] = useState('')

  const handleSignOut = async () => {
    setError('')
    setSigningOut(true)
    try {
      await signOut()
      navigate('/login', { replace: true })
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to sign out.')
      setSigningOut(false)
    }
  }

  return (
    <section>
      <PageHeading
        eyebrow="Operations"
        title="Preventative Maintenance"
        description="Select a facility area or review previously recorded maintenance data."
      />
      <div className="mx-auto max-w-2xl space-y-4">
        <ActionLink
          to="/location"
          title="Location"
          description="Choose a facility and record instrument readings."
          icon={MapPin}
        />
        <ActionLink
          to="/maintenance/history"
          title="Historic Data"
          description="Review saved readings and maintenance trends."
          icon={History}
        />
        <Button variant="danger" className="w-full" onClick={handleSignOut} disabled={signingOut}>
          <LogOut aria-hidden="true" size={19} />
          {signingOut ? 'Signing out...' : 'Back'}
        </Button>
        {error ? <p className="text-center text-sm text-danger" role="alert">{error}</p> : null}
      </div>
    </section>
  )
}
