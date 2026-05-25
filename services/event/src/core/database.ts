import "reflect-metadata";
import { DataSource } from "typeorm";
import { EventEntity } from "../model/event.model";
import dotenv from "dotenv";
dotenv.config();

export const EventDB = new DataSource({
  type: "postgres",
  host: process.env.DB_HOST || "localhost",
  port: Number(process.env.DB_PORT) || 5432,
  username: process.env.DB_USER || "postgres",
  password: process.env.DB_PASSWORD || "",
  database: process.env.DB_NAME || "",
  synchronize: false, // 生產環境建議設為 false，改用 Migration
  logging: false,
  entities: [EventEntity],
  subscribers: [],
  migrations: [],
});
