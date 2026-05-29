import { Request, Response } from 'express';
export declare class EventController {
    createEvent(req: Request, res: Response): Promise<void>;
    getEvents(req: Request, res: Response): Promise<void>;
    getEventDetails(req: Request, res: Response): Promise<void>;
    updateEvent(req: Request, res: Response): Promise<void>;
    batchUpdateEvents(req: Request, res: Response): Promise<void>;
    deleteEvent(req: Request, res: Response): Promise<void>;
}
//# sourceMappingURL=event.controller.d.ts.map