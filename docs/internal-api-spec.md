# Internal API Spec

這份文件給微服務之間互相呼叫使用。
所有 internal endpoint 都需要帶 `X-Internal-Key` header，key 值取自共用的 `.env` 設定 `INTERNAL_API_KEY`。

---

## 認證

所有 internal endpoint 均需要在 request header 中帶入：

```
X-Internal-Key: <shared_secret>
```

- 未帶 header → `422 Unprocessable Entity`
- key 值錯誤 → `401 Unauthorized`

---

# Account Service — Internal API Spec

Base URL（K8s 內部）：`http://account-service:8000`
Base URL（local）：`http://localhost:8000`

## Endpoints

### GET `/v1/internal/users/{user_id}/registration-profile`

取得使用者的報名狀態與個人偏好，供報名前資格驗證與自動填入使用。

**Path Parameters**

| 參數 | 型別 | 說明 |
|------|------|------|
| user_id | string (UUID) | 使用者 ID |

**Response 200**

```json
{
  "data": {
    "userId": "abc-123",
    "role": "employee",
    "registrationStatus": "active",
    "unlockAt": null,
    "autofill": {
      "dietType": "non-veg",
      "selfDriving": false
    },
    "preferences": ["sport", "food"]
  }
}
```

| 欄位 | 型別 | 說明 |
|------|------|------|
| registrationStatus | string | `active` / `locked` |
| unlockAt | string (ISO 8601) \| null | locked 狀態的解鎖時間；active 時為 null |
| autofill.dietType | string | `veg` / `non-veg` |
| autofill.selfDriving | boolean | 是否自駕 |
| preferences | string[] | 興趣標籤，可能為空陣列 |

**Error Responses**

| Status | code | 說明 |
|--------|------|------|
| 401 | `INVALID_INTERNAL_KEY` | key 值錯誤 |
| 404 | `USER_NOT_FOUND` | 使用者不存在 |

---

### POST `/v1/internal/users/{user_id}/punish`

對使用者執行處罰：將 `registrationStatus` 設為 `locked`，並設定 `unlockAt` 為**當下時間 + 30 天**。
若使用者已是 locked 狀態，`unlockAt` 會被重置（從現在起再算 30 天）。

**Path Parameters**

| 參數 | 型別 | 說明 |
|------|------|------|
| user_id | string (UUID) | 使用者 ID |

**Request Body**

無。

**Response 200**

```json
{
  "data": {
    "userId": "abc-123",
    "registrationStatus": "locked",
    "unlockAt": "2026-06-20T08:00:00+00:00"
  }
}
```

**Error Responses**

| Status | code | 說明 |
|--------|------|------|
| 401 | `INVALID_INTERNAL_KEY` | key 值錯誤 |
| 404 | `USER_NOT_FOUND` | 使用者不存在 |

---

## 使用場景

- **報名前驗證**：Transaction Service 在使用者送出報名前，呼叫 `registration-profile` 確認 `registrationStatus == "active"`；若為 `locked`則拒絕報名並告知 `unlockAt`。
- **爽約處罰**：活動結束後若使用者爽約，Transaction Service 呼叫 `punish` 鎖定帳號 30 天。

## 自動解鎖機制

Account Service 內建排程任務，**每天凌晨 1 點**自動掃描 DB：
- `registrationStatus == "locked"` 且 `unlockAt <= 當前時間` 的使用者會自動解鎖
- 解鎖後 `registrationStatus → active`，`unlockAt → null`

Transaction Service 不需要主動呼叫任何 API 來解鎖，時間到了會自動處理。
若需要提前解鎖，請由 welfare_member 透過 `PATCH /v1/users/{userId}/unlock` 手動操作。

---
---

# Event Service — Internal API Spec

Base URL（K8s 內部）：`http://event-service:8003`
Base URL（local）：`http://localhost:8003`

認證方式與 Account Service 段落相同（`X-Internal-Key` header），key 值取自共用的 `INTERNAL_API_KEY`。

## Endpoints

### GET `/v1/internal/events/{eventId}`

取得單一活動詳情，供 Transaction Service / Ticket Service 做跨服務查詢使用。
回傳格式與公開端點 `GET /v1/events/{eventId}` 相同，但不需要使用者 Bearer token。

**Path Parameters**

| 參數 | 型別 | 說明 |
|------|------|------|
| eventId | string | 活動 ID |

**Request Headers**

