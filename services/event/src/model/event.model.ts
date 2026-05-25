import { Entity, PrimaryColumn, Column, CreateDateColumn, UpdateDateColumn, Index } from "typeorm";
import { EventStatus, FAQ } from "../interface/event.interface";

@Entity("events")
export class EventEntity {
  @PrimaryColumn({ type: "varchar", length: 50, name: "event_id", nullable: false })
  eventId!: string;

  @Column({ type: "varchar", length: 255, nullable: false })
  name!: string;

  @Column({ type: "text", nullable: false })
  description!: string;

  @Column({ type: "varchar", length: 255, nullable: false })
  location!: string;

  @Index()
  @Column({ type: "varchar", length: 50, nullable: true })
  category!: string;

  @Column({ type: "boolean", default: false, name: "guest_allowed", nullable: false })
  guestAllowed!: boolean;

  @Column({ type: "integer", name: "ticket_limit", nullable: true })
  ticketLimit!: number | null;

  @Column({ type: "integer", name: "remaining_tickets", default: 0, nullable: false })
  remainingTickets!: number;

  @Column({ type: "timestamp with time zone", name: "cancellation_deadline", nullable: true })
  cancellationDeadline!: Date | null;

  @Column({ type: "decimal", precision: 9, scale: 6, nullable: true })
  latitude!: number;

  @Column({ type: "decimal", precision: 9, scale: 6, nullable: true })
  longitude!: number;

  @Column({ type: "decimal", precision: 9, scale: 6, nullable: true})
  checkinRadiusMeters!: number;

  @Column({ type: "timestamp with time zone", name: "event_start_time", nullable: false })
  eventStartTime!: Date;

  @Column({ type: "timestamp with time zone", name: "event_end_time", nullable: false })
  eventEndTime!: Date;

  @Column({ type: "timestamp with time zone", name: "registration_start", nullable: false })
  registrationStart!: Date;

  @Column({ type: "timestamp with time zone", name: "registration_end", nullable: false })
  registrationEnd!: Date;

  @Column({ type: "jsonb", default: [], nullable: true })
  faqs!: FAQ[];

  @Column({ type: "int", default: EventStatus.NOT_OPEN, nullable: false })
  status!: EventStatus;

  @Column({ type: "boolean", name: "is_draft", default: true, nullable: false })
  isDraft!: boolean;

  @CreateDateColumn({ type: "timestamp with time zone", name: "created_at", nullable: false })
  createdAt!: Date;

  @UpdateDateColumn({ type: "timestamp with time zone", name: "updated_at", nullable: true })
  updatedAt!: Date;
}
