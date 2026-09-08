import { describe, expect, it } from "vitest";
import { createDb } from "./db.js";

const testUrl = process.env.TEST_DATABASE_URL;

describe("db harness (seam: packages/core)", () => {
  it.skipIf(!testUrl)(
    "opens a PostgreSQL connection and round-trips a query",
    async () => {
      const { ping, close } = createDb({ connectionString: testUrl });
      try {
        expect(await ping()).toBe(1);
      } finally {
        await close();
      }
    },
  );

  it.skipIf(!testUrl)(
    "wires the drizzle client to the same pool",
    async () => {
      const { db, close } = createDb({ connectionString: testUrl });
      try {
        const result = await db.execute("select 1 as n");
        expect(result.rows[0]?.n).toBe(1);
      } finally {
        await close();
      }
    },
  );

  it("documents how to run the PG-backed seam test", () => {
    const how = testUrl
      ? "TEST_DATABASE_URL set — PG-backed cases run."
      : "TEST_DATABASE_URL not set — PG-backed cases skipped. Run: TEST_DATABASE_URL=postgres://noema:noema@localhost:5432/noema pnpm --filter @noema/core test";
    expect(how).toContain("TEST_DATABASE_URL");
  });
});