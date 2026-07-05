export interface WeatherData {
  temperature: number;
  precipitationProbability: number;
  precipitationProbabilityMax: number;
  weatherCode: number;
  locationName: string;
  daySummary: string | null;
}

export interface Coordinates {
  latitude: number;
  longitude: number;
}

interface GeocodingResult {
  name: string;
  country?: string;
  admin1?: string;
  latitude: number;
  longitude: number;
}

export type WeatherKind = "sunny" | "cloudy" | "rainy" | "stormy" | "snowy";
export type WeatherCondition =
  | "clear"
  | "partly cloudy"
  | "cloudy"
  | "fog"
  | "drizzle"
  | "rain"
  | "showers"
  | "thunder"
  | "snow";

export interface HourlyForecast {
  time?: string[];
  temperature_2m?: number[];
  weather_code?: number[];
  precipitation_probability?: number[];
}

export interface DailyForecast {
  precipitation_probability_mean?: number[];
  precipitation_probability_max?: number[];
  temperature_2m_max?: number[];
  temperature_2m_min?: number[];
  sunrise?: string[];
  sunset?: string[];
  weather_code?: number[];
}

interface DaylightPoint {
  time: string;
  condition: WeatherCondition;
  precipitationProbability: number;
}

const conditionSeverity: WeatherCondition[] = [
  "clear",
  "partly cloudy",
  "cloudy",
  "fog",
  "drizzle",
  "rain",
  "snow",
  "showers",
  "thunder",
];

export function weatherCondition(code: number): WeatherCondition {
  if (code === 0) return "clear";
  if (code === 1 || code === 2) return "partly cloudy";
  if (code === 3) return "cloudy";
  if (code === 45 || code === 48) return "fog";
  if (code >= 51 && code <= 57) return "drizzle";
  if (code >= 61 && code <= 67) return "rain";
  if ((code >= 71 && code <= 77) || code === 85 || code === 86) return "snow";
  if (code >= 80 && code <= 82) return "showers";
  if (code >= 95) return "thunder";
  return "cloudy";
}

export function weatherKind(code: number): WeatherKind {
  const condition = weatherCondition(code);
  if (condition === "clear") return "sunny";
  if (["partly cloudy", "cloudy", "fog"].includes(condition)) return "cloudy";
  if (condition === "thunder") return "stormy";
  if (condition === "snow") return "snowy";
  return "rainy";
}

function dominantCondition(points: DaylightPoint[]): WeatherCondition | null {
  if (points.length === 0) return null;
  const counts = new Map<WeatherCondition, number>();
  points.forEach(({ condition }) => {
    counts.set(condition, (counts.get(condition) ?? 0) + 1);
  });
  return [...counts.entries()].sort(
    ([left, leftCount], [right, rightCount]) =>
      rightCount - leftCount ||
      conditionSeverity.indexOf(right) - conditionSeverity.indexOf(left),
  )[0][0];
}

function minutesFromIso(value: string): number {
  const time = value.split("T")[1] ?? "";
  const [hour, minute] = time.split(":").map(Number);
  return Number.isFinite(hour) && Number.isFinite(minute)
    ? hour * 60 + minute
    : -1;
}

function daylightPoints(
  hourly: HourlyForecast | undefined,
  daily: DailyForecast | undefined,
): DaylightPoint[] {
  const sunrise = daily?.sunrise?.[0];
  const sunset = daily?.sunset?.[0];
  if (!sunrise || !sunset || !hourly?.time || !hourly.weather_code) return [];
  return hourly.time.flatMap((time, index) => {
    const code = hourly.weather_code?.[index];
    if (
      time < sunrise ||
      time > sunset ||
      typeof code !== "number" ||
      !Number.isFinite(code)
    ) return [];
    return [{
      time,
      condition: weatherCondition(code),
      precipitationProbability: hourly.precipitation_probability?.[index] ?? 0,
    }];
  });
}

function conditionSentence(points: DaylightPoint[]): string | null {
  const segments = [
    { name: "morning", points: points.filter((point) => minutesFromIso(point.time) < 660) },
    {
      name: "afternoon",
      points: points.filter((point) => {
        const minutes = minutesFromIso(point.time);
        return minutes >= 660 && minutes < 960;
      }),
    },
    { name: "evening", points: points.filter((point) => minutesFromIso(point.time) >= 960) },
  ];
  const conditions = segments.flatMap((segment) => {
    const condition = dominantCondition(segment.points);
    return condition ? [{ name: segment.name, condition }] : [];
  });
  if (conditions.length === 0) return null;
  if (conditions.every(({ condition }) => condition === conditions[0].condition)) {
    const condition = conditions[0].condition;
    return condition === "clear"
      ? "Mostly sunny all day."
      : `${condition[0].toUpperCase()}${condition.slice(1)} all day.`;
  }
  const phrases = conditions.map(({ name, condition }, index) => {
    const phrase = name === "evening" ? `${condition} by evening` : `${condition} ${name}`;
    return index === 0 ? `${phrase[0].toUpperCase()}${phrase.slice(1)}` : phrase;
  });
  return `${phrases.join(", ")}.`;
}

