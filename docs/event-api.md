# Event Management API

> 最後更新：2026-06-03

---

## 目錄

1. [專案結構](#1-專案結構)
2. [技術棧](#2-技術棧)
3. [快速啟動](#3-快速啟動)
4. [身分驗證與權限](#4-身分驗證與權限)
<<<<<<< HEAD
5. [API SPEC — 現有功能](#5-api-spec--現有功能)
6. [資料模型](#6-資料模型)
7. [錯誤碼一覽](#7-錯誤碼一覽)
8. [測試案例](#8-測試案例)
=======
5. [API SPEC - 現有功能](#5-api-spec---現有功能)
6. [API SPEC - 批量操作](#6-api-spec---批量操作)
7. [API SPEC - Internal](#7-api-spec---internal)
8. [資料模型](#8-資料模型)
9. [實作重點](#9-實作重點)
10. [錯誤碼一覽](#10-錯誤碼一覽)
11. [測試](#11-測試)
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e

---

## 1. 專案結構

<<<<<<< HEAD
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
=======
```text
backend/event/
├── app/
│   ├── main.py                         # FastAPI app, exception handlers, router mount
│   ├── routers/
│   │   ├── events.py                   # /v1/events routes, including batch endpoints
│   │   └── internal.py                 # /v1/internal/events routes for service-to-service calls
│   ├── services/
│   │   └── event_service.py            # Event business logic
│   ├── repositories/
│   │   └── event_repository.py         # SQLAlchemy query/write logic
│   ├── schemas/
│   │   └── event.py                    # Pydantic request/response schemas
│   ├── models/
│   │   └── event.py                    # SQLAlchemy Event model
│   └── core/
│       ├── database.py                 # PostgreSQL production connection
│       ├── dependencies.py             # JWT auth + role dependency
│       ├── security.py                 # python-jose JWT decoding
│       ├── response.py                 # response wrappers
│       └── scheduler.py                # scheduled status transitions
├── migrations/
│   └── versions/                       # Alembic migrations
└── tests/
    ├── conftest.py                     # PostgreSQL test database
    ├── unit/
    └── integration/
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e
```

---

## 2. 技術棧

| 項目 | 套件 |
|------|------|
| Web Framework | FastAPI |
| ORM | SQLAlchemy + PostgreSQL |
| Migration | Alembic |
| 驗證 Schema | Pydantic |
| 身分驗證 | python-jose |
| 測試 | pytest + FastAPI TestClient + PostgreSQL test database |
| 排程 | APScheduler |

---

## 3. 快速啟動

從 repo root 安裝相依：

```bash
pip install -r requirements.txt
```

<<<<<<< HEAD
=======
設定環境變數或 `.env`：

```env
EVENT_DB_HOST=localhost
EVENT_DB_PORT=5432
EVENT_DB_USER=postgres
EVENT_DB_PASSWORD=postgres
EVENT_DB_NAME=event_db
JWT_SECRET_KEY=your_strong_secret_here
JWT_ALGORITHM=HS256
INTERNAL_API_KEY=dev-internal-key
```

執行 event service：

```bash
cd backend/event
uvicorn app.main:app --reload --port 8003
```

執行 event 測試：

```bash
cd backend/event
pytest tests/ -q
```

>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e
---

## 4. 身分驗證與權限

### 角色清單

| 角色 | 值 | 說明 |
|------|----|------|
<<<<<<< HEAD
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
=======
| `welfare_member` | `welfare_member` | 福委，可建立、更新、刪除活動 |
| `employee` | `employee` | 一般員工，可讀取活動資料 |
| `hr` | `hr` | HR，可讀取活動資料 |

舊文件中的 `admin` 角色已廢除，`user` 角色已更名為 `employee`。

### 權限矩陣

| 端點 | welfare_member | employee | hr |
|------|:--------------:|:--------:|:--:|
| GET /v1/events | yes | yes | yes |
| GET /v1/events/{eventId} | yes | yes | yes |
| POST /v1/events | yes | no | no |
| PATCH /v1/events/{eventId} | yes | no | no |
| PATCH /v1/events | yes | no | no |
| DELETE /v1/events/{eventId} | yes | no | no |
| POST /v1/events/batch | yes | no | no |
| POST /v1/events/batch/query | yes | yes | yes |
| DELETE /v1/events/batch | yes | no | no |
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e

### JWT 格式

Request header:

```http
Authorization: Bearer <token>
```

Token payload:

```json
{
  "user_id": "u_001",
  "email": "user@example.com",
  "role": "welfare_member"
}
```

<<<<<<< HEAD
**產生測試 Token（開發/測試用）**
```ts
import { generateToken, UserRole } from './src/middlewares/auth.middleware';
=======
目前 Event service 主要依 `role` 判斷權限。
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e

### Internal API 認證

跨服務呼叫使用 `X-Internal-Key`，不使用使用者 Bearer token。

```http
X-Internal-Key: <shared_secret>
```

Internal endpoint 詳細契約另見 `docs/internal-api-spec.md`。

---

## 5. API SPEC - 現有功能

Base URL:

```text
http://localhost:8003/v1
```

### POST /v1/events

建立單筆活動。限 `welfare_member`。

Request body:

```json
{
  "name": "2026 年末聚餐",
  "description": "全員參與",
  "location": "公司頂樓",
  "category": "娛樂",
  "guestAllowed": false,
  "ticketLimit": null,
  "remainingTickets": 100,
  "cancellationDeadline": null,
  "latitude": null,
  "longitude": null,
  "checkinRadiusMeters": null,
  "eventStartTime": "2026-12-25T18:00:00Z",
  "eventEndTime": "2026-12-25T22:00:00Z",
  "registrationStart": "2026-11-01T00:00:00Z",
  "registrationEnd": "2026-12-01T23:59:59Z",
  "faqs": [],
  "status": "not_open",
  "isDraft": false
}
```

<<<<<<< HEAD
**Response**
=======
Response 201:

>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e
```json
{
  "data": {
    "eventId": "a3f9b2c1d0",
    "isDraft": false,
    "createdAt": "2026-10-01T00:00:00Z"
  }
}
```

Notes:

- `eventId` 由 UUID hex 前 10 碼產生。
- `name` 必須唯一，重複名稱會造成 DB unique constraint failure。
- `eventEndTime` 必須晚於 `eventStartTime`。
- `registrationEnd` 必須晚於 `registrationStart`。

Response 409, 活動名稱已存在:

```json
{
  "error": {
    "code": "EVENT_NAME_ALREADY_EXISTS",
    "message": "Event name already exists"
  }
}
```

### GET /v1/events
<<<<<<< HEAD
查詢活動列表（單筆查詢或分頁 + 篩選）
=======
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e

查詢活動列表。所有已登入角色可用。

Query parameters:

| 參數 | 型別 | 說明 |
|------|------|------|
| `page` | number | 頁碼，預設 1 |
| `limit` | number | 每頁筆數，預設 20 |
| `keyword` | string | 模糊搜尋名稱或描述 |
| `category` | string | 分類篩選 |
| `status` | string | 狀態篩選，見 EventStatus |
| `startDate` | string | 活動開始時間下限，ISO 8601 |
| `endDate` | string | 活動開始時間上限，ISO 8601 |

Response 200:

<<<<<<< HEAD
**Response**
=======
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e
```json
{
  "data": [
    {
      "eventId": "a3f9b2c1d0",
      "name": "2026 年末聚餐",
      "description": "全員參與",
      "location": "公司頂樓",
      "category": "娛樂",
      "guestAllowed": false,
      "ticketLimit": null,
      "remainingTickets": 100,
      "cancellationDeadline": null,
      "latitude": null,
      "longitude": null,
      "checkinRadiusMeters": null,
      "eventStartTime": "2026-12-25T18:00:00Z",
      "eventEndTime": "2026-12-25T22:00:00Z",
      "registrationStart": "2026-11-01T00:00:00Z",
      "registrationEnd": "2026-12-01T23:59:59Z",
      "faqs": [],
      "status": "not_open",
      "isDraft": false,
      "createdAt": "2026-10-01T00:00:00Z",
      "updatedAt": null
    }
  ],
  "pagination": { "page": 1, "limit": 20, "total": 1 }
}
```

若未指定 `status`，預設排除 `ended` 活動。若指定 `status=ended`，會回傳 ended 活動。

### GET /v1/events/{eventId}

取得單一活動詳情。所有已登入角色可用。

Response 200:

<<<<<<< HEAD
**Response**
=======
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e
```json
{ "data": { "...": "EventEntity" } }
```

<<<<<<< HEAD
**Response**
=======
Response 404:

>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e
```json
{ "error": { "code": "EVENT_NOT_FOUND", "message": "Event not found" } }
```

### PATCH /v1/events/{eventId}

<<<<<<< HEAD
### PATCH /v1/events/:eventId
更新活動 (單筆)
=======
更新單一活動。限 `welfare_member`。所有欄位皆為選填。

Request body:
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e

```json
{
  "ticketLimit": 500,
  "guestAllowed": false,
  "status": "closed"
}
```

<<<<<<< HEAD
**Response**
=======
Response 200:

>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e
```json
{
  "data": {
    "updated": true,
    "updatedAt": "2026-05-29T12:00:00Z"
  }
}
```

Response 404:

```json
{ "error": { "code": "EVENT_NOT_FOUND", "message": "Event not found" } }
```

### PATCH /v1/events

批量更新活動。限 `welfare_member`。

Request body:

```json
{
  "updates": [
    { "eventId": "a3f9b2c1d0", "status": "closed" },
    { "eventId": "b1e8a4f2c9", "ticketLimit": 300 }
  ]
}
```

<<<<<<< HEAD
**Response**
=======
Response 207:

>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e
```json
{
  "data": {
    "succeeded": ["a3f9b2c1d0"],
    "failed": [{ "eventId": "b1e8a4f2c9", "error": "EVENT_NOT_FOUND" }]
  }
}
```

### DELETE /v1/events/{eventId}

<<<<<<< HEAD
### DELETE /v1/events/:eventId
刪除活動（限尚未發布或尚未開始報名的活動）

**Response**
=======
刪除單一活動。限 `welfare_member`。

刪除條件：

- `isDraft = true` 可刪除。
- `isDraft = false` 但 `registrationStart` 尚未到達可刪除。
- 已發布且已開始報名不可刪除。

Response 200:

>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e
```json
{ "data": { "deleted": true } }
```

<<<<<<< HEAD
**Response (找不到活動)**
=======
Response 404:

>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e
```json
{ "error": { "code": "EVENT_NOT_FOUND", "message": "Event not found" } }
```

<<<<<<< HEAD
**Response (活動不能刪除)**
=======
Response 409:

>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e
```json
{ "error": { "code": "EVENT_NOT_DELETABLE", "message": "Event is not deletable" } }
```

---

<<<<<<< HEAD
## 6. 資料模型
=======
## 6. API SPEC - 批量操作

### POST /v1/events/batch

批量新增活動。限 `welfare_member`。單次最多 100 筆。

Request body:

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
      "eventStartTime": "2027-01-15T08:00:00Z",
      "eventEndTime": "2027-01-15T20:00:00Z",
      "registrationStart": "2026-12-01T00:00:00Z",
      "registrationEnd": "2026-12-31T23:59:59Z",
      "status": "not_open",
      "isDraft": true
    }
  ]
}
```

Response 201, 全部成功:

```json
{
  "data": {
    "succeeded": [{ "eventId": "c2d1e0f3b4", "name": "Q1 員工旅遊" }],
    "failed": []
  }
}
```

Response 207, 部分成功:

```json
{
  "data": {
    "succeeded": [{ "eventId": "c2d1e0f3b4", "name": "Q1 員工旅遊" }],
    "failed": [{ "index": 1, "name": "Q1 員工旅遊", "error": "duplicate key value" }]
  }
}
```

Response 422, 全部失敗:

```json
{
  "data": {
    "succeeded": [],
    "failed": [{ "index": 0, "name": "Q1 員工旅遊", "error": "duplicate key value" }]
  }
}
```

### POST /v1/events/batch/query

批量查詢活動。所有已登入角色可用。單次最多 200 筆。

Request body:

```json
{
  "eventIds": ["a3f9b2c1d0", "b1e8a4f2c9", "nonexistent_id"]
}
```

Response 200:

```json
{
  "data": {
    "found": [{ "...": "EventEntity" }],
    "notFound": ["nonexistent_id"],
    "total": 2
  }
}
```

### DELETE /v1/events/batch

批量刪除活動。限 `welfare_member`。單次最多 100 筆。

Request body:

```json
{
  "eventIds": ["a3f9b2c1d0", "b1e8a4f2c9"]
}
```

Response 200, 全部成功:

```json
{
  "data": {
    "succeeded": ["a3f9b2c1d0", "b1e8a4f2c9"],
    "failed": []
  }
}
```

Response 207, 部分成功或部分不可刪:

```json
{
  "data": {
    "succeeded": ["a3f9b2c1d0"],
    "failed": [
      { "eventId": "b1e8a4f2c9", "error": "EVENT_NOT_DELETABLE" },
      { "eventId": "missing_id", "error": "EVENT_NOT_FOUND" }
    ]
  }
}
```

---

## 7. API SPEC - Internal
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e

### GET /v1/internal/events/{eventId}

<<<<<<< HEAD
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
=======
供 Transaction Service / Ticket Service 查詢單一活動詳情。回傳格式與公開端點 `GET /v1/events/{eventId}` 相同。

Request header:

```http
X-Internal-Key: <shared_secret>
```

Response 200:

```json
{ "data": { "...": "EventEntity" } }
```

Response 401:

```json
{ "error": { "code": "INVALID_INTERNAL_KEY", "message": "Invalid internal API key" } }
```

Response 404:

```json
{ "error": { "code": "EVENT_NOT_FOUND", "message": "Event not found" } }
```

Notes:

- 跨服務查詢一律使用此 endpoint。
- Public endpoint `GET /v1/events/{eventId}` 需要使用者 Bearer token，不適合 Ticket / Transaction 服務直接呼叫。

---

## 8. 資料模型

### EventEntity response 欄位

API 對外使用 camelCase。DB/model 內部使用 snake_case，response schema 會轉回 camelCase。

| API 欄位 | DB 欄位 | 型別 | 說明 |
|----------|---------|------|------|
| `eventId` | `event_id` | varchar(50) PK | UUID 前 10 碼 |
| `name` | `name` | varchar(255), unique | 活動名稱，不可重複 |
| `description` | `description` | text | 活動說明 |
| `location` | `location` | varchar(255) | 地點 |
| `category` | `category` | varchar(50), index | 分類 |
| `guestAllowed` | `guest_allowed` | boolean | 是否允許外部人員 |
| `ticketLimit` | `ticket_limit` | integer or null | 報名上限，null = 無限制 |
| `remainingTickets` | `remaining_tickets` | integer | 剩餘名額 |
| `cancellationDeadline` | `cancellation_deadline` | timestamptz or null | 取消截止日 |
| `latitude` | `latitude` | decimal(9,6) or null | 緯度 |
| `longitude` | `longitude` | decimal(9,6) or null | 經度 |
| `checkinRadiusMeters` | `checkin_radius_meters` | decimal(9,6) or null | 打卡範圍，公尺 |
| `eventStartTime` | `event_start_time` | timestamptz | 活動開始時間 |
| `eventEndTime` | `event_end_time` | timestamptz | 活動結束時間 |
| `registrationStart` | `registration_start` | timestamptz | 報名開始時間 |
| `registrationEnd` | `registration_end` | timestamptz | 報名結束時間 |
| `faqs` | `faqs` | json/jsonb | FAQ 陣列 |
| `status` | `status` | integer | 對外序列化成 EventStatus 字串 |
| `isDraft` | `is_draft` | boolean | 是否為草稿 |
| `createdAt` | `created_at` | timestamptz | 建立時間 |
| `updatedAt` | `updated_at` | timestamptz or null | 更新時間 |
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e

### EventStatus

DB 內部以 integer 儲存，API request/response 支援字串。

| DB 值 | API 值 | 說明 |
|-------|--------|------|
| 0 | `not_open` | 尚未開始報名 |
| 1 | `registering` | 開放報名中 |
| 2 | `waitlist` | 額滿候補 |
| 3 | `closed` | 報名截止 |
| 4 | `ended` | 活動結束 |

---

<<<<<<< HEAD
## 7. 錯誤碼
=======
## 9. 實作重點

- Public router 掛在 `backend/event/app/routers/events.py`，prefix 是 `/v1/events`。
- Internal router 掛在 `backend/event/app/routers/internal.py`，prefix 是 `/v1/internal/events`。
- FastAPI route 順序會優先比對靜態路徑，因此 `/batch` 和 `/batch/query` 可和 `/{eventId}` 共存。
- `role_required(...)` 會解析 Bearer token 並檢查 `role`。
- Pydantic validation error 統一回 `400 BAD_REQUEST`。
- Batch create 每筆獨立 commit；單筆失敗會 rollback 該筆並繼續處理下一筆。
- `events.name` 有 unique constraint，重複名稱會造成 batch create partial failure。
- 測試使用 PostgreSQL 測試資料庫，透過 `EVENT_DB_*` 環境變數連線。
- Production/runtime DB 仍使用 PostgreSQL，由 `backend/event/app/core/database.py` 的設定決定。

---

## 10. 錯誤碼一覽
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e

| HTTP | Code | 說明 |
|------|------|------|
| 400 | `BAD_REQUEST` | 請求格式或 schema 驗證失敗 |
| 401 | `NOT_LOGGED_IN` | 缺少 Bearer Token |
| 401 | `INVALID_TOKEN` | JWT 簽名、格式、過期或 payload 無效 |
| 401 | `INVALID_INTERNAL_KEY` | Internal API key 錯誤 |
| 403 | `FORBIDDEN` | 角色權限不足 |
| 404 | `EVENT_NOT_FOUND` | 指定活動不存在 |
<<<<<<< HEAD
| 409 | `EVENT_NOT_DELETABLE` | 活動不符合刪除條件（已發布或已開始報名） |
=======
| 409 | `EVENT_NAME_ALREADY_EXISTS` | 活動名稱已存在 |
| 409 | `EVENT_NOT_DELETABLE` | 活動不符合刪除條件 |
| 422 | - | 批量建立全部失敗 |
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e
| 500 | `INTERNAL_SERVER_ERROR` | 伺服器內部錯誤 |

---

<<<<<<< HEAD
## 8. 測試項目範例
=======
## 11. 測試
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e

Event service 測試採用 pytest + FastAPI TestClient + PostgreSQL 測試資料庫。

<<<<<<< HEAD
### 8.1 Auth Middleware
=======
目前測試資料庫設定位於：
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e

```text
backend/event/tests/conftest.py
```

重點測試覆蓋：

<<<<<<< HEAD
### 8.2 POST /v1/events — 單筆建立
=======
- Auth: missing token、invalid token、expired token、role forbidden。
- POST `/v1/events`: 建立成功、重複名稱回 409、缺欄位回 400、非法 status 回 400。
- GET `/v1/events`: pagination、keyword、category、status、startDate、endDate，預設排除 ended。
- GET `/v1/events/{eventId}`: success、404、401。
- PATCH `/v1/events/{eventId}`: success、404、employee/hr forbidden。
- PATCH `/v1/events`: batch update success、partial failure、forbidden。
- POST `/v1/events/batch`: success、duplicate name partial failure、超過 100 筆、forbidden。
- POST `/v1/events/batch/query`: found/notFound、超過 200 筆。
- DELETE `/v1/events/{eventId}`: draft 可刪、報名前可刪、已開始報名不可刪、404、forbidden。
- DELETE `/v1/events/batch`: all success、partial failure、超過 100 筆。
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e

執行：

```bash
cd backend/event
pytest tests/ -q
```

目前預期結果：

<<<<<<< HEAD
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
=======
```text
38 passed
>>>>>>> c51e8406a4045fd01cd4b4e023201d6fc929993e
```
