# Event Management API

> 最後更新：2026-06-02

---

## 目錄

1. [專案結構](#1-專案結構)
2. [技術棧](#2-技術棧)
3. [快速啟動](#3-快速啟動)
4. [身分驗證與權限](#4-身分驗證與權限)
5. [API SPEC — 現有功能](#5-api-spec--現有功能)
6. [API SPEC — 批量操作（新增）](#6-api-spec--批量操作新增)
7. [資料模型](#7-資料模型)
8. [整合新功能的步驟](#8-整合新功能的步驟)
9. [錯誤碼一覽](#9-錯誤碼一覽)
10. [測試案例](#10-測試案例)

---

## 1. 專案結構

```
src/
├── app.ts                        # Express App（需掛載 batchRouter，見第 8 節）
├── server.ts                     # 啟動入口
├── controller/
│   ├── event.controller.ts       # 單筆 CRUD
│   └── batch.controller.ts       # 批量 CRUD（新增）
├── service/
│   ├── event.service.ts          # 單筆業務邏輯
│   └── batch.service.ts          # 批量業務邏輯（新增）
├── route/
│   ├── event.route.ts            # /v1/events 路由
│   └── batch.route.ts            # /v1/events/batch 路由（新增）
├── schema/
│   ├── event.schema.ts           # 單筆 Zod Schema
│   └── batch.schema.ts           # 批量 Zod Schema（新增）
├── middlewares/
│   └── auth.middleware.ts        # JWT 驗證 + 角色檢查（新增）
├── model/event.model.ts
├── interface/event.interface.ts
├── validate/event.middleware.ts
└── core/database.ts
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

`.env` 必要欄位：

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_NAME=event_db
JWT_SECRET=your_strong_secret_here   # 新增：JWT 簽名金鑰
```

---

## 4. 身分驗證與權限

### 角色清單

| 角色 | 值 | 說明 |
|------|----|------|
| `welfare_member` | `welfare_member` | 福委，可建立／更新／刪除活動 |
| `employee` | `employee` | 一般員工，唯讀活動資料 |
| `hr` | `hr` | HR，可查看報名與票券詳情 |

> **注意**：舊文件中的 `admin` 角色已廢除，`user` 角色已更名為 `employee`，請更新任何現有的 token payload 與測試 fixture。

### 各端點權限矩陣

| 端點 | welfare_member | employee | hr |
|------|:--------------:|:--------:|:--:|
| GET /v1/events | ✅ | ✅ | ✅ |
| GET /v1/events/:id | ✅ | ✅ | ✅ |
| POST /v1/events | ✅ | ❌ | ❌ |
| PATCH /v1/events/:id | ✅ | ❌ | ❌ |
| PATCH /v1/events (batch update) | ✅ | ❌ | ❌ |
| DELETE /v1/events/:id | ✅ | ❌ | ❌ |
| POST /v1/events/batch | ✅ | ❌ | ❌ |
| POST /v1/events/batch/query | ✅ | ✅ | ✅ |
| DELETE /v1/events/batch | ✅ | ❌ | ❌ |

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
  "role": "welfare_member",
  "iat": 1748476800,
  "exp": 1748505600
}
```

**產生測試 Token（開發用）**
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

**Response 201**
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
查詢活動列表（分頁 + 篩選）

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

**Response 200**
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

**Response 200**
```json
{ "data": { ...EventEntity } }
```

**Response 404**
```json
{ "error": { "code": "EVENT_NOT_FOUND", "message": "活動不存在" } }
```

---

### PATCH /v1/events/:eventId
更新單一活動（部分更新）

**Request Body**（所有欄位皆為選填）
```json
{ "ticketLimit": 500, "guestAllowed": false }
```

**Response 200**
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

**Response 207**
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
刪除單一活動（僅限尚未發布或尚未開始報名的活動）

**Response 200**
```json
{ "data": { "deleted": true } }
```

**Response 404**
```json
{ "error": { "code": "EVENT_NOT_FOUND", "message": "活動不存在" } }
```

**Response 409**
```json
{ "error": { "code": "EVENT_NOT_DELETABLE", "message": "活動不符合刪除條件" } }
```

---

## 6. API SPEC — 批量操作（新增）

> 所有批量端點皆需要 `Authorization: Bearer <token>` 標頭。

---

### POST /v1/events/batch
批量新增活動（限 welfare_member）

**Request Body**
```json
{
  "events": [
    {
      "name": "Q1 員工旅遊",
      "description": "北海岸一日遊",
      "location": "石門水庫",
      "category": "旅遊",
      "guestAllowed": false,
      "remainingTickets": 50,
      "eventStartTime":  "2027-01-15T08:00:00Z",
      "eventEndTime":    "2027-01-15T20:00:00Z",
      "registrationStart": "2026-12-01T00:00:00Z",
      "registrationEnd":   "2026-12-31T23:59:59Z",
      "status": "not_open",
      "isDraft": true
    }
  ]
}
```

**限制**：單次最多 100 筆

**Response 201**（全部成功）
```json
{
  "data": {
    "succeeded": [{ "eventId": "c2d1e0f3b4", "name": "Q1 員工旅遊" }],
    "failed":    []
  }
}
```

**Response 207**（部分成功）
```json
{
  "data": {
    "succeeded": [{ "eventId": "c2d1e0f3b4", "name": "Q1 員工旅遊" }],
    "failed":    [{ "index": 1, "name": "重複活動", "error": "duplicate key value" }]
  }
}
```

**Response 422**（全部失敗）

---

### POST /v1/events/batch/query
批量查詢活動（所有已登入使用者）

**Request Body**
```json
{
  "eventIds": ["a3f9b2c1d0", "b1e8a4f2c9", "nonexistent_id"]
}
```

**限制**：單次最多 200 筆

**Response 200**
```json
{
  "data": {
    "found":    [ ...EventEntity ],
    "notFound": ["nonexistent_id"],
    "total":    2
  }
}
```

---

### DELETE /v1/events/batch
批量刪除活動（限 welfare_member）

**Request Body**
```json
{
  "eventIds": ["a3f9b2c1d0", "b1e8a4f2c9"]
}
```

**限制**：單次最多 100 筆

**Response 200**（全部成功）
```json
{
  "data": {
    "succeeded": ["a3f9b2c1d0", "b1e8a4f2c9"],
    "failed":    []
  }
}
```

**Response 207**（部分成功）
```json
{
  "data": {
    "succeeded": ["a3f9b2c1d0"],
    "failed":    [{ "eventId": "b1e8a4f2c9", "error": "EVENT_NOT_FOUND" }]
  }
}
```

---

## 7. 資料模型

### EventEntity（資料表：`events`）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `eventId` | varchar(50) PK | UUID 前 10 碼 |
| `name` | varchar(255) | 活動名稱 |
| `description` | text | 活動說明 |
| `location` | varchar(255) | 地點 |
| `category` | varchar(50) | 分類（有 Index） |
| `guestAllowed` | boolean | 是否允許外部人員 |
| `ticketLimit` | integer \| null | 報名上限（null = 無限制） |
| `remainingTickets` | integer | 剩餘名額 |
| `cancellationDeadline` | timestamptz \| null | 取消截止日 |
| `latitude` | decimal(9,6) | 緯度 |
| `longitude` | decimal(9,6) | 經度 |
| `checkinRadiusMeters` | decimal(9,6) | 打卡範圍（公尺） |
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

## 8. 整合新功能的步驟

### Step 1：安裝 jsonwebtoken

```bash
npm install jsonwebtoken
npm install -D @types/jsonwebtoken
```

### Step 2：在 `.env` 加入 JWT_SECRET

```env
JWT_SECRET=your_strong_secret_at_least_32_chars
```

### Step 3：在 `app.ts` 掛載 batchRouter

```ts
// app.ts 新增以下兩行
import batchRouter from './route/batch.route';
// ...
app.use('/v1/events/batch', batchRouter);  // 必須在 eventRouter 之前註冊
app.use('/v1/events', eventRouter);
```

> **注意**：`/v1/events/batch` 必須在 `/v1/events` 之前，否則 Express 會將 `batch` 誤判為 `:eventId`。

### Step 4（選用）：在 event.route.ts 現有端點加上 Auth Guard

```ts
import { requireAuth, requireRole, UserRole } from '../middlewares/auth.middleware';

const WRITE_ROLES = [UserRole.WELFARE_MEMBER];

router.post('/',          requireAuth, requireRole(WRITE_ROLES), validate(createEventSchema), eventController.createEvent);
router.patch('/:eventId', requireAuth, requireRole(WRITE_ROLES), validate(updateEventSchema), eventController.updateEvent);
router.delete('/:eventId',requireAuth, requireRole(WRITE_ROLES), eventController.deleteEvent);
```

---

## 9. 錯誤碼一覽

| HTTP | Code | 說明 |
|------|------|------|
| 400 | `BAD_REQUEST` | 請求格式或 Schema 驗證失敗 |
| 401 | `UNAUTHORIZED` | 缺少或無效的 Bearer Token |
| 401 | `TOKEN_EXPIRED` | JWT 已過期 |
| 401 | `INVALID_TOKEN` | JWT 簽名或格式無效 |
| 403 | `FORBIDDEN` | 角色權限不足 |
| 404 | `EVENT_NOT_FOUND` | 指定活動不存在 |
| 409 | `EVENT_NOT_DELETABLE` | 活動不符合刪除條件（已發布或已開始報名） |
| 422 | — | 批量操作全部失敗 |
| 500 | `INTERNAL_SERVER_ERROR` | 伺服器內部錯誤 |

---

## 10. 測試案例

測試採用 **Jest + Supertest + SQLite3（in-memory）**。每個 `describe` 區塊在 `beforeAll` 建立測試資料庫並取得對應角色的 token，在 `afterAll` 清除資料。

### 10.1 Auth Middleware

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

### 10.2 POST /v1/events — 單筆建立

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

### 10.3 GET /v1/events — 列表查詢

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

### 10.4 PATCH /v1/events — 批量更新

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

### 10.5 POST /v1/events/batch — 批量新增

```ts
describe('POST /v1/events/batch', () => {
  const token = generateToken({ userId: 'u_wm', email: 'wm@b.com', role: UserRole.WELFARE_MEMBER });

  const validEvent = {
    name: 'Q1 員工旅遊',
    description: '北海岸一日遊',
    location: '石門水庫',
    category: '旅遊',
    guestAllowed: false,
    remainingTickets: 50,
    eventStartTime:    '2027-01-15T08:00:00Z',
    eventEndTime:      '2027-01-15T20:00:00Z',
    registrationStart: '2026-12-01T00:00:00Z',
    registrationEnd:   '2026-12-31T23:59:59Z',
    status:  'not_open',
    isDraft: true,
  };

  it('should return 201 when all events are created successfully', async () => {
    const res = await request(app)
      .post('/v1/events/batch')
      .set('Authorization', `Bearer ${token}`)
      .send({ events: [validEvent] });
    expect(res.status).toBe(201);
    expect(res.body.data.succeeded).toHaveLength(1);
    expect(res.body.data.failed).toHaveLength(0);
  });

  it('should return 207 on partial success', async () => {
    const duplicate = { ...validEvent }; // 重複名稱觸發 DB 衝突
    const res = await request(app)
      .post('/v1/events/batch')
      .set('Authorization', `Bearer ${token}`)
      .send({ events: [validEvent, duplicate] });
    expect(res.status).toBe(207);
    expect(res.body.data.failed.length).toBeGreaterThan(0);
  });

  it('should return 400 when events array exceeds 100 items', async () => {
    const tooMany = Array(101).fill(validEvent);
    const res = await request(app)
      .post('/v1/events/batch')
      .set('Authorization', `Bearer ${token}`)
      .send({ events: tooMany });
    expect(res.status).toBe(400);
  });

  it('should return 403 for employee role', async () => {
    const empToken = generateToken({ userId: 'u_emp', email: 'e@b.com', role: UserRole.EMPLOYEE });
    const res = await request(app)
      .post('/v1/events/batch')
      .set('Authorization', `Bearer ${empToken}`)
      .send({ events: [validEvent] });
    expect(res.status).toBe(403);
  });
});
```

---

### 10.6 POST /v1/events/batch/query — 批量查詢

```ts
describe('POST /v1/events/batch/query', () => {
  const token = generateToken({ userId: 'u_emp', email: 'emp@b.com', role: UserRole.EMPLOYEE });

  it('should return found and notFound arrays', async () => {
    const res = await request(app)
      .post('/v1/events/batch/query')
      .set('Authorization', `Bearer ${token}`)
      .send({ eventIds: [existingId, 'ghost_id'] });
    expect(res.status).toBe(200);
    expect(res.body.data.found).toHaveLength(1);
    expect(res.body.data.notFound).toContain('ghost_id');
  });

  it('should return 400 when eventIds exceeds 200 items', async () => {
    const tooMany = Array(201).fill('id');
    const res = await request(app)
      .post('/v1/events/batch/query')
      .set('Authorization', `Bearer ${token}`)
      .send({ eventIds: tooMany });
    expect(res.status).toBe(400);
  });
});
```

---

### 10.7 DELETE /v1/events/batch — 批量刪除

```ts
describe('DELETE /v1/events/batch', () => {
  const token = generateToken({ userId: 'u_wm', email: 'wm@b.com', role: UserRole.WELFARE_MEMBER });

  it('should return 200 with all succeeded when all events are deletable', async () => {
    const res = await request(app)
      .delete('/v1/events/batch')
      .set('Authorization', `Bearer ${token}`)
      .send({ eventIds: [draftEventId1, draftEventId2] });
    expect(res.status).toBe(200);
    expect(res.body.data.succeeded).toEqual([draftEventId1, draftEventId2]);
    expect(res.body.data.failed).toHaveLength(0);
  });

  it('should return 207 when some events are not deletable', async () => {
    const res = await request(app)
      .delete('/v1/events/batch')
      .set('Authorization', `Bearer ${token}`)
      .send({ eventIds: [draftEventId1, publishedEventId] });
    expect(res.status).toBe(207);
    expect(res.body.data.failed[0].error).toBe('EVENT_NOT_DELETABLE');
  });

  it('should return 400 when eventIds exceeds 100 items', async () => {
    const tooMany = Array(101).fill('id');
    const res = await request(app)
      .delete('/v1/events/batch')
      .set('Authorization', `Bearer ${token}`)
      .send({ eventIds: tooMany });
    expect(res.status).toBe(400);
  });
});
```

---

### 10.8 DELETE /v1/events/:eventId — 單筆刪除

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
