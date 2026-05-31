import { EventStatus, FAQ } from "../interface/event.interface";
export declare class EventEntity {
    eventId: string;
    name: string;
    description: string;
    location: string;
    category: string;
    guestAllowed: boolean;
    ticketLimit: number | null;
    remainingTickets: number;
    cancellationDeadline: Date | null;
    latitude: number;
    longitude: number;
    checkinRadiusMeters: number;
    eventStartTime: Date;
    eventEndTime: Date;
    registrationStart: Date;
    registrationEnd: Date;
    faqs: FAQ[];
    status: EventStatus;
    isDraft: boolean;
    createdAt: Date;
    updatedAt: Date;
}
//# sourceMappingURL=event.model.d.ts.map