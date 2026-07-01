import { useEffect, useState } from "react";

export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  shouldPoll: (data: T) => boolean,
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;

    const tick = async () => {
      try {
        const result = await fetcher();
        if (!active) return;
        setData(result);
        setError(null);
        setLoading(false);
        if (shouldPoll(result)) {
          timer = setTimeout(tick, intervalMs);
        }
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Poll failed");
        setLoading(false);
      }
    };

    tick();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [fetcher, intervalMs, shouldPoll]);

  return { data, error, loading };
}
