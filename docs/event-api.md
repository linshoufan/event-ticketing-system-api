# Event Management API

> 最後更新：2026-06-03

---

## 目錄

1. [專案結構](#1-專案結構)
2. [技術棧](#2-技術棧)
3. [快速啟動](#3-快速啟動)
4. [身分驗證與權限](#4-身分驗證與權限)
5. [API SPEC - 現有功能](#5-api-spec---現有功能)
6. [API SPEC - 批量操作](#6-api-spec---批量操作)
7. [API SPEC - Internal](#7-api-spec---internal)
8. [資料模型](#8-資料模型)
9. [實作重點](#9-實作重點)
10. [錯誤碼一覽](#10-錯誤碼一覽)
11. [測試](#11-測試)

---

## 1. 專案結構

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

---

## 4. 身分驗證與權限

### 角色清單

| 角色 | 值 | 說明 |
|------|----|------|
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
  "role": "welfare_member",
  "iat": 1748476800,
  "exp": 1748505600
}
```

目前 Event service 主要依 `role` 判斷權限。

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

Response 201:

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

```json
{ "data": { "...": "EventEntity" } }
```

Response 404:

```json
{ "error": { "code": "EVENT_NOT_FOUND", "message": "Event not found" } }
```

### PATCH /v1/events/{eventId}

更新單一活動。限 `welfare_member`。所有欄位皆為選填。

Request body:

```json
{
  "ticketLimit": 500,
  "guestAllowed": false,
  "status": "closed"
}
```

Response 200:

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

Response 207:

```json
{
  "data": {
    "succeeded": ["a3f9b2c1d0"],
    "failed": [{ "eventId": "b1e8a4f2c9", "error": "EVENT_NOT_FOUND" }]
  }
}
```

### DELETE /v1/events/{eventId}

刪除單一活動。限 `welfare_member`。

刪除條件：

- `isDraft = true` 可刪除。
- `isDraft = false` 但 `registrationStart` 尚未到達可刪除。
- 已發布且已開始報名不可刪除。

Response 200:

```json
{ "data": { "deleted": true } }
```

Response 404:

```json
{ "error": { "code": "EVENT_NOT_FOUND", "message": "Event not found" } }
```

Response 409:

```json
{ "error": { "code": "EVENT_NOT_DELETABLE", "message": "Event is not deletable" } }
```

---

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

### GET /v1/internal/events/{eventId}

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

| HTTP | Code | 說明 |
|------|------|------|
| 400 | `BAD_REQUEST` | 請求格式或 schema 驗證失敗 |
| 401 | `NOT_LOGGED_IN` | 缺少 Bearer Token |
| 401 | `INVALID_TOKEN` | JWT 簽名、格式、過期或 payload 無效 |
| 401 | `INVALID_INTERNAL_KEY` | Internal API key 錯誤 |
| 403 | `FORBIDDEN` | 角色權限不足 |
| 404 | `EVENT_NOT_FOUND` | 指定活動不存在 |
| 409 | `EVENT_NAME_ALREADY_EXISTS` | 活動名稱已存在 |
| 409 | `EVENT_NOT_DELETABLE` | 活動不符合刪除條件 |
| 422 | - | 批量建立全部失敗 |
| 500 | `INTERNAL_SERVER_ERROR` | 伺服器內部錯誤 |

---

## 11. 測試

Event service 測試採用 pytest + FastAPI TestClient + PostgreSQL 測試資料庫。

目前測試資料庫設定位於：

```text
backend/event/tests/conftest.py
```

重點測試覆蓋：

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

執行：

```bash
cd backend/event
pytest tests/ -q
```

目前預期結果：

```text
38 passed
```
