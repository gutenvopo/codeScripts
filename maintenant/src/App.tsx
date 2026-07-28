import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/AppLayout'
import { LoadingScreen } from './components/LoadingScreen'
import { PlaceholderPage } from './components/PlaceholderPage'
import { ProtectedRoute } from './components/ProtectedRoute'
import { useAuth } from './context/useAuth'
import { LocationPage } from './pages/LocationPage'
import { LoginPage } from './pages/LoginPage'
import { MaintenancePage } from './pages/MaintenancePage'
import { PumpHousePage } from './pages/PumpHousePage'

function HomeRedirect() {
  const { session, loading } = useAuth()
  if (loading) return <LoadingScreen />
  return <Navigate to={session ? '/maintenance' : '/login'} replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/maintenance" element={<MaintenancePage />} />
          <Route
            path="/maintenance/history"
            element={
              <PlaceholderPage
                title="Historic Data"
                description="Saved readings and maintenance trends will appear here in a future release."
                backTo="/maintenance"
              />
            }
          />
          <Route path="/location" element={<LocationPage />} />
          <Route
            path="/location/process-facility"
            element={
              <PlaceholderPage
                title="Process Facility"
                description="Process Facility instruments and inspection routes will be configured here."
                backTo="/location"
              />
            }
          />
          <Route path="/location/pump-house-1" element={<PumpHousePage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
