export type LocationSource = "device" | "manual";

export interface SavedLocationPreference {
  source: LocationSource;
  latitude: number;
  longitude: number;
  locationName: string;
}

const storagePrefix = "kazi-tracker:location:";

function storageKey(uid: string): string {
  return `${storagePrefix}${uid}`;
}

function isSavedLocation(value: unknown): value is SavedLocationPreference {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<SavedLocationPreference>;
  return (
    (candidate.source === "device" || candidate.source === "manual")
    && typeof candidate.latitude === "number"
    && Number.isFinite(candidate.latitude)
    && candidate.latitude >= -90
    && candidate.latitude <= 90
    && typeof candidate.longitude === "number"
    && Number.isFinite(candidate.longitude)
    && candidate.longitude >= -180
    && candidate.longitude <= 180
    && typeof candidate.locationName === "string"
    && candidate.locationName.length > 0
    && candidate.locationName.length <= 300
  );
}

export function loadLocationPreference(
  uid: string,
): SavedLocationPreference | null {
  try {
    const rawValue = window.localStorage.getItem(storageKey(uid));
    if (!rawValue) return null;
    const parsedValue: unknown = JSON.parse(rawValue);
    return isSavedLocation(parsedValue) ? parsedValue : null;
  } catch {
    return null;
  }
}

export function saveLocationPreference(
  uid: string,
  preference: SavedLocationPreference,
): void {
  const roundedPreference = {
    ...preference,
    latitude: Number(preference.latitude.toFixed(3)),
    longitude: Number(preference.longitude.toFixed(3)),
  };
  try {
    window.localStorage.setItem(
      storageKey(uid),
      JSON.stringify(roundedPreference),
    );
  } catch {
    // Weather still works when browser storage is unavailable.
  }
}
