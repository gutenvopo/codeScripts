import { useCallback, useEffect, useState } from "react";
import {
  loadLocationPreference,
  saveLocationPreference,
  type SavedLocationPreference,
} from "../lib/locationPreference";
import { reportAppError } from "../lib/errorLog";
import {
  fetchWeather,
  searchLocation,
  type WeatherData,
} from "../lib/weather";

type GeolocationFailure = Error & {
  code: number | null;
  originalMessage: string | null;
};

function geolocationCode(caught: unknown): number | null {
  if (!caught || typeof caught !== "object" || !("code" in caught)) {
    return null;
  }
  return typeof caught.code === "number" && Number.isFinite(caught.code)
    ? caught.code
    : null;
}

function geolocationMessage(caught: unknown): string | null {
  if (!caught || typeof caught !== "object" || !("message" in caught)) {
    return null;
  }
  return typeof caught.message === "string" && caught.message.trim()
    ? caught.message
    : null;
}

function normalizeGeolocationError(caught: unknown): GeolocationFailure {
  const code = geolocationCode(caught);
  const originalMessage = geolocationMessage(caught);
  let message = originalMessage || "Could not read your current location.";
  if (code === 1) {
    message = "Location access was not allowed. You can use a city instead.";
  } else if (code === 2) {
    message = "Your current location is unavailable. Try again or use a city.";
  } else if (code === 3) {
    message = "Location took too long to respond. Try again or use a city.";
  }

  const error = new Error(message) as GeolocationFailure;
  error.name = "GeolocationError";
  error.code = code;
  error.originalMessage = originalMessage;
  return error;
}

function isGeolocationFailure(caught: unknown): caught is GeolocationFailure {
  return caught instanceof Error && caught.name === "GeolocationError";
}

function reportWeatherError(caught: unknown, source: string): void {
  reportAppError(
    caught,
    source,
    isGeolocationFailure(caught)
      ? {
          code: caught.code,
          originalMessage: caught.originalMessage,
        }
      : undefined,
  );
}

function currentPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(normalizeGeolocationError(
        new Error("This browser does not support device location."),
      ));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, (caught) => {
      reject(normalizeGeolocationError(caught));
    }, {
      enableHighAccuracy: false,
      timeout: 10000,
      maximumAge: 600000,
    });
  });
}

async function currentWeather(): Promise<{
  latitude: number;
  longitude: number;
  weather: WeatherData;
}> {
  const { coords } = await currentPosition();
  const coordinates = {
    latitude: coords.latitude,
    longitude: coords.longitude,
  };
  return {
    ...coordinates,
    weather: await fetchWeather(coordinates),
  };
}

async function permissionState(): Promise<PermissionState | null> {
  if (!navigator.permissions) return null;
  try {
    return (await navigator.permissions.query({ name: "geolocation" })).state;
  } catch {
    return null;
  }
}

function weatherErrorMessage(caught: unknown): string {
  return caught instanceof Error && caught.message
    ? caught.message
    : "Could not load weather.";
}

export function useWeather(uid: string) {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [needsLocation, setNeedsLocation] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadManual = useCallback(async (query: string) => {
    setLoading(true);
    setError(null);
    try {
      const location = await searchLocation(query);
      const nextWeather = await fetchWeather(location, location.name);
      setWeather(nextWeather);
      saveLocationPreference(uid, {
        source: "manual",
        latitude: location.latitude,
        longitude: location.longitude,
        locationName: nextWeather.locationName,
      });
      setNeedsLocation(false);
    } catch (caught) {
      reportAppError(caught, "Weather manual location");
      setError(caught instanceof Error ? caught.message : "Could not load weather.");
    } finally {
      setLoading(false);
    }
  }, [uid]);

  const loadCurrent = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const selection = await currentWeather();
      setWeather(selection.weather);
      saveLocationPreference(uid, {
        source: "device",
        latitude: selection.latitude,
        longitude: selection.longitude,
        locationName: selection.weather.locationName || "Current location",
      });
      setNeedsLocation(false);
    } catch (caught) {
      reportWeatherError(caught, "Weather device location");
      setError(weatherErrorMessage(caught));
      setNeedsLocation(true);
    } finally {
      setLoading(false);
    }
  }, [uid]);

  useEffect(() => {
    let active = true;
    const savedLocation = loadLocationPreference(uid);

    async function restoreLocation(
      preference: SavedLocationPreference,
    ): Promise<void> {
      try {
        const nextWeather = await fetchWeather(
          preference,
          preference.locationName,
        );
        if (!active) return;
        setWeather(nextWeather);
        setNeedsLocation(false);
      } catch (caught) {
        if (!active) return;
        reportAppError(caught, "Weather saved location");
        setError(caught instanceof Error ? caught.message : "Could not load weather.");
        setNeedsLocation(true);
      } finally {
        if (active) setLoading(false);
      }
    }

    async function initialize(): Promise<void> {
      setWeather(null);
      setError(null);
      setLoading(true);
      if (savedLocation) {
        await restoreLocation(savedLocation);
        return;
      }
      const state = navigator.geolocation
        ? await permissionState()
        : "denied";
      if (!active) return;
      if (state === "granted") {
        try {
          const selection = await currentWeather();
          if (!active) return;
          setWeather(selection.weather);
          saveLocationPreference(uid, {
            source: "device",
            latitude: selection.latitude,
            longitude: selection.longitude,
            locationName: selection.weather.locationName || "Current location",
          });
          setNeedsLocation(false);
        } catch (caught) {
          if (!active) return;
          reportWeatherError(caught, "Weather automatic device location");
          setError(weatherErrorMessage(caught));
          setNeedsLocation(true);
        } finally {
          if (active) setLoading(false);
        }
      } else {
        setNeedsLocation(true);
        setLoading(false);
      }
    }

    void initialize();
    return () => {
      active = false;
    };
  }, [uid]);

  const chooseLocation = useCallback(() => {
    setWeather(null);
    setNeedsLocation(true);
    setError(null);
    setLoading(false);
  }, []);

  return {
    weather,
    needsLocation,
    loading,
    error,
    loadManual,
    loadCurrent,
    chooseLocation,
  };
}
