import { Request, Response } from 'express';
import { EventService } from '../service/event.service';
import { batchQueryBody } from '../schema/event.schema';

const serviceHandler = new EventService();

export class EventController {

  public async createEvent(req: Request, res: Response): Promise<void> {
    try {
      const result = await serviceHandler.createEvent(req.body);
      const now_time = new Date();

      const createdEventId = result.identifiers[0]?.eventId;
      const draft = result.generatedMaps[0]?.isDraft;
      const create_time = result.generatedMaps[0]?.createdAt;

      if (create_time) {
        res.status(201).json({
          data: {
            eventId: createdEventId,
            isDraft: draft,
            createdAt: create_time
          }
        });
      } else {
        res.status(201).json({
          data: {
            eventId: createdEventId,
            isDraft: draft,
            createdAt: now_time
          }
        });
      }
    } catch (error: any) {
      res.status(500).json({ success: false, error: { code: 'INTERNAL_SERVER_ERROR', message: error.message } });
    }
  }

  public async getEventInfo(req: Request, res: Response): Promise<void> {
    try {
      const eventId = req.params.eventId as string;
      if (!eventId) {
        res.status(400).json({ error: { code: 'EVENT_ID_IS_NULL', message: '活動ID不能為NULL' } })
        return;
      }

      const event = await serviceHandler.getEventInfo(eventId);
      if (!event) {
        res.status(404).json({ error: { code: 'EVENT_NOT_FOUND', message: '活動不存在' } });
        return;
      }
      res.status(200).json({ data: event });
    } catch (error) {
      res.status(500).json({ error: { code: 'INTERNAL_SERVER_ERROR', message: '內部系統錯誤' } });
    }
  }

  public async getEventList(req: Request, res: Response): Promise<void> {
    try {
      const requestBody = batchQueryBody.parse(req);
      const { page, limit, filters } = requestBody.body;

      const {event_snapshots, total} = await serviceHandler.getFilteredEvents(page, limit, filters);

      res.status(200).json({
        data: event_snapshots,
        pagination: { page, limit, total }
      });
    } catch (error) {
      res.status(500).json({ error: { code: 'INTERNAL_SERVER_ERROR', message: '內部系統錯誤' } });
    }
  }

  public async updateEvent(req: Request, res: Response): Promise<void> {
    try {
      const eventId = req.params.eventId as string;
      if (!eventId) {
        res.status(400).json({ error: { code: 'EVENT_ID_IS_NULL', message: '活動ID不能為NULL' } })
        return;
      }

      const result = await serviceHandler.updateEvent(eventId, req.body);
      const now_time = new Date();
      if (result?.affected == 0) {
        res.status(404).json({ error: { code: 'EVENT_NOT_FOUND', message: '活動不存在' } });
        return;
      }

      const update_time = result?.generatedMaps[0]?.updatedAt;
      if (update_time) {
        res.status(200).json({
          data: { updated: true, updatedAt: update_time }
        });
      } else {
        // If the Database does not return time info, return the time of receiving the result from it
        res.status(200).json({
          data: { updated: true, updatedAt: now_time }
        });
      }
    } catch (error) {
      res.status(400).json({ error: { code: 'BAD_REQUEST', message: '資料格式或參數不合法' } });
    }
  }

  public async batchUpdateEvents(req: Request, res: Response): Promise<void> {
    try {
      const updates = req.body.updates;
      const result = await serviceHandler.batchEventUpdate(updates);
      res.status(207).json({data: result.data});
    } catch (error) {
      res.status(500).json({ error: { code: 'INTERNAL_SERVER_ERROR', message: '內部系統錯誤' } });
    }
  }

  public async deleteEvent(req: Request, res: Response): Promise<void> {
    try {
      const eventId = req.params.eventId as string;
      if (!eventId) {
        res.status(400).json({ error: { code: 'EVENT_ID_IS_NULL', message: '活動ID不能為NULL' } });
        return;
      }

      await serviceHandler.deleteEvent(eventId);
      res.status(200).json({ data: { deleted: true } });

    } catch (error: any) {
      if (error.message === 'EVENT_NOT_DELETABLE') {
        res.status(409).json({ error: { code: 'EVENT_NOT_DELETABLE', message: 'Event is already published or registration started.' } });
      } else if (error.message === 'EVENT_NOT_FOUND') {
        res.status(404).json({ error: { code: 'EVENT_NOT_FOUND', message: '活動不存在' } });
      } else {
        res.status(500).json({ error: { code: 'INTERNAL_SERVER_ERROR', message: '內部系統錯誤' } });
      }
    }
  }
}
