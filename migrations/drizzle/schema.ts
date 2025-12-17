import { pgTable, text, timestamp, integer, jsonb, uuid } from "drizzle-orm/pg-core";

export const orders = pgTable("orders", {
  id: uuid("id").primaryKey(),
  state: text("state").notNull().default("received"),
  addressJson: jsonb("address_json"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
});

export const payments = pgTable("payments", {
  paymentId: uuid("payment_id").primaryKey(),
  orderId: uuid("order_id").notNull().references(() => orders.id, { onDelete: "cascade" }),
  status: text("status").notNull().default("pending"),
  amount: integer("amount").notNull().default(0),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

export const events = pgTable("events", {
  id: uuid("id").primaryKey(),
  orderId: uuid("order_id").notNull().references(() => orders.id, { onDelete: "cascade" }),
  type: text("type").notNull(),
  payloadJson: jsonb("payload_json"),
  ts: timestamp("ts", { withTimezone: true }).defaultNow().notNull(),
});