function temperatureSentence(daily: DailyForecast | undefined): string | null {
  const high = daily?.temperature_2m_max?.[0];
  const low = daily?.temperature_2m_min?.[0];
  if (
    typeof high !== "number" ||
    typeof low !== "number" ||
    !Number.isFinite(high) ||
    !Number.isFinite(low)
  ) return null;
  return `High ${Math.round(high)}°C, low ${Math.round(low)}°C.`;
}

export function buildDaySummary(
  hourly: HourlyForecast | undefined,
  daily: DailyForecast | undefined,
): string | null {
  const points = daylightPoints(hourly, daily);
  const fallbackCode = daily?.weather_code?.[0];
  const conditions = conditionSentence(points) ??
    (typeof fallbackCode === "number" && Number.isFinite(fallbackCode)
      ? `${weatherCondition(fallbackCode)[0].toUpperCase()}${weatherCondition(fallbackCode).slice(1)} today.`
      : null);
  const temperatures = temperatureSentence(daily);
  const maxDaytimeRain = Math.max(0, ...points.map((point) => point.precipitationProbability));
  const alreadyWet = points.some((point) =>
    ["drizzle", "rain", "showers", "thunder"].includes(point.condition),
  );
  const rainNote = !alreadyWet && maxDaytimeRain >= 55
    ? "Rain likely later."
    : !alreadyWet && maxDaytimeRain >= 35
      ? "Some rain possible."
      : null;
  const summary = [conditions, temperatures, rainNote].filter(Boolean).join(" ");
  return summary || null;
}

export async function searchLocation(query: string): Promise<Coordinates & { name: string }> {
  const url = new URL("https://geocoding-api.open-meteo.com/v1/search");
  url.searchParams.set("name", query);
  url.searchParams.set("count", "1");
  url.searchParams.set("language", "en");
  const response = await fetch(url);
  if (!response.ok) throw new Error("Location search is unavailable.");
  const data = (await response.json()) as { results?: GeocodingResult[] };
  const result = data.results?.[0];
  if (!result) throw new Error("We could not find that location.");
  return {
    latitude: result.latitude,
    longitude: result.longitude,
    name: [result.name, result.admin1, result.country].filter(Boolean).join(", "),
  };
}

async function reverseGeocode({ latitude, longitude }: Coordinates): Promise<string> {
  const url = new URL("https://api.bigdatacloud.net/data/reverse-geocode-client");
  url.searchParams.set("latitude", String(latitude));
  url.searchParams.set("longitude", String(longitude));
  url.searchParams.set("localityLanguage", "en");
  const response = await fetch(url);
  if (!response.ok) return "Current location";
  const data = (await response.json()) as {
    city?: string;
    locality?: string;
    principalSubdivision?: string;
    countryName?: string;
  };
  return [
    data.city ?? data.locality,
    data.principalSubdivision,
    data.countryName,
  ]
    .filter(Boolean)
    .join(", ");
}

export async function fetchWeather(
  coordinates: Coordinates,
  knownName?: string,
): Promise<WeatherData> {
  const url = new URL("https://api.open-meteo.com/v1/forecast");
  url.searchParams.set("latitude", String(coordinates.latitude));
  url.searchParams.set("longitude", String(coordinates.longitude));
  url.searchParams.set("current", "temperature_2m,weather_code");
  url.searchParams.set(
    "hourly",
    "temperature_2m,weather_code,precipitation_probability",
  );
  url.searchParams.set(
    "daily",
    "precipitation_probability_mean,precipitation_probability_max,temperature_2m_max,temperature_2m_min,sunrise,sunset,weather_code",
  );
  url.searchParams.set("timezone", "auto");
  const response = await fetch(url);
  if (!response.ok) throw new Error("Weather data is unavailable.");
  const data = (await response.json()) as {
    current: { temperature_2m: number; weather_code: number };
    hourly?: HourlyForecast;
    daily?: DailyForecast;
  };
  return {
    temperature: Math.round(data.current.temperature_2m),
    weatherCode: data.current.weather_code,
    precipitationProbability: Math.round(
      data.daily?.precipitation_probability_mean?.[0] ?? 0,
    ),
    precipitationProbabilityMax: Math.round(
      data.daily?.precipitation_probability_max?.[0] ?? 0,
    ),
    locationName: knownName || (await reverseGeocode(coordinates)),
    daySummary: buildDaySummary(data.hourly, data.daily),
  };
}
