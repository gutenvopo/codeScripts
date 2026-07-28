import { Component, type ErrorInfo, type ReactNode } from "react";
import { reportAppError } from "../lib/errorLog";

interface AppErrorBoundaryProps {
  children: ReactNode;
}

interface AppErrorBoundaryState {
  failed: boolean;
}

export class AppErrorBoundary extends Component<
  AppErrorBoundaryProps,
  AppErrorBoundaryState
> {
  state: AppErrorBoundaryState = { failed: false };

  static getDerivedStateFromError(): AppErrorBoundaryState {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    reportAppError(error, "React error boundary", {
      componentStack: info.componentStack,
    });
  }

  render(): ReactNode {
    if (!this.state.failed) return this.props.children;
    return (
      <main className="fatal-error-page">
        <section className="fatal-error-card">
          <span className="eyebrow">Application error</span>
          <h1>Kazi Tracker hit an unexpected problem.</h1>
          <p>
            The verbose diagnostic was saved locally in the Error Log. Reload
            the app to continue.
          </p>
          <button
            type="button"
            className="primary-button"
            onClick={() => window.location.reload()}
          >
            Reload application
          </button>
        </section>
      </main>
    );
  }
}
