import { Router } from 'express';
import { EventController } from '../controller/event.controller';
import { validate } from '../validate/event.middleware';
import { createEventSchema, updateEventSchema, batchUpdateSchema } from '../schema/event.schema';
// import { requireAuth, requireRole } from '../middlewares/auth.middleware'; // JWT 驗證中介軟體

const router = Router();
const eventController = new EventController();

// 新增活動
router.post('/', validate(createEventSchema), eventController.createEvent);

// 查詢活動列表
router.get('/', eventController.getEvents);

// 取得單一活動詳情
router.get('/:eventId', eventController.getEventDetails);

// 更新活動資訊
router.patch('/:eventId', validate(updateEventSchema), eventController.updateEvent);

// 批量更新活動
router.patch('/', validate(batchUpdateSchema), eventController.batchUpdateEvents);

// 刪除活動
router.delete('/:eventId', /* requireRole(['welfare_member']), */ eventController.deleteEvent);

export default router;
