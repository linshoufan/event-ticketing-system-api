"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const event_controller_1 = require("../controller/event.controller");
const event_middleware_1 = require("../validate/event.middleware");
const event_schema_1 = require("../schema/event.schema");
// import { requireAuth, requireRole } from '../middlewares/auth.middleware'; // JWT 驗證中介軟體
const router = (0, express_1.Router)();
const eventController = new event_controller_1.EventController();
// 新增活動
router.post('/', (0, event_middleware_1.validate)(event_schema_1.createEventSchema), eventController.createEvent);
// 查詢活動列表
router.get('/', eventController.getEvents);
// 取得單一活動詳情
router.get('/:eventId', eventController.getEventDetails);
// 更新活動資訊
router.patch('/:eventId', (0, event_middleware_1.validate)(event_schema_1.updateEventSchema), eventController.updateEvent);
// 批量更新活動
router.patch('/', (0, event_middleware_1.validate)(event_schema_1.batchUpdateSchema), eventController.batchUpdateEvents);
// 刪除活動
router.delete('/:eventId', /* requireRole(['welfare_member']), */ eventController.deleteEvent);
exports.default = router;
//# sourceMappingURL=event.route.js.map