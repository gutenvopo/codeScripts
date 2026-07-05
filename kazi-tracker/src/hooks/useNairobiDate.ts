import { useEffect, useState } from "react";
import { formatNairobiDate, nairobiDateKey } from "../lib/nairobiDate";

interface NairobiDate {
  dateKey: string;
  formattedDate: string;
}

function currentNairobiDate(): NairobiDate {
  const now = new Date();
  return {
    dateKey: nairobiDateKey(now),
    formattedDate: formatNairobiDate(now),
  };
}

export function useNairobiDate(): NairobiDate {
  const [date, setDate] = useState(currentNairobiDate);

  useEffect(() => {
    const refresh = (): void => setDate(currentNairobiDate());
    const timer = window.setInterval(refresh, 60_000);
    window.addEventListener("focus", refresh);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", refresh);
    };
  }, []);

  return date;
}
