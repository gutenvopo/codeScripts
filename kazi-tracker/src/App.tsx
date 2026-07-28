import { BrowserRouter, NavLink, Navigate, Route, Routes } from "react-router-dom";
import { BarChart3, FileWarning, ListTodo, LogOut } from "lucide-react";
import { useSyncExternalStore } from "react";
import kaziIcon from "../assets/icon/kazi-icon.svg";
import { LoginScreen } from "./components/LoginScreen";
import { useAuth } from "./hooks/useAuth";
import {
  getErrorLogSnapshot,
  subscribeToErrorLog,
} from "./lib/errorLog";
import { ErrorLogPage } from "./pages/ErrorLogPage";
import { SummaryPage } from "./pages/SummaryPage";
import { TasksPage } from "./pages/TasksPage";

function ErrorLogNavLink() {
  const entries = useSyncExternalStore(
    subscribeToErrorLog,
    getErrorLogSnapshot,
    getErrorLogSnapshot,
  );
  return (
    <NavLink to="/errors">
      <FileWarning size={17} />
      Error Log
      {entries.length > 0 && (
        <span className="error-count" aria-label={`${entries.length} captured errors`}>
          {entries.length > 99 ? "99+" : entries.length}
        </span>
      )}
    </NavLink>
  );
}

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
            <ErrorLogNavLink />
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
            <Route path="/errors" element={<ErrorLogPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
