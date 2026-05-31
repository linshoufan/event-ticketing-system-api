"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.EventEntity = void 0;
const typeorm_1 = require("typeorm");
const event_interface_1 = require("../interface/event.interface");
let EventEntity = class EventEntity {
    eventId;
    name;
    description;
    location;
    category;
    guestAllowed;
    ticketLimit;
    remainingTickets;
    cancellationDeadline;
    latitude;
    longitude;
    checkinRadiusMeters;
    eventStartTime;
    eventEndTime;
    registrationStart;
    registrationEnd;
    faqs;
    status;
    isDraft;
    createdAt;
    updatedAt;
};
exports.EventEntity = EventEntity;
__decorate([
    (0, typeorm_1.PrimaryColumn)({ type: "varchar", length: 50, name: "event_id", nullable: false }),
    __metadata("design:type", String)
], EventEntity.prototype, "eventId", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "varchar", length: 255, nullable: false }),
    __metadata("design:type", String)
], EventEntity.prototype, "name", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "text", nullable: false }),
    __metadata("design:type", String)
], EventEntity.prototype, "description", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "varchar", length: 255, nullable: false }),
    __metadata("design:type", String)
], EventEntity.prototype, "location", void 0);
__decorate([
    (0, typeorm_1.Index)(),
    (0, typeorm_1.Column)({ type: "varchar", length: 50, nullable: true }),
    __metadata("design:type", String)
], EventEntity.prototype, "category", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "boolean", default: false, name: "guest_allowed", nullable: false }),
    __metadata("design:type", Boolean)
], EventEntity.prototype, "guestAllowed", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "integer", name: "ticket_limit", nullable: true }),
    __metadata("design:type", Object)
], EventEntity.prototype, "ticketLimit", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "integer", name: "remaining_tickets", default: 0, nullable: false }),
    __metadata("design:type", Number)
], EventEntity.prototype, "remainingTickets", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "timestamp with time zone", name: "cancellation_deadline", nullable: true }),
    __metadata("design:type", Object)
], EventEntity.prototype, "cancellationDeadline", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "decimal", precision: 9, scale: 6, nullable: true }),
    __metadata("design:type", Number)
], EventEntity.prototype, "latitude", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "decimal", precision: 9, scale: 6, nullable: true }),
    __metadata("design:type", Number)
], EventEntity.prototype, "longitude", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "decimal", precision: 9, scale: 6, nullable: true }),
    __metadata("design:type", Number)
], EventEntity.prototype, "checkinRadiusMeters", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "timestamp with time zone", name: "event_start_time", nullable: false }),
    __metadata("design:type", Date)
], EventEntity.prototype, "eventStartTime", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "timestamp with time zone", name: "event_end_time", nullable: false }),
    __metadata("design:type", Date)
], EventEntity.prototype, "eventEndTime", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "timestamp with time zone", name: "registration_start", nullable: false }),
    __metadata("design:type", Date)
], EventEntity.prototype, "registrationStart", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "timestamp with time zone", name: "registration_end", nullable: false }),
    __metadata("design:type", Date)
], EventEntity.prototype, "registrationEnd", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "jsonb", default: [], nullable: true }),
    __metadata("design:type", Array)
], EventEntity.prototype, "faqs", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "int", default: event_interface_1.EventStatus.NOT_OPEN, nullable: false }),
    __metadata("design:type", Number)
], EventEntity.prototype, "status", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: "boolean", name: "is_draft", default: true, nullable: false }),
    __metadata("design:type", Boolean)
], EventEntity.prototype, "isDraft", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)({ type: "timestamp with time zone", name: "created_at", nullable: false }),
    __metadata("design:type", Date)
], EventEntity.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.UpdateDateColumn)({ type: "timestamp with time zone", name: "updated_at", nullable: true }),
    __metadata("design:type", Date)
], EventEntity.prototype, "updatedAt", void 0);
exports.EventEntity = EventEntity = __decorate([
    (0, typeorm_1.Entity)("events")
], EventEntity);
//# sourceMappingURL=event.model.js.map