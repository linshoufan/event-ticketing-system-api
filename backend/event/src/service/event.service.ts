import { EventDB } from "../core/database";
import { EventEntity } from "../model/event.model";
import { EventStatus, BatchUpdateResult } from "../interface/event.interface";
import { InsertResult } from "typeorm";
import { randomUUID } from "crypto";

export class EventService {
  private eventRepository = EventDB.getRepository(EventEntity);

  // 新增活動
  public async createEvent(data: Partial<EventEntity>): Promise<InsertResult> {
    const eventId = `${randomUUID().replace(/-/g, "").substring(0,10)}`;
    const newEvent = this.eventRepository.create({
      eventId,
      ...data
    });
    return await this.eventRepository.insert(newEvent);
  }

  // 取得單一活動詳情
  public async getEventDetails(eventId: string) {
    return await this.eventRepository.findOne({ where: { eventId } });
  }

  // 條件查詢活動列表
  public async getFilteredEvents(filters: any, page: number, limit: number) {
    const queryBuilder = this.eventRepository.createQueryBuilder("event");

    // 預設排除已結束的活動
    queryBuilder.where("event.status != :endedStatus", { endedStatus: EventStatus.ENDED });

    if (filters.keyword) {
      queryBuilder.andWhere(
        "(event.name ILIKE :keyword OR event.description ILIKE :keyword)",
        { keyword: `%${filters.keyword}%` } // ILIKE 為 PostgreSQL 的不區分大小寫模糊搜尋
      );
    }
    if (filters.category) {
      queryBuilder.andWhere("event.category = :category", { category: filters.category });
    }
    if (filters.status !== undefined) {
      queryBuilder.andWhere("event.status = :status", { status: Number(filters.status) });
    }

    const skip = (page - 1) * limit;
    queryBuilder.orderBy("event.createdAt", "DESC").skip(skip).take(limit);

    const [events, total] = await queryBuilder.getManyAndCount();
    return { events, total };
  }

  // 更新活動資訊
  public async updateEvent(eventId: string, updateData: Partial<EventEntity>) {
    const event = await this.eventRepository.findOne({ where: { eventId } });
    if (!event) return null;
    return await this.eventRepository.update({eventId}, updateData);
  }

  // 批量更新活動
  public async processBatchUpdates(updates: any[]): Promise<BatchUpdateResult> {
    const result: BatchUpdateResult = { succeeded: [], failed: [], totalProcessed: updates.length };

    await EventDB.transaction(async (transactionalEntityManager) => {
      for (const update of updates) {
        try {
          const { eventId, ...fieldsToUpdate } = update;
          const event = await transactionalEntityManager.findOne(EventEntity, { where: { eventId } });
          
          if (!event) {
            result.failed.push({ eventId, error: "Event not found" });
            continue;
          }

          transactionalEntityManager.merge(EventEntity, event, fieldsToUpdate);
          await transactionalEntityManager.save(EventEntity, event);
          result.succeeded.push(eventId);
        } catch (err: any) {
          result.failed.push({ eventId: update.eventId, error: err.message || "UPDATE_FAILED" });
        }
      }
    });

    return result;
  }

  // 刪除活動
  public async deleteEvent(eventId: string): Promise<boolean> {
    const event = await this.eventRepository.findOne({ where: { eventId } });
    if (!event) throw new Error("EVENT_NOT_FOUND");

    // 設置刪除條件： 1. 草稿 || 2. 尚未開放報名)
    // const now = new Date();
    // const isNotStarted = event.status === EventStatus.NOT_OPEN && new Date(event.registrationStart) > now;
    // if (!event.isDraft && !isNotStarted) {
    //   throw new Error("EVENT_NOT_DELETABLE");
    // }

    await this.eventRepository.delete({ eventId });
    return true;
  }
}
