"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const supertest_1 = __importDefault(require("supertest"));
const app_1 = __importDefault(require("../app"));
const database_1 = require("../core/database");
const event_model_1 = require("../model/event.model");
// Dummy data for test
const validEventPayload = {
    name: "2026跨年喝酒BBQ同樂會",
    description: "如題",
    location: "公司頂樓",
    category: "娛樂",
    guestAllowed: true,
    remainingTickets: 200,
    eventStartTime: "2026-12-31T17:00:00Z",
    eventEndTime: "2026-12-31T21:00:00Z",
    registrationStart: "2026-10-05T00:00:00Z",
    registrationEnd: "2026-11-05T23:59:59Z",
    status: 1,
    isDraft: false,
    createdAt: "2026-10-01T12:00:00Z"
};
describe('Event API Integration Tests', () => {
    const eventRepo = database_1.EventDB.getRepository(event_model_1.EventEntity);
    // 開始前先連線並同步資料庫
    beforeAll(async () => {
        if (!database_1.EventDB.isInitialized) {
            await database_1.EventDB.initialize();
        }
        await database_1.EventDB.synchronize(true); // true會清空整個資料庫，僅限測試使用！
    });
    // 結束後關閉資料庫連線
    afterAll(async () => {
        if (database_1.EventDB.isInitialized) {
            await database_1.EventDB.destroy();
        }
    });
    // 每個測試案例結束後，清空 events 資料表，確保測試互相獨立
    afterEach(async () => {
        await eventRepo.clear();
    });
    // CREATE 測試
    // ==========================================
    describe('POST /v1/events', () => {
        it('成功建立活動後，資料庫產生正確紀錄', async () => {
            const response = await (0, supertest_1.default)(app_1.default)
                .post('/v1/events')
                .send(validEventPayload);
            // console.log(response.text)
            expect(response.status).toBe(201);
            expect(response.body.data).toHaveProperty('eventId');
            const eventInDb = await eventRepo.findOne({ where: { eventId: response.body.data.eventId } });
            expect(eventInDb).not.toBeNull();
            expect(eventInDb?.name).toStrictEqual(validEventPayload.name);
            expect(eventInDb?.location).toStrictEqual(validEventPayload.location);
            expect(eventInDb?.remainingTickets).toBe(200);
        });
        it('Schema 驗證：開始時間 < 結束時間', async () => {
            const invalidPayload = {
                ...validEventPayload,
                eventStartTime: "2026-06-02T09:00:00Z",
                eventEndTime: "2026-06-01T18:00:00Z",
            };
            const response = await (0, supertest_1.default)(app_1.default)
                .post('/v1/events')
                .send(invalidPayload);
            expect(response.status).toBe(400);
            expect(response.body.error.code).toBe('BAD_REQUEST');
            expect(response.body.error.details[0].path).toBe('body.eventEndTime');
            const count = await eventRepo.count();
            expect(count).toBe(0);
        });
    });
    // READ 測試
    // ==========================================
    describe('GET /v1/events/:eventId', () => {
        it('成功取得指定活動詳情', async () => {
            const newEvent = eventRepo.create({ ...validEventPayload, eventId: 'test_read_001' });
            await eventRepo.save(newEvent);
            const response = await (0, supertest_1.default)(app_1.default).get('/v1/events/test_read_001');
            // console.log(response.text)
            expect(response.status).toBe(200);
            expect(response.body.data.eventId).toBe('test_read_001');
            expect(response.body.data.name).toBe(validEventPayload.name);
        });
        it('查詢不存在的活動回傳錯誤碼', async () => {
            const response = await (0, supertest_1.default)(app_1.default).get('/v1/events/test_read_002');
            expect(response.status).toBe(404);
        });
    });
    // UPDATE 測試
    // ==========================================
    describe('PATCH /v1/events/:eventId', () => {
        it('成功更新活動欄位後，資料庫正確反映', async () => {
            const newEvent = eventRepo.create({ ...validEventPayload, eventId: 'test_update_001' });
            await eventRepo.insert(newEvent);
            const response = await (0, supertest_1.default)(app_1.default)
                .patch('/v1/events/test_update_001')
                .send({ ticketLimit: 500, guestAllowed: false });
            // console.log(response.text)
            expect(response.status).toBe(200);
            const updatedEvent = await eventRepo.findOne({ where: { eventId: 'test_update_001' } });
            expect(updatedEvent?.ticketLimit).toBe(500);
            expect(updatedEvent?.guestAllowed).toBe(false);
            expect(updatedEvent?.name).toBe(validEventPayload.name);
        });
        it('Schema 驗證：傳入型別錯誤的更新資料', async () => {
            const response = await (0, supertest_1.default)(app_1.default)
                .patch('/v1/events/test_update_001')
                .send({ ticketLimit: "五百" });
            expect(response.status).toBe(400);
            expect(response.body.error.details[0].path).toBe('body.ticketLimit');
        });
    });
    // DELETE 測試
    // ==========================================
    describe('DELETE /v1/events/:eventId', () => {
        it('成功刪除活動後，資料從資料庫抹除', async () => {
            const newEvent = eventRepo.create({ ...validEventPayload, eventId: 'test_delete_001' });
            await eventRepo.save(newEvent);
            const response = await (0, supertest_1.default)(app_1.default).delete('/v1/events/test_delete_001');
            console.log(response.text);
            expect(response.status).toBe(200);
            const deletedEvent = await eventRepo.findOne({ where: { eventId: 'test_delete_001' } });
            expect(deletedEvent).toBeNull();
        });
    });
});
//# sourceMappingURL=api.test.js.map