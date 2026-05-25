# Backend — Internal API Spec

這份文件給 backend 內部或其他模組使用。
所有 internal endpoint 都需要帶 `X-Internal-Key` header，key 值透過 `.env` 中的 `INTERNAL_API_KEY` 設定。

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
