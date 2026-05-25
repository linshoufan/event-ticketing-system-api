# Ticket APIs — API Spec

這份文件描述票券管理相關 API。
目前包含員工查看自己的票券、查看單一票券詳情，以及活動期間報到。

---

## 認證

所有 ticket endpoint 均需要在 request header 中帶入：

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

- token 無效或過期 → `401 Unauthorized`
- 角色權限不足 → `403 Forbidden`

---

## Ticket Status

票券狀態由系統依目前時間、活動時間與 `checked_in_at` 動態計算，不直接儲存在 `tickets.status` 欄位。

| status | 說明 |
|--------|------|
| `invalid` | 非活動期間，包含活動尚未開始或已結束 |
| `unused` | 活動期間且票券尚未兌換，可報到 |
| `used` | 活動期間且票券已兌換，報到完成 |

---

## Endpoints

### GET `/v1/tickets`

取得目前登入員工自己的票券列表。

**Roles**

| role | 說明 |
|------|------|
| employee | 僅能查看自己的票券 |

**Query Parameters**

| 參數 | 型別 | 必填 | 說明 |
|------|------|------|------|
| status | string | 否 | `used` / `unused` / `invalid` |

**Response 200**

```json
{
  "data": [
    {
      "ticketId": "tk_001",
      "eventId": "ev_001",
      "eventName": "夏日烤肉趴",
      "eventStartTime": "2025-07-15T18:00:00Z",
      "eventLocation": "台北辦公室頂樓",
      "status": "unused",
      "checkinAvailable": true
    }
  ]
}
```

| 欄位 | 型別 | 說明 |
|------|------|------|
| ticketId | string | 票券 ID |
| eventId | string | 活動 ID |
| eventName | string | 活動名稱 |
| eventStartTime | string (ISO 8601) | 活動開始時間 |
| eventLocation | string | 活動地點 |
| status | string | `used` / `unused` / `invalid` |
| checkinAvailable | boolean | 是否可報到 |

**Error Responses**

| Status | code | 說明 |
|--------|------|------|
| 400 | `INVALID_STATUS` | status query 不是合法值 |
| 401 | `INVALID_TOKEN` | token 無效或過期 |
| 403 | `FORBIDDEN` | 非 employee 角色 |

---

### GET `/v1/tickets/{ticket_id}`

取得單一票券詳情，包含報到所需資訊與 QR payload。

**Roles**

| role | 說明 |
|------|------|
| employee | 僅能查看自己的票券 |
| welfare_member | 可查看任一票券 |

**Path Parameters**

| 參數 | 型別 | 說明 |
|------|------|------|
| ticket_id | string | 票券 ID |

**Response 200**

```json
{
  "data": {
    "ticketId": "tk_001",
    "userId": "u_abc123",
    "eventId": "ev_001",
    "eventName": "夏日烤肉趴",
    "eventStartTime": "2025-07-15T18:00:00Z",
    "eventEndTime": "2025-07-15T22:00:00Z",
    "eventLocation": "台北辦公室頂樓",
    "latitude": 25.0478,
    "longitude": 121.5319,
    "checkinRadiusMeters": 200,
    "status": "unused",
    "checkinAvailable": true,
    "qrPayload": "tk_001:ev_001:u_abc123:sig_xxxxxx"
  }
}
```

| 欄位 | 型別 | 說明 |
|------|------|------|
| ticketId | string | 票券 ID |
| userId | string | 票券持有人 ID |
| eventId | string | 活動 ID |
| eventName | string | 活動名稱 |
| eventStartTime | string (ISO 8601) | 活動開始時間 |
| eventEndTime | string (ISO 8601) | 活動結束時間 |
| eventLocation | string | 活動地點 |
| latitude | number | 活動地點緯度 |
| longitude | number | 活動地點經度 |
| checkinRadiusMeters | integer | 報到允許半徑，單位公尺 |
| status | string | `used` / `unused` / `invalid` |
| checkinAvailable | boolean | 是否可報到 |
| qrPayload | string | QR code payload |

**Error Responses**

| Status | code | 說明 |
|--------|------|------|
| 401 | `INVALID_TOKEN` | token 無效或過期 |
| 403 | `FORBIDDEN` | 權限不足 |
| 404 | `TICKET_NOT_FOUND` | 票券不存在 |

---

### POST `/v1/tickets/{ticket_id}/checkin`

報到。後端會驗證使用者是否為票券持有人、票券是否在活動期間、票券是否尚未使用，以及使用者 GPS 是否在活動地點半徑內。

**Roles**

| role | 說明 |
|------|------|
| employee | 僅能對自己的票券報到 |

**Path Parameters**

| 參數 | 型別 | 說明 |
|------|------|------|
| ticket_id | string | 票券 ID |

**Request Body**

```json
{
  "latitude": 25.0479,
  "longitude": 121.5320
}
```

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| latitude | number | 是 | 使用者目前緯度 |
| longitude | number | 是 | 使用者目前經度 |

**Response 200**

```json
{
  "data": {
    "checkedIn": true,
    "checkedInAt": "2025-07-15T18:05:00Z"
  }
}
```

**Error Responses**

| Status | code | 說明 |
|--------|------|------|
| 400 | `OUT_OF_RANGE` | 使用者不在活動地點半徑內 |
| 400 | `TICKET_INVALID` | 票券已使用或不可用 |
| 400 | `NOT_EVENT_TIME` | 現在不是活動時間 |
| 401 | `INVALID_TOKEN` | token 無效或過期 |
| 403 | `FORBIDDEN` | 不是票券持有人或非 employee |
| 404 | `TICKET_NOT_FOUND` | 票券不存在 |

---

## 使用場景

- **查看票券列表**：員工進入「我的票券」頁面，呼叫 `GET /v1/tickets` 取得自己的票券。
- **顯示票券 QR code**：員工打開單一票券頁面，呼叫 `GET /v1/tickets/{ticket_id}` 取得 QR payload 與活動地點資訊。
- **活動報到**：活動期間員工抵達活動地點，呼叫 `POST /v1/tickets/{ticket_id}/checkin` 完成報到。
