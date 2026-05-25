import { Request, Response } from 'express';
import { EventService } from '../service/event.service';
import { success } from 'zod';

const serviceHandler = new EventService();

export class EventController {

  public async createEvent(req: Request, res: Response): Promise<void> {
    try {
      const result = await serviceHandler.createEvent(req.body);
      const createdEventId = result.identifiers[0]?.eventId;
      res.status(201).json({
        data: {
          success: true,
          message: "成功創建活動",
          eventId: createdEventId
        }
      });
    } catch (error: any) {
      res.status(500).json({ success: false, error: { code: 'INTERNAL_SERVER_ERROR', message: error.message } });
    }
  }

  public async getEvents(req: Request, res: Response): Promise<void> {
    try {
      const page = Number(req.query.page) || 1;
      const limit = Number(req.query.limit) || 20;
      
      const { events, total } = await serviceHandler.getFilteredEvents(req.query, page, limit);

      res.status(200).json({
        data: events,
        pagination: { page, limit, total }
      });
    } catch (error) {
      res.status(500).json({ error: { code: 'INTERNAL_SERVER_ERROR', message: '內部系統錯誤' } });
    }
  }

  public async getEventDetails(req: Request, res: Response): Promise<void> {
    try {
      const eventId = req.params.eventId as string;
      if (!eventId) {
        res.status(400).json({ error: { code: 'EVENT_NOT_FOUND', message: '活動ID不能為NULL' } })
        return;
      }

      const event = await serviceHandler.getEventDetails(eventId);

      if (!event) {
        res.status(404).json({ error: { code: 'EVENT_NOT_FOUND', message: '活動不存在' } });
        return;
      }
      res.status(200).json({ data: event });
    } catch (error) {
      res.status(500).json({ error: { code: 'INTERNAL_SERVER_ERROR', message: '內部系統錯誤' } });
    }
  }

  public async updateEvent(req: Request, res: Response): Promise<void> {
    try {
      const eventId = req.params.eventId as string;
      if (!eventId) {
        res.status(400).json({ error: { code: 'EVENT_NOT_FOUND', message: '活動ID不能為NULL' } })
        return;
      }

      const result = await serviceHandler.updateEvent(eventId, req.body);

      if (result?.affected == 0) {
        res.status(404).json({ error: { code: 'EVENT_NOT_FOUND', message: '活動不存在' } });
        return;
      }

      if (result?.generatedMaps[0] && result.generatedMaps[0].updated_at) {
        res.status(200).json({
          data: { updated: true, updatedAt: result?.generatedMaps[0].updated_at }
        });
      } else {
        res.status(200).json({
          data: { updated: true, updatedAt: new Date() }
        });
      }
    } catch (error) {
      res.status(400).json({ error: { code: 'BAD_REQUEST', message: '資料格式或參數不合法' } });
    }
  }

  public async batchUpdateEvents(req: Request, res: Response): Promise<void> {
    try {
      const updates = req.body.updates;
      const result = await serviceHandler.processBatchUpdates(updates);
      res.status(207).json({ data: result });
    } catch (error) {
      res.status(500).json({ error: { code: 'INTERNAL_SERVER_ERROR', message: '內部系統錯誤' } });
    }
  }

  public async deleteEvent(req: Request, res: Response): Promise<void> {
    try {
      const eventId = req.params.eventId as string;
      if (!eventId) {
        res.status(400).json({ error: { code: 'EVENT_NOT_FOUND', message: '活動ID不能為NULL' } })
        return;
      }

      await serviceHandler.deleteEvent(eventId);
      res.status(200).json({ data: { deleted: true } });
    } catch (error: any) {
      if (error.message === 'EVENT_NOT_DELETABLE') {
        res.status(409).json({ error: { code: 'EVENT_NOT_DELETABLE', message: '活動不符合刪除條件' } });
      } else if (error.message === 'EVENT_NOT_FOUND') {
        res.status(404).json({ error: { code: 'EVENT_NOT_FOUND', message: '活動不存在' } });
      } else {
        res.status(500).json({ error: { code: 'INTERNAL_SERVER_ERROR', message: '內部系統錯誤' } });
      }
    }
  }
}
