import { useState, type FormEvent } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Chrome, Sparkles } from "lucide-react";
import kaziIcon from "../../assets/icon/kazi-icon.svg";

interface LoginScreenProps {
  onGoogle: () => Promise<void>;
  onEmail: (email: string, password: string) => Promise<void>;
  onRegister: (
    email: string,
    password: string,
    firstName: string,
    lastName: string,
  ) => Promise<void>;
}

function safeAuthenticationError(
  caught: unknown,
  registering: boolean,
): string {
  const code =
    typeof caught === "object"
    && caught !== null
    && "code" in caught
    && typeof caught.code === "string"
      ? caught.code
      : "";
  const message = caught instanceof Error ? caught.message : "";

  if (message.startsWith("Password must be at least 12 characters")) {
    return message;
  }
  if (code === "auth/too-many-requests") {
    return "Too many attempts. Please wait a while and try again.";
  }
  if (code === "auth/network-request-failed") {
    return "Unable to reach the authentication service. Check your connection.";
  }
  return registering
    ? "Unable to create the account with those details."
    : "Unable to sign in with those credentials.";
}

export function LoginScreen({ onGoogle, onEmail, onRegister }: LoginScreenProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [registering, setRegistering] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(action: () => Promise<void>): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (caught) {
      setError(safeAuthenticationError(caught, registering));
    } finally {
      setBusy(false);
    }
  }

  function submit(event: FormEvent): void {
    event.preventDefault();
    void run(() =>
      registering
        ? onRegister(email, password, firstName.trim(), lastName.trim())
        : onEmail(email, password),
    );
  }

  return (
    <div className="login-page">
      <motion.section
        className="login-brand"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <div className="brand-mark large">
          <img src={kaziIcon} alt="" aria-hidden="true" />
        </div>
        <span className="eyebrow">Clear work. Quiet mind.</span>
        <h1>Kazi<br />Tracker</h1>
        <p>A focused command centre for everything worth finishing.</p>
        <div className="login-features">
          <span><Sparkles size={15} /> Priorities that stay visible</span>
          <span><Sparkles size={15} /> Progress that feels rewarding</span>
          <span><Sparkles size={15} /> One account across every device</span>
        </div>
      </motion.section>
      <motion.section
        className="login-card"
        initial={{ opacity: 0, y: 22 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.12 }}
      >
        <span className="eyebrow">{registering ? "Start fresh" : "Welcome back"}</span>
        <h2>{registering ? "Create your workspace" : "Sign in to your day"}</h2>
        <button
          className="google-button"
          disabled={busy}
          onClick={() => void run(onGoogle)}
        >
          <Chrome size={18} />
          Continue with Google
        </button>
        <div className="divider"><span>or use email</span></div>
        <form onSubmit={submit}>
          {registering && (
            <div className="signup-name-grid">
              <label>
                First name
                <input
                  value={firstName}
                  onChange={(event) => setFirstName(event.target.value)}
                  autoComplete="given-name"
                  required
                />
              </label>
              <label>
                Last name
                <input
                  value={lastName}
                  onChange={(event) => setLastName(event.target.value)}
                  autoComplete="family-name"
                  required
                />
              </label>
            </div>
          )}
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder={registering ? "12+ characters" : "Your password"}
              minLength={registering ? 12 : 6}
              pattern={registering ? "(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).{12,}" : undefined}
              title={
                registering
                  ? "Use at least 12 characters with uppercase, lowercase, and a number."
                  : undefined
              }
              required
            />
          </label>
          {error && <p className="form-error">{error}</p>}
          <button className="primary-button login-submit" type="submit" disabled={busy}>
            {busy ? "Connecting…" : registering ? "Create account" : "Sign in"}
            {!busy && <ArrowRight size={17} />}
          </button>
        </form>
        <button className="switch-auth" onClick={() => setRegistering((value) => !value)}>
          {registering ? "Already have an account? Sign in" : "New here? Create an account"}
        </button>
      </motion.section>
    </div>
  );
}
