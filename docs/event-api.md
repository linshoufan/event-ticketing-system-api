# Event Management API

> 最後更新：2026-06-03

---

## 目錄

1. [專案結構](#1-專案結構)
2. [技術棧](#2-技術棧)
3. [快速啟動](#3-快速啟動)
4. [身分驗證與權限](#4-身分驗證與權限)
5. [API SPEC — 現有功能](#5-api-spec--現有功能)
6. [資料模型](#6-資料模型)
7. [錯誤碼一覽](#7-錯誤碼一覽)
8. [測試案例](#8-測試案例)

---

## 1. 專案結構

```
src/
├── app                           # Express App
├── server                        # 啟動入口
├── controller/
│   └── event.controller          # CRUD 邏輯 / API 與資料庫溝通橋樑
│
├── service/
│   └── event.service             # 下層資料庫讀寫溝通邏輯
│
├── route/
│   └── event.route               # 負責導流不同 API Call
│
├── schema/
│   └── event.schema              # 定義 Event Schema
│
├── middlewares/
│   ├── auth.middleware           # JWT 驗證 + User 角色檢查
│   └── schema.middleware         # 檢查傳輸資料 (格式、類別) 是否合乎 Schema
│
├── model/event.model
├── interface/event.interface     # 定義 Event Class
└── core/
    ├── database                  # Database 設定
    └── event.cron                # 自動排程 / 更新
```

---

## 2. 技術棧

| 項目 | 套件 |
|------|------|
| Web Framework | Express 5 |
| ORM | TypeORM 1.x + PostgreSQL |
| 驗證 Schema | Zod 4 |
| 身分驗證 | jsonwebtoken（新增相依） |
| 測試 | Jest + Supertest + SQLite3 |
| 排程 | node-cron |

### 新增相依套件

```bash
npm install jsonwebtoken
npm install -D @types/jsonwebtoken
```

---

## 3. 快速啟動

```bash
# 安裝相依
npm install

# 設定環境變數（複製後填入）
cp .env.example .env

# 開發模式
npm run dev

# 執行測試
npm test
```

---

## 4. 身分驗證與權限

### 角色清單

| 角色 | 值 | 說明 |
|------|----|------|
| `welfare_member` | `welfare_member` | 福委成員，可建立／更新／刪除活動 |
| `user` | `user` | 一般員工和HR，唯讀活動資料 |

### 各端點權限一覽

| 端點 | welfare_member | user |
|------|:--------------:|:----:|
| GET /v1/events | ✅ | ✅ |
| GET /v1/events/:id | ✅ | ✅ |
| POST /v1/events | ✅ | ❌ |
| PATCH /v1/events/:id | ✅ | ❌ |
| PATCH /v1/events (batch update) | ✅ | ❌ |
| DELETE /v1/events/:id | ✅ | ❌ |
| POST /v1/events/batch | ✅ | ❌ |
| POST /v1/events/batch/query | ✅ | ✅ |
| DELETE /v1/events/batch | ✅ | ❌ |

### JWT 格式

**Request Header**
```
Authorization: Bearer <token>
```

**Token Payload**
```json
{
  "userId": "u_001",
  "email": "user@example.com",
  "role": "welfare_member"
}
```

**產生測試 Token（開發/測試用）**
```ts
import { generateToken, UserRole } from './src/middlewares/auth.middleware';

const token = generateToken({
  userId: 'u_test',
  email:  'test@example.com',
  role:   UserRole.WELFARE_MEMBER,
});
```

---

## 5. API SPEC — 現有功能

Base URL: `http://localhost:3000/v1`

---

### POST /v1/events
建立單筆活動

**Request Body**
```json
{
  "name": "2026 年末聚餐",
  "description": "全員參與",
  "location": "公司頂樓",
  "category": "娛樂",
  "guestAllowed": false,
  "remainingTickets": 100,
  "eventStartTime": "2026-12-25T18:00:00Z",
  "eventEndTime":   "2026-12-25T22:00:00Z",
  "registrationStart": "2026-11-01T00:00:00Z",
  "registrationEnd":   "2026-12-01T23:59:59Z",
  "status": "not_open",
  "isDraft": false
}
```

**Response**
```json
{
  "data": {
    "eventId": "a3f9b2c1d0",
    "isDraft": false,
    "createdAt": "2026-10-01T00:00:00Z"
  }
}
```

---

### GET /v1/events
查詢活動列表（單筆查詢或分頁 + 篩選）

**Query Parameters**

| 參數 | 型別 | 說明 |
|------|------|------|
| `page` | number | 頁碼，預設 1 |
| `limit` | number | 每頁筆數，預設 20 |
| `keyword` | string | 模糊搜尋名稱/描述（ILIKE） |
| `category` | string | 分類篩選 |
| `status` | string | 狀態篩選（見 EventStatus） |
| `startDate` | string (ISO 8601) | 活動開始時間下限 |
| `endDate` | string (ISO 8601) | 活動開始時間上限 |

**Response**
```json
{
  "data": [ ...EventEntity ],
  "pagination": { "page": 1, "limit": 20, "total": 42 }
}
```

> 預設排除 `status = ended` 的活動。

---

### GET /v1/events/:eventId
取得單一活動詳情

**Response**
```json
{ "data": { ...EventEntity } }
```

**Response**
```json
{ "error": { "code": "EVENT_NOT_FOUND", "message": "活動不存在" } }
```

---

### PATCH /v1/events/:eventId
更新活動 (單筆)

**Request Body**（所有欄位皆為選填）
```json
{ "ticketLimit": 500, "guestAllowed": false }
```

**Response**
```json
{ "data": { "updated": true, "updatedAt": "2026-05-29T12:00:00Z" } }
```

---

### PATCH /v1/events
批量更新活動

**Request Body**
```json
{
  "updates": [
    { "eventId": "a3f9b2c1d0", "status": "closed" },
    { "eventId": "b1e8a4f2c9", "ticketLimit": 300 }
  ]
}
```

**Response**
```json
{
  "data": {
    "succeeded": ["a3f9b2c1d0"],
    "failed":    [{ "eventId": "b1e8a4f2c9", "error": "EVENT_ALREADY_STARTED" }]
  }
}
```

---

### DELETE /v1/events/:eventId
刪除活動（限尚未發布或尚未開始報名的活動）

**Response**
```json
{ "data": { "deleted": true } }
```

**Response (找不到活動)**
```json
{ "error": { "code": "EVENT_NOT_FOUND", "message": "活動不存在" } }
```

**Response (活動不能刪除)**
```json
{ "error": { "code": "EVENT_NOT_DELETABLE", "message": "活動不符合刪除條件" } }
```

---

## 6. 資料模型

### EventEntity（資料表：`events`）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `eventId` | varchar(50) | 每筆活動紀錄 ID 不重複 |
| `name` | varchar(255) | 活動名稱 |
| `description` | text | 活動說明 |
| `location` | varchar(255) | 地點 |
| `category` | varchar(50) | 分類 |
| `guestAllowed` | boolean | 是否允許外部人員 |
| `ticketLimit` | integer \| null | 報名上限（null = 無限制） |
| `remainingTickets` | integer | 剩餘名額 |
| `cancellationDeadline` | timestamptz \| null | 取消截止日 |
| `latitude` | decimal(20,16) | 緯度 |
| `longitude` | decimal(20,16) | 經度 |
| `checkinRadiusMeters` | integer | 打卡範圍（公尺） |
| `eventStartTime` | timestamptz | 活動開始時間 |
| `eventEndTime` | timestamptz | 活動結束時間 |
| `registrationStart` | timestamptz | 報名開始時間 |
| `registrationEnd` | timestamptz | 報名結束時間 |
| `faqs` | jsonb | FAQ 陣列 |
| `status` | varchar(20) | 見 EventStatus |
| `isDraft` | boolean | 是否為草稿 |
| `createdAt` | timestamptz | 建立時間 |
| `updatedAt` | timestamptz | 更新時間 |

### EventStatus

| 值 | 說明 |
|----|------|
| `not_open` | 尚未開始報名 |
| `registering` | 開放報名中 |
| `waitlist` | 額滿候補 |
| `closed` | 報名截止 |
| `ended` | 活動結束（預設不列於查詢） |

---

## 7. 錯誤碼

| HTTP | Code | 說明 |
|------|------|------|
| 400 | `BAD_REQUEST` | 請求格式或 Schema 驗證失敗 |
| 401 | `UNAUTHORIZED` | 缺少或無效的 Bearer Token |
| 401 | `TOKEN_EXPIRED` | JWT 已過期 |
| 401 | `INVALID_TOKEN` | JWT 簽名或格式無效 |
| 403 | `FORBIDDEN` | 角色權限不足 |
| 404 | `EVENT_NOT_FOUND` | 指定活動不存在 |
| 409 | `EVENT_NOT_DELETABLE` | 活動不符合刪除條件（已發布或已開始報名） |
| 500 | `INTERNAL_SERVER_ERROR` | 伺服器內部錯誤 |

---

## 8. 測試項目範例

測試採用 **Jest + Supertest + SQLite3（in-memory）**。每個 `describe` 區塊在 `beforeAll` 建立測試資料庫並取得對應角色的 token，在 `afterAll` 清除資料。

### 8.1 Auth Middleware

```ts
describe('Auth Middleware', () => {
  it('should return 401 when Authorization header is missing', async () => {
    const res = await request(app).get('/v1/events');
    // GET /v1/events is public; for a protected route:
    const res2 = await request(app).post('/v1/events').send({});
    expect(res2.status).toBe(401);
    expect(res2.body.error.code).toBe('UNAUTHORIZED');
  });

  it('should return 401 when token is malformed', async () => {
    const res = await request(app)
      .post('/v1/events')
      .set('Authorization', 'Bearer not.a.valid.token');
    expect(res.status).toBe(401);
    expect(res.body.error.code).toBe('INVALID_TOKEN');
  });

  it('should return 401 when token is expired', async () => {
    const expiredToken = generateToken({ userId: 'u_1', email: 'a@b.com', role: UserRole.WELFARE_MEMBER }, '-1s');
    const res = await request(app)
      .post('/v1/events')
      .set('Authorization', `Bearer ${expiredToken}`)
      .send({});
    expect(res.status).toBe(401);
    expect(res.body.error.code).toBe('TOKEN_EXPIRED');
  });

  it('should return 403 when employee attempts a write operation', async () => {
    const employeeToken = generateToken({ userId: 'u_emp', email: 'emp@b.com', role: UserRole.EMPLOYEE });
    const res = await request(app)
      .post('/v1/events')
      .set('Authorization', `Bearer ${employeeToken}`)
      .send({ name: 'test' });
    expect(res.status).toBe(403);
    expect(res.body.error.code).toBe('FORBIDDEN');
  });

  it('should pass through with a valid welfare_member token', async () => {
    const token = generateToken({ userId: 'u_wm', email: 'wm@b.com', role: UserRole.WELFARE_MEMBER });
    const res = await request(app)
      .get('/v1/events')
      .set('Authorization', `Bearer ${token}`);
    expect(res.status).toBe(200);
  });
});
```

---

### 8.2 POST /v1/events — 單筆建立

```ts
describe('POST /v1/events', () => {
  const token = generateToken({ userId: 'u_wm', email: 'wm@b.com', role: UserRole.WELFARE_MEMBER });

  it('should create an event and return 201 with eventId, isDraft, createdAt', async () => {
    const res = await request(app)
      .post('/v1/events')
      .set('Authorization', `Bearer ${token}`)
      .send({
        name: '2026 年末聚餐',
        location: '頂樓',
        category: '娛樂',
        guestAllowed: false,
        remainingTickets: 100,
        eventStartTime: '2026-12-25T18:00:00Z',
        eventEndTime:   '2026-12-25T22:00:00Z',
        registrationStart: '2026-11-01T00:00:00Z',
        registrationEnd:   '2026-12-01T23:59:59Z',
        status: 'not_open',
        isDraft: false,
      });
    expect(res.status).toBe(201);
    expect(res.body.data).toMatchObject({
      eventId:   expect.any(String),
      isDraft:   false,
      createdAt: expect.any(String),
    });
  });

  it('should return 400 when required fields are missing', async () => {
    const res = await request(app)
      .post('/v1/events')
      .set('Authorization', `Bearer ${token}`)
      .send({ name: 'Missing fields' });
    expect(res.status).toBe(400);
    expect(res.body.error.code).toBe('BAD_REQUEST');
  });

  it('should return 400 when status is an invalid string', async () => {
    const res = await request(app)
      .post('/v1/events')
      .set('Authorization', `Bearer ${token}`)
      .send({ /* valid body */ status: 'unknown_status' });
    expect(res.status).toBe(400);
  });
});
```

---

### 8.3 GET /v1/events — 列表查詢

```ts
describe('GET /v1/events', () => {
  it('should return paginated list excluding ended events by default', async () => {
    const res = await request(app).get('/v1/events');
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('data');
    expect(res.body).toHaveProperty('pagination');
    const statuses = res.body.data.map((e: any) => e.status);
    expect(statuses).not.toContain('ended');
  });

  it('should filter by keyword', async () => {
    const res = await request(app).get('/v1/events?keyword=聚餐');
    expect(res.status).toBe(200);
    res.body.data.forEach((e: any) => {
      expect(e.name + e.description).toMatch(/聚餐/);
    });
  });

  it('should filter by startDate and endDate', async () => {
    const res = await request(app).get('/v1/events?startDate=2026-12-01&endDate=2026-12-31');
    expect(res.status).toBe(200);
    res.body.data.forEach((e: any) => {
      expect(new Date(e.eventStartTime).getFullYear()).toBe(2026);
    });
  });
});
```

---

### 8.4 PATCH /v1/events — 批量更新

```ts
describe('PATCH /v1/events (batch update)', () => {
  const token = generateToken({ userId: 'u_wm', email: 'wm@b.com', role: UserRole.WELFARE_MEMBER });

  it('should return 207 with succeeded and failed arrays', async () => {
    const res = await request(app)
      .patch('/v1/events')
      .set('Authorization', `Bearer ${token}`)
      .send({
        updates: [
          { eventId: existingId, status: 'closed' },
          { eventId: 'nonexistent', ticketLimit: 10 },
        ],
      });
    expect(res.status).toBe(207);
    expect(res.body.data.succeeded).toContain(existingId);
    expect(res.body.data.failed[0].eventId).toBe('nonexistent');
    // totalProcessed は返さない（spec に存在しない）
    expect(res.body.data).not.toHaveProperty('totalProcessed');
  });
});
```

---

### 8.5 DELETE /v1/events/:eventId — 單筆刪除

```ts
describe('DELETE /v1/events/:eventId', () => {
  const token = generateToken({ userId: 'u_wm', email: 'wm@b.com', role: UserRole.WELFARE_MEMBER });

  it('should return 200 for a deletable (draft) event', async () => {
    const res = await request(app)
      .delete(`/v1/events/${draftEventId}`)
      .set('Authorization', `Bearer ${token}`);
    expect(res.status).toBe(200);
    expect(res.body.data.deleted).toBe(true);
  });

  it('should return 404 for a non-existent event', async () => {
    const res = await request(app)
      .delete('/v1/events/nonexistent_id')
      .set('Authorization', `Bearer ${token}`);
    expect(res.status).toBe(404);
    expect(res.body.error.code).toBe('EVENT_NOT_FOUND');
  });

  it('should return 409 for a published / registration-started event', async () => {
    const res = await request(app)
      .delete(`/v1/events/${publishedEventId}`)
      .set('Authorization', `Bearer ${token}`);
    expect(res.status).toBe(409);
    expect(res.body.error.code).toBe('EVENT_NOT_DELETABLE');
  });
});
```
