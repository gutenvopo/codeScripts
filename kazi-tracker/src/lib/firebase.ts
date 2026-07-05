import { initializeApp } from "firebase/app";
import {
  ReCaptchaEnterpriseProvider,
  initializeAppCheck,
} from "firebase/app-check";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

const missingKeys = Object.entries(firebaseConfig)
  .filter(([, value]) => !value)
  .map(([key]) => key);

if (missingKeys.length > 0) {
  throw new Error(`Missing Firebase configuration: ${missingKeys.join(", ")}`);
}

export const firebaseApp = initializeApp(firebaseConfig);
const appCheckSiteKey =
  import.meta.env.VITE_FIREBASE_APPCHECK_RECAPTCHA_ENTERPRISE_SITE_KEY?.trim();

export const appCheck = (() => {
  if (!appCheckSiteKey) {
    console.warn("App Check disabled: site key not set");
    return null;
  }

  if (
    import.meta.env.DEV
    && import.meta.env.VITE_FIREBASE_APPCHECK_DEBUG === "true"
    && typeof self !== "undefined"
  ) {
    (self as typeof self & { FIREBASE_APPCHECK_DEBUG_TOKEN: boolean })
      .FIREBASE_APPCHECK_DEBUG_TOKEN = true;
  }

  return initializeAppCheck(firebaseApp, {
    provider: new ReCaptchaEnterpriseProvider(appCheckSiteKey),
    isTokenAutoRefreshEnabled: true,
  });
})();
export const auth = getAuth(firebaseApp);
export const db = getFirestore(firebaseApp);
