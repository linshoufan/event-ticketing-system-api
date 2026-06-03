# 自訂網域購買與接線指南（Custom Domain Setup）

> 對象：Group 14 ticketing system —— 前端在 **Vercel**（`*.vercel.app`）、後端四個服務在 **Cloud Run**（`*-api-...run.app`）。
> 目的：把醜醜的 `*.run.app` / `*.vercel.app` 換成自己的網域，順便讓 CORS 與架構圖更乾淨。
> 結論先講：**Demo / 報告其實「不一定要」買網域**；現有網址都能跑。買網域是「加分 + 美觀 + 架構分數」。下面說明要不要買、買什麼、怎麼接。

---

## 0. 先決定：你到底需不需要買？

| 你的目標 | 建議 |
|---|---|
| 只是把功能 Demo 出來 | **不用買**。`*.run.app` + `*.vercel.app` 都能用，CORS 也已設好。 |
| 想要報告「架構/可靠性」分數更漂亮（單一網域、一張憑證、host-based routing） | **建議買**，並走「Load Balancer」接法（見 §3 方案 B）。 |
| 想要前端網址好看一點就好 | 買最便宜的，走「Cloud Run domain mapping」接法（見 §3 方案 A）。 |
| 完全不想花錢、但想要好看的主機名（尤其走 GKE Ingress） | 用免費的 `nip.io` / `sslip.io`（把 IP 變成主機名），不用買。 |

---

## 1. 買什麼網域（TLD 與價格）

- **`.com`**：最通用，約 **US$10–11/年**。挑「首年=續約同價、不灌水」的註冊商最安全。
- **便宜玩具 TLD**（`.xyz` / `.site` / `.online` 等）：常有首年 < US$3 的促銷，**很適合短命的學生專案**。注意續約價會跳，但你大概用完就退掉。
- **`.app` / `.dev`**：在 HSTS preload 清單，**強制 HTTPS**——對你沒差（本來就全 HTTPS），但要知道。
- 建議：學生 Demo 用一個便宜 `.xyz`，或從 Cloudflare/Porkbun 買 `.com`（首年=續約同價）。

## 2. 去哪買（註冊商）

| 註冊商 | 特點 | 適合 |
|---|---|---|
| **Cloudflare Registrar** | **以成本價賣、零加價**，首年=續約同價（`.com` ≈ US$10.44），免費 WHOIS 隱私。需用 Cloudflare 當 DNS（沒差）。 | 想要長期可預測價格、最省心 |
| **Porkbun** | 便宜、UX 好、`.xyz`/`.dev` 常有促銷，首年=續約同價。 | 想撿便宜 TLD |
| **Namecheap** | 首年最便宜（`.com` ≈ US$6.49），但**續約會跳到 ~US$18**。 | 只用一年、用完就退 |
| **Cloud Domains（GCP 內）** | 直接在 GCP Console 管理、和 Cloud DNS 整合，但較貴、TLD 少。 | 想全部留在 GCP 裡 |

> ⚠️ 「Google Domains」已在 2023 年賣給 Squarespace、**消費端產品已不存在**；GCP 裡現在叫 **Cloud Domains**（是不同的東西）。別再找「Google Domains」。

## 3. 怎麼把網域接到後端 Cloud Run（兩種方案）

### 方案 A：Cloud Run Domain Mapping（最簡單，適合純 Demo）
每個服務各對應一個子網域：
```bash
gcloud beta run domain-mappings create \
  --service transaction-api \
  --domain  txn.api.yourdomain.com \
  --region  asia-east1
# account-api → account.api.yourdomain.com、event-api → event.api...、ticket-api → ticket.api... 同理
```
- 指令會印出要在註冊商 DNS 加的記錄（CNAME/A）；加完後 Google 會**自動簽發並續期受管 TLS 憑證**。
- **限制**：此功能是 *preview*（官方說不建議 production）、只能對應到 `/`（不能做路徑路由）、不能上傳自己的憑證。對 Demo 完全夠用。

### 方案 B：Global External Application Load Balancer + Serverless NEG（推薦，架構分數高）
在四個 Cloud Run 服務前面放一個**全域外部 HTTPS Load Balancer**：
- 一個網域 + 一個受管憑證，**host-based 或 path-based 路由**到四個服務（例：`account.yourdomain.com` / `event...` / `txn...` / `ticket...`）。
- 可外掛 **Cloud CDN**（邊緣快取）與 **Cloud Armor**（WAF/DDoS）。
- 給你**單一外部 IP + 單一憑證**，畫進系統架構圖很好看，也和 `deployment-gcp.md` 的 GKE Ingress 故事一致。
- 代價：設定步驟較多、LB forwarding rule 會有少許費用。
- 步驟參考官方文件（見文末連結）：建 serverless NEG → 建 backend service → URL map（host rules）→ target HTTPS proxy + 受管憑證 → global forwarding rule → 在 DNS 把網域 A record 指到 LB 的 IP。

## 4. 前端（Vercel）接網域

1. Vercel 專案 → **Settings → Domains** → 新增 `app.yourdomain.com`（或 apex `yourdomain.com`）。
2. Vercel 會給你一筆 DNS 記錄（CNAME 或 A）→ 到註冊商 DNS 加上去。
3. Vercel 會**自動簽發 TLS**，等幾分鐘生效。

## 5. 接好之後一定要做的收尾

1. **前端 `.env.production`**：四個 `VITE_*_API_URL` 改成新的後端網域（例 `https://txn.api.yourdomain.com/v1`）→ **重新部署前端**（Vercel 改 env 要重 build）。
2. **後端 CORS**：四個服務的 `CORS_ORIGINS`（env）或 `cors_origins` 預設值，加入新的**前端網域**（例 `https://app.yourdomain.com`）→ **重新部署四個服務**。
3. 用瀏覽器或 `curl -i -X OPTIONS -H "Origin: https://app.yourdomain.com" ...` 驗證 CORS header 有出現。

## 6. 注意事項（很重要）

- **時間**：DNS 傳播 + 憑證簽發要**幾分鐘到數小時**。**千萬不要 Demo 前一晚才弄**；提早幾天做。
- **保留退路**：接新網域時，舊的 `*.run.app` / `*.vercel.app` 先別關，當 fallback。
- **不要把任何密鑰 commit**；網域 DNS 設定不算密鑰，但 registrar 帳密要保管好。

## 7. 我的建議（懶人包）

- **要報告架構分數** → 方案 B（LB + 四個子網域），買 Cloudflare/Porkbun 的 `.com`。
- **只想快快 Demo 好看** → 方案 A（domain mapping，每服務一個子網域），買便宜 `.xyz`，約 30 分鐘 + 等傳播。
- **不想花錢** → 不買；`*.run.app`/`*.vercel.app` 照常用，或走 GKE 時用 `nip.io`。

---

## 參考連結
- Cloud Run — Mapping custom domains：<https://docs.cloud.google.com/run/docs/mapping-custom-domains>
- Global external Application Load Balancer with Cloud Run：<https://cloud.google.com/load-balancing/docs/https/setup-global-ext-https-serverless>
- 便宜註冊商比較（2026）：<https://domaindetails.com/registrars/cheapest>
