import { useState, type FormEvent } from "react";
import { LocateFixed, MapPin } from "lucide-react";
import { useNairobiDate } from "../hooks/useNairobiDate";
import { useWeather } from "../hooks/useWeather";
import { weatherCondition, weatherKind, type WeatherCondition } from "../lib/weather";

const rainDropPositions: Record<number, number[]> = {
  5: [8, 13, 18, 23, 28],
  6: [7, 11.5, 16, 20, 24.5, 29],
  7: [6.5, 10.5, 14.5, 18, 21.5, 25.5, 29.5],
};

function RainChanceIcon({ probability }: { probability: number }) {
  const intensity = probability < 20 ? "low" : probability <= 60 ? "moderate" : "high";
  const dropCount = intensity === "low" ? 5 : intensity === "moderate" ? 6 : 7;
  const dropPositions = rainDropPositions[dropCount];

  return (
    <svg
      className={`rain-indicator rain-indicator-${intensity}`}
      viewBox="0 0 36 38"
      role="img"
      aria-label={`${intensity} rain animation`}
    >
      <path
        className="rain-indicator-cloud"
        d="M9 19.5h17.2a5.3 5.3 0 0 0 .4-10.6 8 8 0 0 0-15.2-1.6A6.2 6.2 0 0 0 9 19.5Z"
      />
      <g className="rain-indicator-drops">
        {dropPositions.map((x, index) => (
          <line
            key={x}
            className={`rain-drop rain-drop-${index + 1}`}
            x1={x}
            y1="23"
            x2={x - 1.5}
            y2="28"
          />
        ))}
      </g>
    </svg>
  );
}

const cloudPath =
  "M16 39h32a8 8 0 0 0 .5-16 12.5 12.5 0 0 0-23.8-2.5A9.7 9.7 0 0 0 16 39Z";

function SunShape({ compact = false }: { compact?: boolean }) {
  return (
    <g className={`condition-sun ${compact ? "condition-sun-compact" : ""}`}>
      <g className="condition-sun-rays">
        <path d="M32 6v7M32 51v7M6 32h7M51 32h7M13.6 13.6l5 5M45.4 45.4l5 5M50.4 13.6l-5 5M18.6 45.4l-5 5" />
      </g>
      <circle className="condition-sun-core" cx="32" cy="32" r="11" />
    </g>
  );
}

function MainRainDrops() {
  return (
    <g className="condition-rain">
      {[20, 26, 32, 38, 44].map((x, index) => (
        <line
          key={x}
          className={`condition-rain-drop condition-rain-drop-${index + 1}`}
          x1={x}
          y1="42"
          x2={x - 2}
          y2="49"
        />
      ))}
    </g>
  );
}

function WeatherGlyph({ code }: { code: number }) {
  const condition: WeatherCondition = weatherCondition(code);

  if (condition === "clear") {
    return (
      <svg className="condition-glyph" viewBox="0 0 64 64" role="img" aria-label="Clear skies">
        <SunShape />
      </svg>
    );
  }

  if (condition === "partly cloudy") {
    return (
      <svg className="condition-glyph" viewBox="0 0 64 64" role="img" aria-label="Partly cloudy">
        <g className="condition-partly-sun"><SunShape compact /></g>
        <path className="condition-cloud condition-cloud-drift" d={cloudPath} />
      </svg>
    );
  }

  if (condition === "fog") {
    return (
      <svg className="condition-glyph" viewBox="0 0 64 64" role="img" aria-label="Foggy">
        <path className="condition-cloud condition-cloud-muted" d={cloudPath} />
        <g className="condition-fog">
          <path d="M12 45h36" />
          <path d="M18 51h34" />
          <path d="M10 57h30" />
        </g>
      </svg>
    );
  }

  if (condition === "drizzle" || condition === "rain" || condition === "showers") {
    return (
      <svg className="condition-glyph" viewBox="0 0 64 64" role="img" aria-label={`${condition} weather`}>
        <path className="condition-cloud condition-cloud-drift" d={cloudPath} />
        <MainRainDrops />
      </svg>
    );
  }

  if (condition === "thunder") {
    return (
      <svg className="condition-glyph" viewBox="0 0 64 64" role="img" aria-label="Thunderstorm">
        <path className="condition-cloud condition-cloud-storm" d={cloudPath} />
        <MainRainDrops />
        <path className="condition-lightning" d="M35 38h-8l3 8h-5l4 12 10-15h-6Z" />
      </svg>
    );
  }

  if (condition === "snow") {
    return (
      <svg className="condition-glyph" viewBox="0 0 64 64" role="img" aria-label="Snowy">
        <path className="condition-cloud condition-cloud-drift" d={cloudPath} />
        <g className="condition-snow">
          {[20, 27, 34, 41, 47].map((x, index) => (
            <circle
              key={x}
              className={`condition-snowflake condition-snowflake-${index + 1}`}
              cx={x}
              cy="45"
              r="1.7"
            />
          ))}
        </g>
      </svg>
    );
  }

  return (
    <svg className="condition-glyph" viewBox="0 0 64 64" role="img" aria-label="Cloudy">
      <path className="condition-cloud condition-cloud-back" d="M9 34h29a7 7 0 0 0 .4-14 11 11 0 0 0-20.8-2.1A8.5 8.5 0 0 0 9 34Z" />
      <path className="condition-cloud condition-cloud-drift" d={cloudPath} />
    </svg>
  );
}

