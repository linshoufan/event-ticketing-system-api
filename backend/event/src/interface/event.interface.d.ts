export declare enum EventStatus {
    NOT_OPEN = 0,
    REGISTERING = 1,
    WAITLIST = 2,
    CLOSED = 3,
    ENDED = 4
}
export interface FAQ {
    question: string;
    answer: string;
}
export interface Event {
    eventId: string;
    name: string;
    description: string;
    location: string;
    category: string;
    guestAllowed: boolean;
    ticketLimit: number | null;
    remainingTickets: number;
    cancellationDeadline: Date | null;
    latitude?: number;
    longitude?: number;
    checkinRadiusMeters?: number;
    eventStartTime: Date;
    eventEndTime: Date;
    registrationStart: Date;
    registrationEnd: Date;
    faqs?: FAQ[];
    status: EventStatus;
    isDraft: boolean;
    createdAt: Date;
    updatedAt: Date;
}
export interface BatchUpdateResult {
    succeeded: string[];
    failed: {
        eventId: string;
        error: string;
    }[];
    totalProcessed: number;
}
//# sourceMappingURL=event.interface.d.ts.map