```http
X-Internal-Key: <shared_secret>
```

**Response 200**

```json
{
  "data": {
    "eventId": "event_002",
    "name": "Family Day",
    "description": "親子同樂活動",
    "location": "Taipei",
    "category": "family",
    "guestAllowed": true,
    "ticketLimit": 100,
    "remainingTickets": 42,
    "cancellationDeadline": "2026-06-01T00:00:00Z",
    "latitude": 25.033,
    "longitude": 121.565,
    "checkinRadiusMeters": 100,
    "eventStartTime": "2026-06-20T10:00:00Z",
    "eventEndTime": "2026-06-20T12:00:00Z",
    "registrationStart": "2026-05-01T00:00:00Z",
    "registrationEnd": "2026-06-15T23:59:59Z",
    "faqs": [],
    "status": "registering",
    "isDraft": false,
    "createdAt": "2026-05-01T00:00:00Z",
    "updatedAt": null
  }
}
```

**Error Responses**

| Status | code | 說明 |
|--------|------|------|
| 401 | `INVALID_INTERNAL_KEY` | key 值錯誤 |
| 404 | `EVENT_NOT_FOUND` | 活動不存在 |

## 使用場景（Event Service）

- **報名前資格/容量檢查**：Transaction Service 查活動狀態、報名期間、名額與取消截止時間。
- **票券顯示與 check-in**：Ticket Service 查活動名稱、開始/結束時間、地點、座標與 check-in 半徑。
- **跨服務查詢不可呼叫 public Event API**：`GET /v1/events/{eventId}` 需要使用者 Bearer token；service-to-service 一律呼叫 `GET /v1/internal/events/{eventId}`。

---
---

# Ticket Service — Internal API Spec
>
> 本段落由 Transaction Service 提出，作為 Transaction → Ticket 跨服務互動的契約。
> 在 Ticket Service 完成這幾個 endpoint、且 Transaction Service 的 `.env` 設定
> `TICKET_SERVICE_ENABLED=true` 之前，Transaction Service 內部會以 mock client 模擬呼叫
> （`issue_ticket` 產生 `mock-<uuid>` 字串，`void` / `list-no-show` 為 no-op）。
> Ticket Service 完成後切換 flag 即可無痛接入，Transaction Service service 層程式碼不會改動。

Base URL（K8s 內部）：`http://ticket-service:8001`
Base URL（local）：`http://localhost:8001`

認證方式與 Account Service 段落相同（`X-Internal-Key` header），key 值取自共用的 `INTERNAL_API_KEY`。

## 整體模型

- Transaction Service 是「報名紀錄的真實來源」（誰報了誰沒報、誰在 waitlist）
- Ticket Service 是「票券生命週期的真實來源」（票券狀態 unused / used / invalid，QR payload, check-in）
- 因此 `confirmed` 報名 ↔ ticket 為 1:1 對應；`waitlist` / `cancelled` 報名都不對應到 ticket

呼叫關係：

```
[使用者] → POST /v1/transactions → Transaction Service
                                        │
                                        ├─ GET registration-profile (Account internal)
                                        ├─ GET event detail        (Event internal)
                                        └─ POST /v1/internal/tickets (Ticket internal)
```

---

### POST `/v1/internal/tickets`

配發票券。Transaction Service 在「報名成功且狀態為 confirmed」時呼叫；waitlist 不會呼叫；
waitlist 候補升為 confirmed 時也會呼叫。

**Request Body**

```json
{
  "userId": "abc-123",
  "eventId": "evt-2026-summer-party",
  "transactionId": "tx-uuid-xyz"
}
```

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| userId | string | True | 報名者 user_id |
| eventId | string | True | 活動 event_id |
| transactionId | string | True | 對應的報名紀錄 ID（給 Ticket Service 留作審計反查用） |

**Response 201**

```json
{
  "data": {
    "ticketId": "tkt-uuid-abc",
    "userId": "abc-123",
    "eventId": "evt-2026-summer-party",
    "status": "unused",
    "issuedAt": "2026-05-26T08:00:00+00:00"
  }
}
```

| 欄位 | 型別 | 說明 |
|------|------|------|
| ticketId | string | 新建立的票券 ID（Transaction Service 會把此 ID 存在 transactions.ticket_id） |
| status | string | 初始一律為 `unused` |

**Behavior**

