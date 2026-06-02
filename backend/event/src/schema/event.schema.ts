import { z } from 'zod';

// FAQ驗證格式
const faqBody = z.object({
  question: z.string().min(1, "問題不能為空").max(100, '超過問題字數上限'),
  answer: z.string().min(1, "答案不能為空").max(250, '超過答案字數上限')
});

// Schema Template for EventBody
const eventBody = z.object({
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

  faqs: z.array(faqBody).optional(),
  status: z.string(),
  isDraft: z.boolean().default(true),
});


// Schema: create event (Single)
export const createEventBody = z.object({
  body: eventBody.refine(
    (data) => new Date(data.eventEndTime) > new Date(data.eventStartTime), {
      message: "活動結束時間必須晚於開始時間",
      path: ["eventEndTime"], 
    }).refine((data) => new Date(data.registrationEnd) > new Date(data.registrationStart), {
      message: "報名結束時間必須晚於報名開始時間",
      path: ["registrationEnd"],
    })
});


// Schema: get event info (Single)
export const eventQueryBody = z.object({
  params: z.object({
    eventId: z.string().min(1, '查詢活動ID不能為空')
  })
});

// Get event info (Batch)
export const batchQueryBody = z.object({
  body: z.object({
    page: z.number().min(1, '頁數不可為0'),
    limit: z.number().min(1, '搜尋數量不可為0'),
    filters: z.object({
      keyword: z.string().optional(),
      category: z.string().optional(),
      startDate: z.coerce.date().optional(),
      endDate: z.coerce.date().optional(),
      status: z.string().optional()
    }).default({})
  })
});


// Schema: update event (Single)
export const updateEventBody = z.object({
  body: eventBody.partial() // partial() 將所有欄位變成 Optional
});

// Update event (Batch)
export const batchUpdateBody = z.object({
  body: z.object({
    updates: z.array(
      z.object({
        eventId: z.string().min(1, '活動ID不能為空')
      }).and(eventBody.partial())
    ).min(1, '需輸入至少一筆更新資料')
  })
});


// Schema: delete event (Single)
export const deleteEventBody = z.object({
  params: z.object({
    eventId: z.string().min(1, '活動ID不能為空')
  })
});
