# Account Service — 資料庫 Schema 文件

## 總覽

Account Service 共有三張表：

| 表名 | 說明 |
|---|---|
| `users` | 使用者基本資料 |
| `user_interest_tags` | 使用者興趣標籤（一對多） |
| `user_preferences` | 使用者依活動類別的報名偏好（一對多） |

---

## `users`

使用者基本資料，每個使用者一筆。

| 欄位 | 型別 | Nullable | 預設值 | 可選值 | 說明 |
|---|---|---|---|---|---|
| user_id | VARCHAR(36) | NO | - | UUID | 主鍵 |
| username | VARCHAR(100) | NO | - | - | 顯示名稱，從第三方登入取得，唯一 |
| email | VARCHAR(255) | NO | - | - | 登入用，從第三方登入取得，唯一 |
| role | VARCHAR(20) | NO | `employee` | `employee` / `welfare_member` / `hr` | 使用者角色 |
| registration_status | VARCHAR(10) | NO | `active` | `active` / `locked` | 報名資格狀態 |
| unlock_at | TIMESTAMPTZ | YES | `null` | - | 鎖定解除時間，`locked` 時才有值 |
| diet_type | VARCHAR(10) | YES | `non-veg` | `veg` / `non-veg` | 全域飲食偏好預設值 |
| self_driving | BOOLEAN | YES | `null` | `true` / `false` | 全域自駕偏好預設值 |
| created_at | TIMESTAMPTZ | NO | NOW() | - | 建立時間 |
| updated_at | TIMESTAMPTZ | NO | NOW() | - | 更新時間 |

**範例資料：**
```json
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "andy.hsu",
  "email": "andy@company.com",
  "role": "employee",
  "registration_status": "active",
  "unlock_at": null,
  "diet_type": "non-veg",
  "self_driving": true,
  "created_at": "2026-05-20T10:00:00Z",
  "updated_at": "2026-05-20T10:00:00Z"
}
```

---

## `user_interest_tags`

使用者的興趣標籤，一個使用者可以有多個標籤。

| 欄位 | 型別 | Nullable | 預設值 | 可選值 | 說明 |
|---|---|---|---|---|---|
| id | SERIAL | NO | 自動遞增 | - | 主鍵 |
| user_id | VARCHAR(36) | NO | - | 對應 users.user_id | 外鍵，user 刪除時一起刪 |
| tag | VARCHAR(50) | NO | - | 見下方 | 興趣標籤 |

**tag 可選值：**

| 值 | 說明 |
|---|---|
| `sport` | 運動 |
| `food` | 美食 |
| `travel` | 旅遊 |
| `culture` | 文藝 / 展覽 |
| `family` | 親子 / 家庭 |
| `contest` | 競賽 |
| `music` | 音樂 |

> tag 可選值與活動的 `category` 一致，供活動推薦使用。

**限制：** 同一個 user 不能有重複的 tag（`UNIQUE(user_id, tag)`）

**範例資料：**
```json
[
  { "id": 1, "user_id": "a1b2c3d4-...", "tag": "sport" },
  { "id": 2, "user_id": "a1b2c3d4-...", "tag": "food" }
]
```

---

## `user_preferences`

使用者依活動類別設定的報名偏好，用於報名時自動填入。

| 欄位 | 型別 | Nullable | 預設值 | 可選值 | 說明 |
|---|---|---|---|---|---|
| id | SERIAL | NO | 自動遞增 | - | 主鍵 |
| user_id | VARCHAR(36) | NO | - | 對應 users.user_id | 外鍵，user 刪除時一起刪 |
| category | VARCHAR(50) | NO | - | 與 tag 相同 | 活動類別 |
| diet_type | VARCHAR(10) | YES | `null` | `veg` / `non-veg` | 此類別的飲食偏好 |
| self_driving | BOOLEAN | YES | `null` | `true` / `false` | 此類別的自駕偏好 |
| guest_count | INTEGER | YES | `null` | 0 以上整數 | 此類別的攜伴人數 |
| updated_at | TIMESTAMPTZ | NO | NOW() | - | 更新時間 |

**限制：** 同一個 user 同一個 category 只能有一筆（`UNIQUE(user_id, category)`）

**範例資料：**
```json
[
  {
    "id": 1,
    "user_id": "a1b2c3d4-...",
    "category": "sport",
    "diet_type": "non-veg",
    "self_driving": true,
    "guest_count": 0,
    "updated_at": "2026-05-20T10:00:00Z"
  }
]
```

---

## 關聯圖

```
users (1)
  ├── user_interest_tags (N)
  └── user_preferences (N)
```

---

## Autofill 邏輯

使用者報名活動時，系統依序查詢填入預設值：

1. 查 `user_preferences`，有沒有對應 `category` 的設定 → 有就用
2. 沒有對應 `category` → fallback 到 `users` 的 `diet_type` / `self_driving`
