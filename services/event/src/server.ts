import app from "./app";
import dotenv from "dotenv";
import { AppDataSource } from "./core/database";
import { initCronJobs } from "./core/event.cron";

dotenv.config();

const PORT = process.env.PORT || 3000;

const startServer = async () => {
  try {
    // 初始化 PostgreSQL 連線
    await AppDataSource.initialize();
    console.log("Database connected successfully via TypeORM.");

    // 初始化每日排程任務
    initCronJobs();

    app.listen(PORT, () => {
      console.log(`Event Service successfully runs on http://localhost:${PORT}/v1`);
    });
  } catch (error) {
    console.error("Failed to start server: ", error);
    process.exit(1);
  }
};

startServer();
