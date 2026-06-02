# Mock/Test Data Inventory

這份文件彙整目前 backend 各服務用到的假資料來源，作為後續整理共用整合測試資料的基準。

## Canonical Shared Data

目前最接近共用測資入口的是 `scripts/mock_data.yaml`，並由 `scripts/seed_all.py` 寫入四個服務資料庫。預設 seed 只會 upsert YAML 內的固定資料，不清空既有資料；若要重建乾淨環境，需明確加上 `--reset`。

### Users

在目前的系統架構中，**`user_id` 等同於 `employee_id` / `username`**。這確保了跨服務識別的一致性。

| user_id | email | role | 用途 |
| --- | --- | --- | --- |
| `1000001` | `andy@company.com` | `employee` | Account login、Ticket 主要測試使用者 |
| `1000002` | `sarah@company.com` | `welfare_member` | Account login、福委會角色 |
| `1000003` | `role@company.com` | `employee` | Account wrong-role 測試 |
| `1000099` | `unique@company.com` | `employee` | Account duplicate-login 測試 |
| `user_005` | `user_005@company.com` | `employee` | Transaction waitlist/no-show 測試 |
| `user_006` | `user_006@company.com` | `employee` | Transaction 主要使用者，預設 veg/self-driving |
| `user_007` | `user_007@company.com` | `employee` | Transaction waitlist/forbidden 測試 |
| `welfare_001` | `welfare_001@company.com` | `welfare_member` | Transaction eligibility 角色測試 |
| `hr_001` | `hr_001@company.com` | `hr` | Transaction backstage 角色測試 |
| `locked_001` | `locked_001@company.com` | `employee` | locked 帳號情境 |

### Events

| event_id | name | category | status | 時間設定 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `event_001` | 夏日烤肉趴 | `outdoor` | `1` | 已開始、4 小時活動 | 可 check-in、未使用票券 |
| `event_002` | 部門聚餐 | `food` | `4` | 已結束 | 已使用票券、歷史活動 |
| `event_003` | 週五電影之夜 | `culture` | `1` | 48 小時後開始 | 已報名但尚未發票 |
| `event_004` | 員工家庭日 | `family` | `1` | 168 小時後開始 | 可取消期限較長 |
| `event_005` | Event event_005 | `test` | `1` | 10 天後開始 | Transaction 一般報名 |
| `event_011` | 跨年烤肉 | `娛樂` | `1` | 固定 2026-12-31 | 明確時間字串測試 |

### Transactions

| transaction_id | user_id | event_id | status | ticket_id | 用途 |
| --- | --- | --- | --- | --- | --- |
| `tx_001` | `1000001` | `event_001` | `confirmed` | `ticket_001` | confirmed + unused ticket |
| `tx_002` | `1000001` | `event_002` | `confirmed` | `ticket_002` | confirmed + used ticket |
| `tx_003` | `1000001` | `event_003` | `confirmed` | `null` | confirmed 但尚無 ticket |
| `tx_004` | `1000001` | `event_004" | `confirmed` | `ticket_003` | confirmed + future cancellable event |

### Tickets

| ticket_id | user_id | event_id | transaction_id | status | 用途 |
| --- | --- | --- | --- | --- | --- |
| `ticket_001` | `1000001` | `event_001` | `tx_001` | `unused` | no-show/check-in 測試 |
| `ticket_002` | `1000001` | `event_002` | `tx_002` | `used` | 已 check-in 歷史票 |
| `ticket_003` | `1000001` | `event_004` | `tx_004` | `unused` | 未來活動票券 |

## Service-Specific Test Data

### Account Service

來源：
- `backend/account/app/core/external_db.py`
- `backend/account/tests/`

### Event Service

來源：
- `backend/event/src/test/api.test.ts`

### Transaction Service

來源：
- `backend/transaction/tests/`

特殊情境：
- `event_005`：滿額後進 waitlist 測試。

### Ticket Service

來源：
- `backend/ticket/tests/unit/`
- `backend/ticket/tests/integration/`

## Test Fixture Pattern

服務測試使用 `scripts/mock_data.yaml` 作為來源，確保測試環境與開發環境資料同步。
- CI 執行時會起測試 DB 並跑完 Migrations 後再執行測試。
- 每個測試案例應自主 Arrange 所需資料，不依賴前案遺留狀態。

## API Request Samples

### Event Service

#### Create Event (POST /v1/events)
```json
{
  "name": "2026 仲夏星空電影節",
  "description": "在公司頂樓花園享受露天電影與精緻餐點，放鬆您的心情。",
  "location": "台北辦公室頂樓花園",
  "category": "entertainment",
  "guestAllowed": true,
  "ticketLimit": 100,
  "remainingTickets": 100,
  "cancellationDeadline": "2026-07-10T23:59:59Z",
  "latitude": 25.0478,
  "longitude": 121.5319,
  "checkinRadiusMeters": 150,
  "eventStartTime": "2026-07-15T19:00:00Z",
  "eventEndTime": "2026-07-15T22:00:00Z",
  "registrationStart": "2026-06-01T09:00:00Z",
  "registrationEnd": "2026-07-01T18:00:00Z",
  "status": "registering",
  "isDraft": false,
  "faqs": [
    {
      "question": "需要自備椅子嗎？",
      "answer": "主辦單位會提供舒適的懶人沙發與靠墊。"
    },
    {
      "question": "現場有提供食物嗎？",
      "answer": "現場將提供爆米花、吉拿棒與各式軟性飲料。"
    }
  ]
}
```

