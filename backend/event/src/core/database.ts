import 'reflect-metadata';
import { DataSource } from 'typeorm';
import { EventEntity, EventIdPool } from '../model/event.model';
import dotenv from 'dotenv';
dotenv.config();

// docker run --name event-test -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgrestest -e POSTGRES_DB=event_db_test -p 5433:5432 -d postgres:15-alpine
// docker ps

export const EventDB = new DataSource({
  type: 'postgres',
  host: process.env.DB_HOST || 'localhost',
  port: Number(process.env.DB_PORT) || 5432,
  username: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || '',
  database: process.env.NODE_ENV === 'test'
  ? process.env.DB_TEST_NAME || 'event_db_test'
  : process.env.DB_NAME || 'event_db',
  synchronize: process.env.NODE_ENV === 'test', // 生產環境建議設為 false，改用 Migration
  logging: false,
  entities: [EventEntity, EventIdPool],
  subscribers: [],
  migrations: []
});
