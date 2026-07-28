import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { AppErrorBoundary } from "./components/AppErrorBoundary";
import {
  installGlobalErrorCapture,
  reportAppError,
} from "./lib/errorLog";
import "./styles/index.css";

installGlobalErrorCapture();

createRoot(document.getElementById("root")!, {
  onUncaughtError: (error, info) => {
    reportAppError(error, "React uncaught error", {
      componentStack: info.componentStack,
    });
  },
  onRecoverableError: (error, info) => {
    reportAppError(error, "React recoverable error", {
      componentStack: info.componentStack,
    });
  },
}).render(
  <StrictMode>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  </StrictMode>,
);
