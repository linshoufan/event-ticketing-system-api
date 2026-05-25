import { z } from 'zod';

// FAQ驗證格式
const faqSchema = z.object({
  question: z.string().min(1, "問題不能為空"),
  answer: z.string().min(1, "答案不能為空"),
});

// Schema Template for EventBody
const eventBodySchema = z.object({
  name: z.string().min(1, "活動名稱為必填").max(255, "名稱過長"),
  description: z.string().min(1, "活動內容不能為空"),
  location: z.string(),
  category: z.string(),
  guestAllowed: z.boolean().default(false),
  ticketLimit: z.number().int().min(1).nullable().optional(),
  remainingTickets: z.number().min(1),
  cancellationDeadline: z.coerce.date().nullable().optional(),

  latitude: z.number().min(-90).max(90).optional(),
  longitude: z.number().min(-180).max(180).optional(),
  checkinRadiusMeters: z.number().optional(),

  eventStartTime: z.coerce.date({ message: "須為有效的 ISO 時間格式" }),
  eventEndTime: z.coerce.date({ message: "須為有效的 ISO 時間格式" }),
  registrationStart: z.coerce.date({ message: "須為有效的 ISO 時間格式" }),
  registrationEnd: z.coerce.date({ message: "須為有效的 ISO 時間格式" }),

  faqs: z.array(faqSchema).optional(),
  status: z.number().min(0).max(4),
  isDraft: z.boolean().default(true),
  createdAt: z.coerce.date({ message: "須為有效的 ISO 時間格式" }),
  updatedAt: z.coerce.date({ message: "須為有效的 ISO 時間格式" }).nullish()
});

// 創建活動
export const createEventSchema = z.object({
  body: eventBodySchema.refine(
    (data) => new Date(data.eventEndTime) > new Date(data.eventStartTime), {
      message: "活動結束時間必須晚於開始時間",
      path: ["eventEndTime"], 
    }).refine((data) => new Date(data.registrationEnd) > new Date(data.registrationStart), {
      message: "報名結束時間必須晚於報名開始時間",
      path: ["registrationEnd"],
    })
});

// 更新單一活動
export const updateEventSchema = z.object({
  body: eventBodySchema.partial(), // partial() 將所有欄位變成 Optional
});

// 批量更新
export const batchUpdateSchema = z.object({
  body: z.object({
    updates: z.array(
      z.object({
        eventId: z.string().min(1, "eventId 為必填"),
      }).and(updateEventSchema.shape.body) // 結合 eventId 與可選的更新欄位
    ).min(1, "至少需要一筆更新資料")
  })
});
