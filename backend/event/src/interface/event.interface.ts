// All event status
export enum EventStatus {
  NOT_OPEN = 'not_open',
  REGISTERING = 'registering',
  WAITLIST = 'waitlist',
  CLOSED = 'closed',
  ENDED = 'ended'
}

export interface FAQ {
  question: string;
  answer: string;
}

// Event attribute field
// null = no limit
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
