const TTL_MS = 12 * 60 * 1000;

type Entry = {
  expiresAt: number;
  json: string;
};

const store = new Map<string, Entry>();

export function dashboardCacheKey(preset: string): string {
  return `dashboard:v1:${preset}`;
}

export function getDashboardCache(key: string): string | null {
  const hit = store.get(key);
  if (!hit) return null;
  if (Date.now() > hit.expiresAt) {
    store.delete(key);
    return null;
  }
  return hit.json;
}

export function setDashboardCache(key: string, json: string): void {
  store.set(key, { expiresAt: Date.now() + TTL_MS, json });
  if (store.size > 20) {
    const oldest = [...store.entries()].sort((a, b) => a[1].expiresAt - b[1].expiresAt)[0];
    if (oldest) store.delete(oldest[0]);
  }
}