import { BrowserRouter, NavLink, Navigate, Route, Routes } from "react-router-dom";
import { BarChart3, ListTodo, LogOut } from "lucide-react";
import kaziIcon from "../assets/icon/kazi-icon.svg";
import { LoginScreen } from "./components/LoginScreen";
import { useAuth } from "./hooks/useAuth";
import { SummaryPage } from "./pages/SummaryPage";
import { TasksPage } from "./pages/TasksPage";

export default function App() {
  const {
    user,
    profile,
    loading,
    signInWithGoogle,
    signInWithEmail,
    register,
    signOut,
  } = useAuth();

  if (loading) {
    return (
      <div className="app-loader">
        <div className="loader-ring" />
        <span>Kazi Tracker</span>
      </div>
    );
  }

  if (!user) {
    return (
      <LoginScreen
        onGoogle={signInWithGoogle}
        onEmail={signInWithEmail}
        onRegister={register}
      />
    );
  }

  return (
    <BrowserRouter>
      <div className="app-shell">
        <header className="topbar">
          <NavLink to="/" className="wordmark">
            <span className="brand-mark">
              <img src={kaziIcon} alt="" aria-hidden="true" />
            </span>
            <span>Kazi <strong>Tracker</strong></span>
          </NavLink>
          <nav aria-label="Primary navigation">
            <NavLink to="/" end>
              <ListTodo size={17} />
              Tasks
            </NavLink>
            <NavLink to="/summary">
              <BarChart3 size={17} />
              Summary
            </NavLink>
          </nav>
          <div className="account">
            <span className="account-name">
              {profile
                ? `${profile.firstName} ${profile.lastName}`
                : user.displayName || user.email?.split("@")[0]}
            </span>
            <button
              className="logout-button"
              onClick={() => void signOut()}
              aria-label="Logout"
            >
              <LogOut size={17} />
              <span>Logout</span>
            </button>
          </div>
        </header>
        <div className="content-shell">
          <Routes>
            <Route path="/" element={<TasksPage uid={user.uid} profile={profile} />} />
            <Route path="/summary" element={<SummaryPage uid={user.uid} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
