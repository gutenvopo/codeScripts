import type { Timestamp } from "firebase/firestore";

export interface UserProfile {
  firstName: string;
  lastName: string;
  email: string;
  createdAt: Timestamp;
}
