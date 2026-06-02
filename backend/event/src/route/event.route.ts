import { Router } from 'express';
import { EventController } from '../controller/event.controller';
import { createEventBody, updateEventBody, eventQueryBody, deleteEventBody } from '../schema/event.schema';
import { batchUpdateBody, batchQueryBody } from '../schema/event.schema';
import { validate } from '../middleware/schema.middleware';
import { requireAuth, requireRole, UserRole } from '../middleware/auth.middleware';

const router = Router();
const eventController = new EventController();
const AUTHORIZED_USERS = [UserRole.ADMIN, UserRole.WELFARE_MEMBER];
const ALL_USERS   = [UserRole.ADMIN, UserRole.WELFARE_MEMBER, UserRole.USER];

// 新增活動
router.post('/', requireAuth, requireRole(AUTHORIZED_USERS), validate(createEventBody), eventController.createEvent);

// 取得單一活動詳情
router.get('/:eventId', requireAuth, validate(eventQueryBody), eventController.getEventInfo);
// 查看活動列表
router.get('/', requireAuth, validate(batchQueryBody), eventController.getEventList);

// 更新活動資訊
router.patch('/:eventId', requireAuth, requireRole(AUTHORIZED_USERS), validate(updateEventBody), eventController.updateEvent);
// 批量更新活動
router.patch('/', requireAuth, requireRole(AUTHORIZED_USERS), validate(batchUpdateBody), eventController.batchUpdateEvents);

// 刪除活動
router.delete('/:eventId', requireAuth, requireRole(AUTHORIZED_USERS), validate(deleteEventBody), eventController.deleteEvent);

export default router;
