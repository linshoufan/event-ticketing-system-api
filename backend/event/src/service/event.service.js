"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.EventService = void 0;
const database_1 = require("../core/database");
const event_model_1 = require("../model/event.model");
const event_interface_1 = require("../interface/event.interface");
const crypto_1 = require("crypto");
class EventService {
    eventRepository = database_1.EventDB.getRepository(event_model_1.EventEntity);
    // 新增活動
    async createEvent(data) {
        const eventId = `${(0, crypto_1.randomUUID)().replace(/-/g, "").substring(0, 10)}`;
        const newEvent = this.eventRepository.create({
            eventId,
            ...data
        });
        return await this.eventRepository.insert(newEvent);
    }
    // 取得單一活動詳情
    async getEventDetails(eventId) {
        return await this.eventRepository.findOne({ where: { eventId } });
    }
    // 條件查詢活動列表
    async getFilteredEvents(filters, page, limit) {
        const queryBuilder = this.eventRepository.createQueryBuilder("event");
        // 預設排除已結束的活動
        queryBuilder.where("event.status != :endedStatus", { endedStatus: event_interface_1.EventStatus.ENDED });
        if (filters.keyword) {
            queryBuilder.andWhere("(event.name ILIKE :keyword OR event.description ILIKE :keyword)", { keyword: `%${filters.keyword}%` } // ILIKE 為 PostgreSQL 的不區分大小寫模糊搜尋
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
    async updateEvent(eventId, updateData) {
        const event = await this.eventRepository.findOne({ where: { eventId } });
        if (!event)
            return null;
        return await this.eventRepository.update({ eventId }, updateData);
    }
    // 批量更新活動
    async processBatchUpdates(updates) {
        const result = { succeeded: [], failed: [], totalProcessed: updates.length };
        await database_1.EventDB.transaction(async (transactionalEntityManager) => {
            for (const update of updates) {
                try {
                    const { eventId, ...fieldsToUpdate } = update;
                    const event = await transactionalEntityManager.findOne(event_model_1.EventEntity, { where: { eventId } });
                    if (!event) {
                        result.failed.push({ eventId, error: "Event not found" });
                        continue;
                    }
                    transactionalEntityManager.merge(event_model_1.EventEntity, event, fieldsToUpdate);
                    await transactionalEntityManager.save(event_model_1.EventEntity, event);
                    result.succeeded.push(eventId);
                }
                catch (err) {
                    result.failed.push({ eventId: update.eventId, error: err.message || "UPDATE_FAILED" });
                }
            }
        });
        return result;
    }
    // 刪除活動
    async deleteEvent(eventId) {
        const event = await this.eventRepository.findOne({ where: { eventId } });
        if (!event)
            throw new Error("EVENT_NOT_FOUND");
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
exports.EventService = EventService;
//# sourceMappingURL=event.service.js.map