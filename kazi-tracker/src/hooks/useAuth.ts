import { useEffect, useState } from "react";
import {
  GoogleAuthProvider,
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updateProfile,
  type User,
} from "firebase/auth";
import { doc, getDoc, serverTimestamp, setDoc } from "firebase/firestore";
import { auth, db } from "../lib/firebase";
import { reportAppError } from "../lib/errorLog";
import type { UserProfile } from "../types/profile";

const PASSWORD_MIN_LENGTH = 12;
const PASSWORD_REQUIREMENTS =
  /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/;

async function fetchUserProfile(uid: string): Promise<UserProfile | null> {
  const snapshot = await getDoc(doc(db, "users", uid, "profile", "main"));
  return snapshot.exists() ? (snapshot.data() as UserProfile) : null;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const unsubscribe = onAuthStateChanged(auth, (nextUser) => {
      setUser(nextUser);
      setProfile(null);
      setLoading(false);
      if (!nextUser) return;
      void fetchUserProfile(nextUser.uid).then((nextProfile) => {
        if (active && auth.currentUser?.uid === nextUser.uid) {
          setProfile(nextProfile);
        }
      }).catch((caught: unknown) => {
        reportAppError(caught, "User profile load");
        if (active && auth.currentUser?.uid === nextUser.uid) {
          setProfile(null);
        }
      });
    });
    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  async function recordProfile(nextUser: User): Promise<void> {
    await setDoc(
      doc(db, "users", nextUser.uid),
      {
        email: nextUser.email,
        displayName: nextUser.displayName,
        updatedAt: serverTimestamp(),
      },
      { merge: true },
    );
  }

  async function signInWithGoogle(): Promise<void> {
    const credential = await signInWithPopup(auth, new GoogleAuthProvider());
    await recordProfile(credential.user);
  }

  async function signInWithEmail(email: string, password: string): Promise<void> {
    const credential = await signInWithEmailAndPassword(auth, email, password);
    await recordProfile(credential.user);
  }

  async function register(
    email: string,
    password: string,
    firstName: string,
    lastName: string,
  ): Promise<void> {
    const trimmedFirstName = firstName.trim();
    const trimmedLastName = lastName.trim();
    if (!trimmedFirstName || !trimmedLastName) {
      throw new Error("First name and last name are required.");
    }
    if (
      password.length < PASSWORD_MIN_LENGTH
      || !PASSWORD_REQUIREMENTS.test(password)
    ) {
      throw new Error(
        "Password must be at least 12 characters and include uppercase, lowercase, and a number.",
      );
    }
    const credential = await createUserWithEmailAndPassword(auth, email, password);
    const displayName = `${trimmedFirstName} ${trimmedLastName}`;
    await updateProfile(credential.user, { displayName });
    await recordProfile(credential.user);
    await setDoc(doc(db, "users", credential.user.uid, "profile", "main"), {
      firstName: trimmedFirstName,
      lastName: trimmedLastName,
      email: credential.user.email ?? email,
      createdAt: serverTimestamp(),
    });
    setUser(auth.currentUser);
    setProfile(await fetchUserProfile(credential.user.uid));
  }

  return {
    user,
    profile,
    loading,
    signInWithGoogle,
    signInWithEmail,
    register,
    signOut: () => signOut(auth),
  };
}
