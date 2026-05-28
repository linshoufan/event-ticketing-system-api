# Transaction Service（報名管理）

Corporate Event Ticketing System 的報名管理微服務。負責處理活動報名、取消、候補
（waitlist）、自動補位，以及爽約（No-Show）處罰。

技術棧：Python 3.12 + FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL。

---

## 在系統中的角色

```
[前端] ──JWT──> Transaction Service ──┬── Account Service (internal)  取使用者資格 / 處罰
                                      ├── Event Service   (public)    取活動詳情
                                      └── Ticket Service  (internal)  配發 / 作廢票券
```

- 報名紀錄的真實來源（誰報名、誰候補、誰取消）
- 名額容量的真實來源（用 advisory lock + DB 內計數，避免超賣）
- Ticket / Account / Event 的資料則向各自的服務查詢

---

## API 一覽

| Method | Path | 角色 | 說明 |
|--------|------|------|------|
| GET | `/v1/events/{eventId}/eligibility` | employee | 報名資格檢查 |
| GET | `/v1/transactions` | employee | 查自己的報名（分頁） |
| GET | `/v1/transactions/{id}` | employee / welfare_member | 查單筆 |
| POST | `/v1/transactions` | employee | 報名 |
| PATCH | `/v1/transactions/{id}` | employee | 修改報名細節 |
| DELETE | `/v1/transactions/{id}` | employee | 取消（自動補位候補） |
| GET | `/v1/events/{eventId}/registrations` | welfare_member / hr | 後台查報名 |
| POST | `/v1/internal/events/{eventId}/punish-no-shows` | internal key | 觸發 No-Show 處罰 |

詳細 request/response 格式見 `docs/api-spec.txt`；跨服務 internal API 契約見
`docs/internal-api-spec.md`。

---

## 本地開發

### 1. 啟動資料庫

於 repo 根目錄：

```bash
docker compose up -d transaction-db
```

### 2. 設定環境變數

複製 `.env.example` 為 `.env` 並填好。重點：
- `JWT_SECRET_KEY` / `INTERNAL_API_KEY` 必須與 Account Service 一致
- `TICKET_SERVICE_ENABLED` 在 Ticket Service 整合前保持 `false`（走 mock）

### 3. 安裝套件 + 建表

```bash
cd services/transaction
pip install -r ../../requirements.txt
export $(cat ../../.env | grep -v '^#' | xargs)
alembic upgrade head
```

### 4. 啟動服務

```bash
uvicorn app.main:app --reload --port 8002
```

開 `http://localhost:8002/docs` 看 Swagger UI。

---

## 測試

測試完全不依賴 Account / Event / Ticket Service（用 fake client 注入），但需要一個
真實的 PostgreSQL（因為使用了 advisory lock 與 partial unique index）。

```bash
cd services/transaction
export $(cat ../../.env | grep -v '^#' | xargs)
python -m pytest                         # 跑全部
python -m pytest --cov=app               # 含覆蓋率
python -m pytest tests/test_concurrency.py -v   # 只跑併發測試
```

目前覆蓋率約 87%（標準 ≥ 80%）。

### 本地手動測試（不跑 OAuth）

Account Service 正式 token 走 Google OAuth；本地測試可用 `scripts/make_token.py`
自簽一個合法 token（secret 需與 Account 一致）：

```bash
TOKEN=$(python scripts/make_token.py <真實的user_id> employee)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8002/v1/events/<eventId>/eligibility
```

注意：`user_id` 與 `eventId` 必須在 Account / Event 的 DB 真實存在，且這兩個服務要
同時在跑，eligibility / 報名才打得通。

---

## 設計要點

- **併發控制**：報名 / 取消時對 `event_id` 取 `pg_advisory_xact_lock`，序列化同一活動
  的名額決策，不同活動互不阻塞，避免超賣。
- **候補補位**：取消 confirmed 時，自動把 `waitlist_number` 最小的候補升為 confirmed，
  並配發新票券。
- **取消規則**：`cancellation_deadline = NULL` 代表「不可取消」；waitlist 一律可取消。
- **票券一致性**：對 Ticket Service 的呼叫放在 DB commit 之後，接受極小機率的最終一致
  性落差（可由日後的 reconciliation job 補正）。
- **No-Show 處罰**：活動結束後，比對 Ticket Service 的未核銷票券，對應的 user 呼叫
  Account Service 停權 30 天。

---

## 已知待協調項目

1. 後台 registrations 的 `username` 目前為 `null`，待 Account Service 在
   `registration-profile` 補上 username 或提供 username 查詢 endpoint。
2. POST 報名的 `saveAutofill` 目前僅記 log，待 Account Service 提供「更新使用者
   autofill 預設值」的 internal endpoint 後接上。