- 若 `(userId, eventId)` 已存在 active ticket，請回 `409 TICKET_ALREADY_EXISTS` 並附現有 ticketId；Transaction Service 會把此情況視為冪等成功（理論上不會發生，因為 transactions 表的 partial unique index 已守住）

**Error Responses**

| Status | code | 說明 |
|--------|------|------|
| 401 | `INVALID_INTERNAL_KEY` | key 值錯誤 |
| 409 | `TICKET_ALREADY_EXISTS` | 該 user 對該 event 已有 active ticket |

---

### DELETE `/v1/internal/tickets/{ticket_id}`

作廢票券。Transaction Service 在使用者取消 confirmed 報名時呼叫。

**Path Parameters**

| 參數 | 型別 | 說明 |
|------|------|------|
| ticket_id | string | 要作廢的票券 ID |

**Response 200**

```json
{
  "data": {
    "ticketId": "tkt-uuid-abc",
    "voided": true
  }
}
```

**Behavior**

- 若 ticket 已 check-in（`status=used`）→ 回 `409 ALREADY_USED`
- 若 ticket 不存在 → 回 `404`（Transaction Service 會視為冪等成功）
- 否則直接刪除 record 或標記為 voided（依 Ticket Service 內部設計）

**Error Responses**

| Status | code | 說明 |
|--------|------|------|
| 401 | `INVALID_INTERNAL_KEY` | key 值錯誤 |
| 404 | `TICKET_NOT_FOUND` | 票券不存在（Transaction Service 視為冪等成功） |
| 409 | `ALREADY_USED` | 票券已 check-in，不能作廢 |

---

### DELETE `/v1/internal/tickets/events/{eventId}`

刪除某活動底下所有票券。Event Service 在刪除活動前呼叫，避免活動已不存在但使用者票券列表仍出現 `Unknown Event`。

**Path Parameters**

| 參數 | 型別 | 說明 |
|------|------|------|
| eventId | string | 活動 ID |

**Response 200**

```json
{
  "data": {
    "eventId": "evt-2026-summer-party",
    "deletedCount": 12
  }
}
```

**Behavior**

- 刪除該 `eventId` 底下所有 ticket records，包含 `unused` / `used` / `invalid`
- 若該活動沒有任何 ticket，仍回 `200` 且 `deletedCount=0`
- Event Service 會先呼叫此 API；若呼叫失敗，Event Service 不會刪除 event，避免 orphan tickets

**Error Responses**

| Status | code | 說明 |
|--------|------|------|
| 401 | `INVALID_INTERNAL_KEY` | key 值錯誤 |

---

### GET `/v1/internal/tickets/no-show`

撈出某活動結束後、所有「狀態仍為 unused」的 ticket 清單，供 Transaction Service 跑
No-Show punishment 排程使用。

**Query Parameters**

| 參數 | 型別 | 必填 | 說明 |
|------|------|------|------|
| eventId | string | ✅ | 活動 ID |

**Response 200**

```json
{
  "data": {
    "eventId": "evt-2026-summer-party",
    "ticketIds": ["tkt-1", "tkt-2", "tkt-3"]
  }
}
```

**Behavior**

- 只回傳 `status='unused'` 且 `event_end_time < now()` 的 ticket
- 若活動尚未結束，回 `400 EVENT_NOT_ENDED`（Transaction Service 不會在活動結束前呼叫此 API，但 Ticket Service 仍應 defensively 檢查）

**Error Responses**

| Status | code | 說明 |
|--------|------|------|
| 400 | `EVENT_NOT_ENDED` | 活動尚未結束 |
| 401 | `INVALID_INTERNAL_KEY` | key 值錯誤 |

---

## 使用場景（Ticket Service）

- **報名成功 (confirmed)**：Transaction Service 取得 ticketId 後寫回自己的 `transactions.ticket_id`
- **取消報名 (was confirmed)**：Transaction Service 在更新 `status='cancelled'` 後呼叫 DELETE
- **刪除活動**：Event Service 刪除活動前呼叫 `DELETE /v1/internal/tickets/events/{eventId}` 清除該活動所有票券
- **Waitlist 補位**：候補升為 confirmed 時，先呼叫 POST 拿到新 ticketId，再 update transaction
- **No-Show 偵測**：每日排程或活動結束後手動觸發，呼叫此 endpoint 撈名單，再對應到 user_ids 餵給 Account Service 的 `POST /v1/internal/users/{user_id}/punish`
