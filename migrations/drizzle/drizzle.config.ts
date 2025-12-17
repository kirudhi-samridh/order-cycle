import type { Config } from "drizzle-kit";

export default {
  schema: "./schema.ts",
  out: "./migrations",
  dialect: "postgresql",
  dbCredentials: {
    url: process.env.DATABASE_URL || "postgresql://temporal:temporal@172.31.11.185:5434/temporal",
  },
} satisfies Config;


