import cron from "node-cron";
import { EventDB } from "../core/database";
import { EventEntity } from "../model/event.model";
import { EventStatus } from "../interface/event.interface";

export const initCronJobs = () => {
  // 每天凌晨 00:00 準時執行
  cron.schedule("0 0 * * *", async () => {
    console.log("[Cron] 開始執行每日 PostgreSQL 活動狀態更新...");
    const queryRunner = EventDB.createQueryRunner();
    await queryRunner.connect();
    await queryRunner.startTransaction();

    try {
      const now = new Date();

      // 報名未開放 -> 報名中 (當前時間大於等於報名開始時間，小於結束時間)
      await queryRunner.manager
        .createQueryBuilder()
        .update(EventEntity)
        .set({ status: EventStatus.REGISTERING })
        .where("status = :status AND registrationStart <= :now AND registrationEnd > :now", {
          status: EventStatus.NOT_OPEN,
          now,
        })
        .execute();

      // 報名中/候補 -> 報名截止 (當前時間大於等於報名結束時間)
      await queryRunner.manager
        .createQueryBuilder()
        .update(EventEntity)
        .set({ status: EventStatus.CLOSED })
        .where("status IN (:...statuses) AND registrationEnd <= :now", {
          statuses: [EventStatus.REGISTERING, EventStatus.WAITLIST],
          now,
        })
        .execute();

      // 任何非結束狀態 -> 活動結束 (當前時間大於等於活動結束時間)
      await queryRunner.manager
        .createQueryBuilder()
        .update(EventEntity)
        .set({ status: EventStatus.ENDED })
        .where("status != :endedStatus AND eventEndTime <= :now", {
          endedStatus: EventStatus.ENDED,
          now,
        })
        .execute();

      await queryRunner.commitTransaction();
      console.log("[Cron] PostgreSQL 活動狀態批次更新成功。");
    } catch (error) {
      await queryRunner.rollbackTransaction();
      console.error("[Cron] 活動狀態更新發生錯誤，已進行 Rollback:", error);
    } finally {
      await queryRunner.release();
    }
  });
};
