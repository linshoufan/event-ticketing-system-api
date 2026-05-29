"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.batchUpdateSchema = exports.updateEventSchema = exports.createEventSchema = void 0;
const zod_1 = require("zod");
// FAQ驗證格式
const faqSchema = zod_1.z.object({
    question: zod_1.z.string().min(1, "問題不能為空"),
    answer: zod_1.z.string().min(1, "答案不能為空"),
});
// Schema Template for EventBody
const eventBodySchema = zod_1.z.object({
    name: zod_1.z.string().min(1, "活動名稱為必填").max(255, "名稱過長"),
    description: zod_1.z.string().min(1, "活動內容不能為空"),
    location: zod_1.z.string(),
    category: zod_1.z.string(),
    guestAllowed: zod_1.z.boolean().default(false),
    ticketLimit: zod_1.z.number().int().min(1).nullable().optional(),
    remainingTickets: zod_1.z.number().min(1),
    cancellationDeadline: zod_1.z.coerce.date().nullable().optional(),
    latitude: zod_1.z.number().min(-90).max(90).optional(),
    longitude: zod_1.z.number().min(-180).max(180).optional(),
    checkinRadiusMeters: zod_1.z.number().optional(),
    eventStartTime: zod_1.z.coerce.date({ message: "須為有效的 ISO 時間格式" }),
    eventEndTime: zod_1.z.coerce.date({ message: "須為有效的 ISO 時間格式" }),
    registrationStart: zod_1.z.coerce.date({ message: "須為有效的 ISO 時間格式" }),
    registrationEnd: zod_1.z.coerce.date({ message: "須為有效的 ISO 時間格式" }),
    faqs: zod_1.z.array(faqSchema).optional(),
    status: zod_1.z.number().min(0).max(4),
    isDraft: zod_1.z.boolean().default(true),
    createdAt: zod_1.z.coerce.date({ message: "須為有效的 ISO 時間格式" }),
    updatedAt: zod_1.z.coerce.date({ message: "須為有效的 ISO 時間格式" }).nullish()
});
// 創建活動
exports.createEventSchema = zod_1.z.object({
    body: eventBodySchema.refine((data) => new Date(data.eventEndTime) > new Date(data.eventStartTime), {
        message: "活動結束時間必須晚於開始時間",
        path: ["eventEndTime"],
    }).refine((data) => new Date(data.registrationEnd) > new Date(data.registrationStart), {
        message: "報名結束時間必須晚於報名開始時間",
        path: ["registrationEnd"],
    })
});
// 更新單一活動
exports.updateEventSchema = zod_1.z.object({
    body: eventBodySchema.partial(), // partial() 將所有欄位變成 Optional
});
// 批量更新
exports.batchUpdateSchema = zod_1.z.object({
    body: zod_1.z.object({
        updates: zod_1.z.array(zod_1.z.object({
            eventId: zod_1.z.string().min(1, "eventId 為必填"),
        }).and(exports.updateEventSchema.shape.body) // 結合 eventId 與可選的更新欄位
        ).min(1, "至少需要一筆更新資料")
    })
});
//# sourceMappingURL=event.schema.js.map