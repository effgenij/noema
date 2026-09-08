import { drizzle, type NodePgDatabase } from "drizzle-orm/node-postgres";
import pg from "pg";

export interface DbConfig {
  /** PostgreSQL connection string (default: env DATABASE_URL, или `postgres://...` из тестов). */
  connectionString?: string;
  /** Max pool size (web + stdio MCP делят один PG; default 10). */
  max?: number;
}

export interface Db {
  db: NodePgDatabase;
  pool: pg.Pool;
  close: () => Promise<void>;
  /** Серверный ping: вернуть 1, если соединение живо. */
  ping: () => Promise<number>;
}

/**
 * Единственная точка инициализации БД noema (AC4: «одна DB-инициализация»).
 *
 * PostgreSQL (ADR-001): чистый JS-драйвер `pg` — не ломает SSR-бандл
 * (в отличие от нативного better-sqlite3), web и stdio-MCP делят один PG
 * конкурентно. Пул вынесен наружу, чтобы скелет владел одним соединением.
 */
export function createDb(config: DbConfig = {}): Db {
  const connectionString =
    config.connectionString ?? process.env.DATABASE_URL ?? "postgres://noema:noema@localhost:5432/noema";
  const pool = new pg.Pool({ connectionString, max: config.max ?? 10 });
  const db = drizzle(pool);

  return {
    db,
    pool,
    close: () => pool.end(),
    ping: async () => {
      const { rows } = await pool.query<{ n: number }>("select 1 as n");
      return rows[0]?.n ?? 0;
    },
  };
}