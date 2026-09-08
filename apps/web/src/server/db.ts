import { createDb } from "@noema/core";

// The skeleton owns exactly one DB connection (AC4: «одна DB-инициализация»).
// PostgreSQL (ADR-001): чистый JS-драйвер — SSR-бандл не ломается.
// T5 ставит данные в Docker volume; T2+ добавляют доменные схемы на этот пул.
let db: ReturnType<typeof createDb> | undefined;

export function getDb(): ReturnType<typeof createDb> {
  if (!db) db = createDb();
  return db;
}

/** Server-side proof that the web-skeleton ↔ core seam is wired. */
export async function dbHealth(): Promise<{ ok: boolean }> {
  try {
    const n = await getDb().ping();
    return { ok: n === 1 };
  } catch {
    // БД недоступна (нет запущенного PG) — страница не должна падать (AC1).
    return { ok: false };
  }
}