export function WeatherWidget({ uid }: { uid: string }) {
  const {
    weather,
    needsLocation,
    loading,
    error,
    loadManual,
    loadCurrent,
    chooseLocation,
  } = useWeather(uid);
  const { formattedDate } = useNairobiDate();
  const [query, setQuery] = useState("");
  const celsius = weather ? Math.round(weather.temperature) : null;
  const fahrenheit = celsius === null ? null : Math.round((celsius * 9) / 5 + 32);

  function submit(event: FormEvent): void {
    event.preventDefault();
    if (query.trim()) void loadManual(query.trim());
  }

  return (
    <section className="weather-card">
      <div className="weather-glow" />
      {loading && !weather ? (
        <div className="weather-subpanel weather-loading-panel">
          <div className="weather-loading">Reading the sky…</div>
        </div>
      ) : weather ? (
        <>
          <div className="weather-subpanel weather-temperature-panel">
            <div className={`weather-icon weather-${weatherKind(weather.weatherCode)}`}>
              <WeatherGlyph code={weather.weatherCode} />
            </div>
            <div className="weather-place">
              <time className="weather-panel-date">{formattedDate}</time>
              <span><MapPin size={14} /> {weather.locationName}</span>
              <div className="weather-temperature">
                <strong>{celsius}°C</strong>
                <b aria-hidden="true">·</b>
                <em>{fahrenheit}°F</em>
              </div>
            </div>
          </div>
          <div className="weather-subpanel weather-summary-panel">
            <span className="weather-panel-label">Weather today</span>
            {weather.daySummary && (
              <p className="weather-day-summary">{weather.daySummary}</p>
            )}
          </div>
          <div
            className="weather-subpanel rain-chance"
            title={`Peak: ${weather.precipitationProbabilityMax}%`}
          >
            <span>Chance of rain:</span>
            <div className="rain-chance-value">
              <strong>{weather.precipitationProbability}%</strong>
              <RainChanceIcon probability={weather.precipitationProbability} />
            </div>
          </div>
        </>
      ) : (
        <div className="manual-location">
          <div>
            <span className="eyebrow">Local forecast</span>
            <h2>Where are you planning from?</h2>
            {error && <p>{error}</p>}
          </div>
          <div className="location-options">
            {navigator.geolocation && (
              <button
                className="current-location-button"
                type="button"
                onClick={() => void loadCurrent()}
              >
                <LocateFixed size={16} />
                Use current location
              </button>
            )}
            <form onSubmit={submit}>
              <MapPin size={18} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Nairobi, Kenya"
                aria-label="City or location"
              />
              <button type="submit">Use city</button>
            </form>
          </div>
        </div>
      )}
      {weather && !needsLocation && (
        <button className="weather-change" onClick={chooseLocation}>
          Change location
        </button>
      )}
    </section>
  );
}
