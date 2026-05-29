import { EventEntity } from "../model/event.model";
import { BatchUpdateResult } from "../interface/event.interface";
import { InsertResult } from "typeorm";
export declare class EventService {
    private eventRepository;
    createEvent(data: Partial<EventEntity>): Promise<InsertResult>;
    getEventDetails(eventId: string): Promise<EventEntity | null>;
    getFilteredEvents(filters: any, page: number, limit: number): Promise<{
        events: EventEntity[];
        total: number;
    }>;
    updateEvent(eventId: string, updateData: Partial<EventEntity>): Promise<import("typeorm").UpdateResult | null>;
    processBatchUpdates(updates: any[]): Promise<BatchUpdateResult>;
    deleteEvent(eventId: string): Promise<boolean>;
}
//# sourceMappingURL=event.service.d.ts.map