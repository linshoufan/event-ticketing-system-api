"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.EventDB = void 0;
require("reflect-metadata");
const typeorm_1 = require("typeorm");
const event_model_1 = require("../model/event.model");
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config();
exports.EventDB = new typeorm_1.DataSource({
    type: "postgres",
    host: process.env.DB_HOST || "localhost",
    port: Number(process.env.DB_PORT) || 5432,
    username: process.env.DB_USER || "postgres",
    password: process.env.DB_PASSWORD || "",
    database: process.env.DB_NAME || "",
    synchronize: false, // 生產環境建議設為 false，改用 Migration
    logging: false,
    entities: [event_model_1.EventEntity],
    subscribers: [],
});
//# sourceMappingURL=database.js.map