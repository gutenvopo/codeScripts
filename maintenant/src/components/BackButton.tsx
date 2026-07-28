import { ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Button } from './Button'

interface BackButtonProps {
  to: string
  label?: string
}

export function BackButton({ to, label = 'Back' }: BackButtonProps) {
  const navigate = useNavigate()
  return (
    <Button variant="quiet" onClick={() => navigate(to)}>
      <ArrowLeft aria-hidden="true" size={18} />
      {label}
    </Button>
  )
}
