import { EventDB } from "../core/database";
import { EventEntity, EventIdPool } from "../model/event.model";
import { EventStatus } from "../interface/event.interface";
import { InsertResult, UpdateResult, DeleteResult, EntityManager } from "typeorm";

export class EventService {
  private eventRepository = EventDB.getRepository(EventEntity);

  // 新增活動
  public async createEvent(data: Partial<EventEntity>): Promise<InsertResult> {
    return await this.eventRepository.manager.transaction(async (entityManager) => {
      const record_num = await entityManager.count(EventIdPool);
      const nextAvailableId = await entityManager.findOne(EventIdPool, {
          where: { isOccupied: false },
          order: { id: 'ASC' },
          lock: { mode: 'pessimistic_write' } // Prevents race condition
        });

      let nextId = 1;
      if (!nextAvailableId) {
        if (record_num == 0) {
          await entityManager.save(EventIdPool, {id: nextId, isOccupied: true});
        } else if (record_num > 0 && record_num <= 10000) {
          const greatestUsedId = await entityManager.findOne(EventIdPool, {
            where: {},
            order: { id: 'DESC' },
            lock: { mode: 'pessimistic_write' }
          });
          if (greatestUsedId) {
            nextId = greatestUsedId.id + 1;
            await entityManager.insert(EventIdPool, { id: nextId, isOccupied: true });
          }
        }
        else throw new Error("EVENT_LIMIT_EXCEEDED");
      } else {
        await entityManager.update(EventIdPool, { id: nextAvailableId.id }, { isOccupied: true });
        nextId = nextAvailableId.id;
      }
      const newEventId = "event_" + String(nextId);
      const newEvent = entityManager.create(EventEntity, {
        eventId: newEventId,
        ...data
      });
      return await entityManager.insert(EventEntity, newEvent);
    })
  }

  // 取得單一活動詳情
  public async getEventInfo(eventId: string) {
    return await this.eventRepository.findOne({
      where: { eventId }
    });
  }

  // 查看活動列表
  public async getFilteredEvents(page: number, limit: number, filters: any) {
    const queryBuilder = this.eventRepository.createQueryBuilder("event");

    // 首先排除已結束活動
    queryBuilder.where("event.status != :endedStatus", { endedStatus: EventStatus.ENDED });

    // 關鍵字篩選
    if (filters.keyword) {
      queryBuilder.andWhere(
        "(event.name ILIKE :keyword OR event.description ILIKE :keyword)",
        { keyword: `%${filters.keyword}%` } // ILIKE 為 PostgreSQL 的不區分大小寫模糊搜尋
      );
    }
    if (filters.category) {
      queryBuilder.andWhere("event.category = :category", { category: filters.category });
    }
    if (filters.startDate && filters.endDate) {
      queryBuilder.andWhere("event.eventStartTime >= :startDate AND event.eventEndTime < :endDate", { startDate: filters.startDate, endDate: filters.endDate});
    }
    if (filters.status !== undefined) {
      queryBuilder.andWhere("event.status = :status", { status: filters.status });
    }

    // 跳至第 n 頁並顯示活動 (n = page)
    const skip = (page - 1) * limit;
    queryBuilder.orderBy("event.createdAt", "DESC").skip(skip).take(limit);

    const [events, total] = await queryBuilder.getManyAndCount();
    // 去蕪存菁
    const event_snapshots = events.map(({latitude, longitude, checkinRadiusMeters, faqs, isDraft, createdAt, ...returnFields}) => returnFields);
    return { event_snapshots, total };
  }

  // 更新活動資訊
  public async updateEvent(eventId: string, updateData: Partial<EventEntity>) {
    const event = await this.eventRepository.findOne({ where: { eventId } });
    if (!event) throw new Error("EVENT_NOT_FOUND");
    return await this.eventRepository.update({eventId}, updateData);
  }

  // 批量更新活動
  public async batchEventUpdate(updates: any[]) {
    const result = {
      data: {
        succeeded: [] as any[],
        failed: [] as any[]
      }
    };

    await EventDB.transaction(async (transactionEntityManager) => {
      for (const updateData of updates) {
        try {
          const { eventId, ...updateFields } = updateData;
          const eventToUpdate = await transactionEntityManager.findOne(EventEntity, { where: { eventId } });
          
          if (!eventToUpdate) {
            result.data.failed.push({ eventId: eventId, error: 'EVENT_NOT_FOUND' });
            continue;
          }

          const outcome = await transactionEntityManager.update(EventEntity, {eventId}, updateData);
          if (outcome.affected == 1) {
            result.data.succeeded.push(eventId);
          }
        } catch (error: any) {
          result.data.failed.push({ eventId: error.eventId, error: error.message });
        }
      }
    })

    return result;
  }

  // 刪除活動
  public async deleteEvent(eventId: string) {
    return await this.eventRepository.manager.transaction(async (EntityManager) => {
      const event = await EntityManager.findOne(EventEntity, { where: { eventId } });
      if (!event) throw new Error("EVENT_NOT_FOUND");

      // 可刪除條件：尚未開放或開始報名
      const now = new Date();
      const startTime = new Date(event.eventStartTime);
      if (event.status !== EventStatus.NOT_OPEN || now >= startTime) {
        throw new Error("EVENT_NOT_DELETABLE");
      }
      try {
        const availableId = Number(eventId.replace("event_", ""));
        await EntityManager.delete(EventEntity, {eventId});
        await EntityManager.update(EventIdPool, { id: availableId }, { isOccupied: false });
      } catch(error: any) {
        return error.message;
      }
    })
  }
}
