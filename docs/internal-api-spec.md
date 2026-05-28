# Account Service — Internal API Spec

這份文件給其他微服務（例如 Transaction Service）使用。
所有 internal endpoint 都需要帶 `X-Internal-Key` header，key 值請向帳號服務維護者索取(透過 `.env` 中的 `INTERNAL_API_KEY`)。

---

## 認證

所有 internal endpoint 均需要在 request header 中帶入：

```
X-Internal-Key: <shared_secret>
```

- 未帶 header → `422 Unprocessable Entity`
- key 值錯誤 → `401 Unauthorized`

---

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

- **報名前驗證**：Transaction Service 在使用者送出報名前，呼叫 `registration-profile` 確認 `registrationStatus == "active"`；若為 `locked` 則拒絕報名並告知 `unlockAt`。
- **爽約處罰**：活動結束後若使用者爽約，Transaction Service 呼叫 `punish` 鎖定帳號 30 天。

## 自動解鎖機制

Account Service 內建排程任務，**每天凌晨 1 點**自動掃描 DB：
- `registrationStatus == "locked"` 且 `unlockAt <= 當前時間` 的使用者會自動解鎖
- 解鎖後 `registrationStatus → active`，`unlockAt → null`

Transaction Service 不需要主動呼叫任何 API 來解鎖，時間到了會自動處理。
若需要提前解鎖，請由 welfare_member 透過 `PATCH /v1/users/{userId}/unlock` 手動操作。

---
---

# Ticket Service — Internal API Spec (Proposed by Transaction Service)

> **Status: 待 Ticket Service 實作**
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
                                        ├─ GET event detail        (Event public)
                                        └─ POST /v1/internal/tickets (Ticket internal) ←─ 本段所定義
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
- **Waitlist 補位**：候補升為 confirmed 時，先呼叫 POST 拿到新 ticketId，再 update transaction
- **No-Show 偵測**：每日排程或活動結束後手動觸發，呼叫此 endpoint 撈名單，再對應到 user_ids 餵給 Account Service 的 `POST /v1/internal/users/{user_id}/punish`