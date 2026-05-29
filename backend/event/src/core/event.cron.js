"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.initCronJobs = void 0;
const node_cron_1 = __importDefault(require("node-cron"));
const database_1 = require("../core/database");
const event_model_1 = require("../model/event.model");
const event_interface_1 = require("../interface/event.interface");
const initCronJobs = () => {
    // 每天凌晨 00:00 準時執行
    node_cron_1.default.schedule("0 0 * * *", async () => {
        console.log("[Cron] 開始執行每日 PostgreSQL 活動狀態更新...");
        const queryRunner = database_1.EventDB.createQueryRunner();
        await queryRunner.connect();
        await queryRunner.startTransaction();
        try {
            const now = new Date();
            // 報名未開放 -> 報名中 (當前時間大於等於報名開始時間，小於結束時間)
            await queryRunner.manager
                .createQueryBuilder()
                .update(event_model_1.EventEntity)
                .set({ status: event_interface_1.EventStatus.REGISTERING })
                .where("status = :status AND registrationStart <= :now AND registrationEnd > :now", {
                status: event_interface_1.EventStatus.NOT_OPEN,
                now,
            })
                .execute();
            // 報名中/候補 -> 報名截止 (當前時間大於等於報名結束時間)
            await queryRunner.manager
                .createQueryBuilder()
                .update(event_model_1.EventEntity)
                .set({ status: event_interface_1.EventStatus.CLOSED })
                .where("status IN (:...statuses) AND registrationEnd <= :now", {
                statuses: [event_interface_1.EventStatus.REGISTERING, event_interface_1.EventStatus.WAITLIST],
                now,
            })
                .execute();
            // 任何非結束狀態 -> 活動結束 (當前時間大於等於活動結束時間)
            await queryRunner.manager
                .createQueryBuilder()
                .update(event_model_1.EventEntity)
                .set({ status: event_interface_1.EventStatus.ENDED })
                .where("status != :endedStatus AND eventEndTime <= :now", {
                endedStatus: event_interface_1.EventStatus.ENDED,
                now,
            })
                .execute();
            await queryRunner.commitTransaction();
            console.log("[Cron] PostgreSQL 活動狀態批次更新成功。");
        }
        catch (error) {
            await queryRunner.rollbackTransaction();
            console.error("[Cron] 活動狀態更新發生錯誤，已進行 Rollback:", error);
        }
        finally {
            await queryRunner.release();
        }
    });
};
exports.initCronJobs = initCronJobs;
//# sourceMappingURL=event.cron.js.map