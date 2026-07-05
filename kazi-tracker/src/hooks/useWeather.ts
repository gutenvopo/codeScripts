import { useCallback, useEffect, useState } from "react";
import {
  fetchWeather,
  searchLocation,
  type WeatherData,
} from "../lib/weather";

export function useWeather() {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [needsLocation, setNeedsLocation] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadManual = useCallback(async (query: string) => {
    setLoading(true);
    setError(null);
    try {
      const location = await searchLocation(query);
      setWeather(await fetchWeather(location, location.name));
      setNeedsLocation(false);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load weather.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!navigator.geolocation) {
      setNeedsLocation(true);
      setLoading(false);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        try {
          setWeather(
            await fetchWeather({
              latitude: coords.latitude,
              longitude: coords.longitude,
            }),
          );
        } catch (caught) {
          setError(caught instanceof Error ? caught.message : "Could not load weather.");
          setNeedsLocation(true);
        } finally {
          setLoading(false);
        }
      },
      () => {
        setNeedsLocation(true);
        setLoading(false);
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 },
    );
  }, []);

  return { weather, needsLocation, loading, error, loadManual };
}
