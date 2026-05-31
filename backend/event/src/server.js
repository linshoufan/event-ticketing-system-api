"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const app_1 = __importDefault(require("./app"));
const dotenv_1 = __importDefault(require("dotenv"));
const database_1 = require("./core/database");
const event_cron_1 = require("./core/event.cron");
dotenv_1.default.config();
const PORT = process.env.PORT || 3000;
const startServer = async () => {
    try {
        // 初始化 PostgreSQL 連線
        await database_1.EventDB.initialize();
        console.log("Database connected successfully via TypeORM.");
        // 初始化每日排程任務
        (0, event_cron_1.initCronJobs)();
        app_1.default.listen(PORT, () => {
            console.log(`Event Service successfully runs on http://localhost:${PORT}/v1`);
        });
    }
    catch (error) {
        console.error("Failed to start server: ", error);
        process.exit(1);
    }
};
startServer();
//# sourceMappingURL=server.js.map