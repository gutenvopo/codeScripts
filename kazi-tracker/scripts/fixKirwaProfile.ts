/* global console, process */

import admin from "firebase-admin";

const TARGET_EMAIL = "kirwaboit@gmail.com";
const FIRST_NAME = "Kirwa";
const LAST_NAME = "Boit";

function initializeAdmin(): void {
  if (!process.env.GOOGLE_APPLICATION_CREDENTIALS) {
    throw new Error("GOOGLE_APPLICATION_CREDENTIALS must point to a service account JSON key.");
  }
  if (admin.apps.length === 0) {
    admin.initializeApp({ credential: admin.credential.applicationDefault() });
  }
}

async function resolveTargetUser(): Promise<admin.auth.UserRecord> {
  let user: admin.auth.UserRecord;
  try {
    user = await admin.auth().getUserByEmail(TARGET_EMAIL);
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(`Could not resolve ${TARGET_EMAIL}: ${detail}`);
  }
  if (user.email?.toLowerCase() !== TARGET_EMAIL) {
    throw new Error(`Resolved account email did not match ${TARGET_EMAIL}; aborting.`);
  }
  return user;
}

async function main(): Promise<void> {
  if (process.argv.slice(2).length > 0) {
    throw new Error("This script accepts no target arguments.");
  }
  initializeAdmin();
  const user = await resolveTargetUser();
  console.log(`Updating ${TARGET_EMAIL} (uid: ${user.uid})`);

  const profileReference = admin
    .firestore()
    .collection("users")
    .doc(user.uid)
    .collection("profile")
    .doc("main");
  if (profileReference.path !== `users/${user.uid}/profile/main`) {
    throw new Error("Refusing to write outside the resolved user's profile.");
  }

  const existingProfile = await profileReference.get();
  await admin.auth().updateUser(user.uid, { displayName: `${FIRST_NAME} ${LAST_NAME}` });
  await profileReference.set(
    {
      firstName: FIRST_NAME,
      lastName: LAST_NAME,
      email: TARGET_EMAIL,
      ...(!existingProfile.get("createdAt")
        ? { createdAt: admin.firestore.FieldValue.serverTimestamp() }
        : {}),
    },
    { merge: true },
  );
  console.log(`Set Auth displayName to "${FIRST_NAME} ${LAST_NAME}" and updated ${profileReference.path}.`);
}

main().catch((error: unknown) => {
  const detail = error instanceof Error ? error.message : String(error);
  console.error(`Profile correction aborted: ${detail}`);
  process.exitCode = 1;
});
