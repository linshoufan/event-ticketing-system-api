# GCP 部署指南（GKE Autopilot + Cloud SQL）

> 對象：Group 14 Corporate Event Ticketing System（4 個 FastAPI 微服務 + 前端）。
> 環境：GCP Free Trial（US$300 / 90 天）。本指南所有指令以 **`asia-east1`（台灣）** 為例。
> 這份是「雲端正式部署」說明；本機開發請看 `docs/deployment.md`。
>
> 架構對齊 HW2 架構圖：GKE（每服務 1~2 Pod）+ Cloud SQL(PostgreSQL) + GKE Ingress(Load Balancer)。
> Pub/Sub / Redis 在目前程式碼尚未使用（通知功能未實作），本指南不部署它們。

---

## 0. 部署拓樸總覽

```
                         ┌──────────── GKE Ingress (1 個外部 IP) ────────────┐
                         │  host-based routing (用 nip.io 免買網域)           │
  使用者 / 前端  ───────▶ │  account.<IP>.nip.io  → account-service          │
                         │  event.<IP>.nip.io    → event-service            │
                         │  txn.<IP>.nip.io      → transaction-service      │
                         │  ticket.<IP>.nip.io   → ticket-service           │
                         └───────────────────────────┬──────────────────────┘
                                                      │ (ClusterIP, K8s DNS)
        ┌──────────────┬───────────────┬─────────────┴───────────┐
        ▼              ▼               ▼                         ▼
  account-pod    event-pod       transaction-pod           ticket-pod
  (app+proxy)    (app+proxy)     (app+proxy)               (app+proxy)
        └──────────────┴───────────────┴─────────────────────────┘
                                  │ Cloud SQL Auth Proxy (sidecar, unix socket)
                                  ▼
                    Cloud SQL (PostgreSQL 15, 1 instance)
                    databases: account_db / event_db / transaction_db / ticket_db
```

**為什麼用 host-based（不同子網域）而不是 path-based？**
四個服務的路徑會重疊：`/v1/events/{id}`（event）、`/v1/events/{id}/eligibility`（transaction）、`/v1/events/{id}/tickets`（ticket）共用 `/v1/events/...` 前綴，單純用 path prefix 無法乾淨切分。用「每服務一個子網域」最單純也最不會出錯，前端只要設定四個 base URL 即可。

---

## 1. 前置工具與專案

```bash
# 安裝 gcloud（若未裝）：https://cloud.google.com/sdk/docs/install
gcloud version                      # 確認有 gcloud
gcloud components install gke-gcloud-auth-plugin kubectl   # GKE 需要

# 登入 + 設定專案（用 Free Trial 啟用的專案）
gcloud auth login
gcloud config set project <YOUR_PROJECT_ID>
gcloud config set compute/region asia-east1

# 啟用需要的 API（第一次會跑一兩分鐘）
gcloud services enable \
  container.googleapis.com \
  sqladmin.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

把這幾個值記下來，後面整份指南會一直用到（請替換成你自己的）：

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION=asia-east1
export AR_REPO=ticketing                       # Artifact Registry repo 名稱
export SQL_INSTANCE=ticketing-sql              # Cloud SQL 實例名稱
export CLUSTER=ticketing-cluster               # GKE 叢集名稱
export IMAGE_TAG=v1
```

---

## 2. 程式碼前置修正（部署前一定要先做）

### 2.1 修 Event 的 DB 連線（讓它支援 Cloud SQL）

`backend/event/app/core/database.py` 目前**只寫死 TCP 連線、沒有 production 分支**，會無法連 Cloud SQL（account / ticket / transaction 都已支援）。把第 5–10 行：

```python
DATABASE_URL = (
    f"postgresql://{settings.event_db_user}:{settings.event_db_password}"
    f"@{settings.event_db_host}:{settings.event_db_port}/{settings.event_db_name}"
)

engine = create_engine(DATABASE_URL)
```

換成（與 account / ticket 一致：production 走 Cloud SQL Unix socket，本機走 TCP）：

```python
def build_database_url() -> str:
    """production 走 Cloud SQL Unix socket（host=/cloudsql/PROJECT:REGION:INSTANCE），本機走 TCP。"""
    if settings.env == "production":
        return (
            f"postgresql+psycopg2://{settings.event_db_user}:{settings.event_db_password}"
            f"@/{settings.event_db_name}?host={settings.event_db_host}"
        )
    return (
        f"postgresql+psycopg2://{settings.event_db_user}:{settings.event_db_password}"
        f"@{settings.event_db_host}:{settings.event_db_port}/{settings.event_db_name}"
    )

DATABASE_URL = build_database_url()
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
```

> 其餘（`SessionLocal` / `Base` / `get_db`）不動。這是 event 組員的檔案，請一起協調進版。

### 2.2 新增 `Dockerfile`（放在 repo 根目錄）

四個服務共用一份 Dockerfile，用 build-arg 指定要跑哪個服務。**build context 必須是 repo 根目錄**，因為服務會讀根目錄的 `requirements.txt` 與 `scripts/mock_data.yaml`。

```dockerfile
# Dockerfile（repo 根目錄）
FROM python:3.11-slim

# psycopg2-binary 不需編譯，但保留基本工具
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 要跑哪個服務：account / event / transaction / ticket
ARG SERVICE_DIR
ENV SERVICE_DIR=${SERVICE_DIR}

WORKDIR /app/backend/${SERVICE_DIR}
EXPOSE 8080

# 四個服務都有 app/main.py（app 物件），統一用 app.main:app
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8080"]
```

### 2.3 新增 `.dockerignore`（放 repo 根目錄，加速 build、避免把垃圾塞進 image）

```
**/__pycache__/
**/*.pyc
**/.pytest_cache/
**/.ruff_cache/
.git/
.venv/
venv/
*.png
*.pdf
htmlcov/
.env
```

### 2.4 新增 `cloudbuild.yaml`（一次 build 出四個 image）

> 用 Cloud Build 而不是本機 `docker build`，因為你的 MacBook Air 是 ARM，本機 build 出來的 image 在 GKE（amd64 節點）跑不起來。Cloud Build 直接幫你 build amd64。

```yaml
# cloudbuild.yaml（repo 根目錄）
steps:
  - name: gcr.io/cloud-builders/docker
    args: ['build','--build-arg','SERVICE_DIR=account',
           '-t','${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/account:${_TAG}','.']
  - name: gcr.io/cloud-builders/docker
    args: ['build','--build-arg','SERVICE_DIR=event',
           '-t','${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/event:${_TAG}','.']
  - name: gcr.io/cloud-builders/docker
    args: ['build','--build-arg','SERVICE_DIR=transaction',
           '-t','${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/transaction:${_TAG}','.']
  - name: gcr.io/cloud-builders/docker
    args: ['build','--build-arg','SERVICE_DIR=ticket',
           '-t','${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/ticket:${_TAG}','.']
images:
  - '${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/account:${_TAG}'
  - '${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/event:${_TAG}'
  - '${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/transaction:${_TAG}'
  - '${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPO}/ticket:${_TAG}'
substitutions:
  _REGION: asia-east1
  _REPO: ticketing
  _TAG: v1
options:
  machineType: E2_HIGHCPU_8
```

---

## 3. 建立 Cloud SQL（PostgreSQL）

```bash
# 建立實例（demo 用最便宜的 db-f1-micro；要對齊架構圖可改 --tier=db-custom-1-3840）
gcloud sql instances create $SQL_INSTANCE \
  --database-version=POSTGRES_15 \
  --edition=enterprise \
  --tier=db-f1-micro \
  --region=$REGION \
  --storage-size=10GB \
  --storage-type=SSD

# 設定 postgres 使用者密碼（請改成你自己的強密碼）
gcloud sql users set-password postgres \
  --instance=$SQL_INSTANCE \
  --password='ChangeMe-StrongPassword-123'

# 在同一個實例建立四個資料庫
for DB in account_db event_db transaction_db ticket_db; do
  gcloud sql databases create $DB --instance=$SQL_INSTANCE
done

# 取得「連線名稱」(格式 PROJECT:REGION:INSTANCE)，後面 proxy / DB_HOST 會用到
export SQL_CONN=$(gcloud sql instances describe $SQL_INSTANCE --format='value(connectionName)')
echo "Cloud SQL connection name = $SQL_CONN"
```

---

## 4. 建 Artifact Registry 並 build / push image

```bash
# 建 Docker repo
gcloud artifacts repositories create $AR_REPO \
  --repository-format=docker \
  --location=$REGION

# 用 Cloud Build 一次 build 四個（在 repo 根目錄執行）
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_REGION=$REGION,_REPO=$AR_REPO,_TAG=$IMAGE_TAG

# 確認四個 image 都在
gcloud artifacts docker images list $REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO
```

---

## 5. 建 GKE Autopilot 叢集

```bash
gcloud container clusters create-auto $CLUSTER --region=$REGION

# 取得 kubectl 連線憑證
gcloud container clusters get-credentials $CLUSTER --region=$REGION
kubectl get nodes        # 確認連得上（Autopilot 可能顯示 0 nodes，正常，會按需配置）
```

### 5.1 設定 Workload Identity（讓 Pod 能連 Cloud SQL）

```bash
# 1) 建一個 GCP service account 給 Cloud SQL Proxy 用
gcloud iam service-accounts create ticketing-sql \
  --display-name="Ticketing Cloud SQL access"

# 2) 給它 Cloud SQL Client 權限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:ticketing-sql@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# 3) 建 K8s service account
kubectl create serviceaccount ticketing-ksa

# 4) 綁定 KSA ↔ GSA（Workload Identity）
gcloud iam service-accounts add-iam-policy-binding \
  ticketing-sql@$PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:$PROJECT_ID.svc.id.goog[default/ticketing-ksa]"

# 5) 在 KSA 上加註解
kubectl annotate serviceaccount ticketing-ksa \
  iam.gke.io/gcp-service-account=ticketing-sql@$PROJECT_ID.iam.gserviceaccount.com
```

---

## 6. 建 K8s Secret 與 ConfigMap

```bash
# 機密：DB 密碼、JWT、internal key（四個服務共用同一把 JWT 與 internal key）
kubectl create secret generic app-secrets \
  --from-literal=DB_PASSWORD='ChangeMe-StrongPassword-123' \
  --from-literal=JWT_SECRET_KEY='please-generate-a-long-random-string' \
  --from-literal=INTERNAL_API_KEY='please-generate-another-random-string'

# 非機密設定：Cloud SQL 連線名稱（給所有服務當 DB_HOST 與 proxy 參數）
kubectl create configmap app-config \
  --from-literal=SQL_CONN="$SQL_CONN"
```

> JWT_SECRET_KEY 四服務必須一致（互相驗 token）；INTERNAL_API_KEY 四服務也必須一致（跨服務 X-Internal-Key）。

---

## 7. 先跑 Migration + Seed（一次性 Job）

四個服務各有 alembic migration，加上 `scripts/seed_all.py` 灌入 mock 資料。用一個 K8s Job 跑（任一 image 都含整包 repo；這裡用 account image），DB 連線一樣透過 Cloud SQL Proxy sidecar。

把下面存成 `k8s/migrate-job.yaml`（記得先把 `PROJECT_ID` / `REGION` / `SQL_CONN` 換成實際值，或用 `envsubst`，見第 9 節）：

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate-seed
spec:
  backoffLimit: 2
  template:
    spec:
      serviceAccountName: ticketing-ksa
      restartPolicy: Never
      containers:
        - name: migrate
          image: REGION-docker.pkg.dev/PROJECT_ID/ticketing/account:v1
          workingDir: /app
          command: ["sh","-c"]
          args:
            - |
              echo "Waiting for Cloud SQL proxy socket..."
              until [ -S /cloudsql/$SQL_CONN/.s.PGSQL.5432 ]; do sleep 2; done
              echo "Running migrations..."
              cd backend/account     && alembic upgrade head &&
              cd ../event            && alembic upgrade head &&
              cd ../transaction      && alembic upgrade head &&
              cd ../ticket           && alembic upgrade head &&
              cd ../.. && echo "Seeding..." && python scripts/seed_all.py
          env:
            - name: ENV
              value: "production"
            - name: SQL_CONN
              valueFrom: { configMapKeyRef: { name: app-config, key: SQL_CONN } }
            # 四個 DB 都在同一個實例，host 都是 /cloudsql/<conn>，只有 db name 不同
            - { name: ACCOUNT_DB_HOST,     value: "/cloudsql/$(SQL_CONN)" }
            - { name: ACCOUNT_DB_NAME,     value: "account_db" }
            - { name: ACCOUNT_DB_USER,     value: "postgres" }
            - { name: ACCOUNT_DB_PASSWORD, valueFrom: { secretKeyRef: { name: app-secrets, key: DB_PASSWORD } } }
            - { name: EVENT_DB_HOST,       value: "/cloudsql/$(SQL_CONN)" }
            - { name: EVENT_DB_NAME,       value: "event_db" }
            - { name: EVENT_DB_USER,       value: "postgres" }
            - { name: EVENT_DB_PASSWORD,   valueFrom: { secretKeyRef: { name: app-secrets, key: DB_PASSWORD } } }
            - { name: TRANSACTION_DB_HOST,     value: "/cloudsql/$(SQL_CONN)" }
            - { name: TRANSACTION_DB_NAME,     value: "transaction_db" }
            - { name: TRANSACTION_DB_USER,     value: "postgres" }
            - { name: TRANSACTION_DB_PASSWORD, valueFrom: { secretKeyRef: { name: app-secrets, key: DB_PASSWORD } } }
            - { name: TICKET_DB_HOST,      value: "/cloudsql/$(SQL_CONN)" }
            - { name: TICKET_DB_NAME,      value: "ticket_db" }
            - { name: TICKET_DB_USER,      value: "postgres" }
            - { name: TICKET_DB_PASSWORD,  valueFrom: { secretKeyRef: { name: app-secrets, key: DB_PASSWORD } } }
          volumeMounts:
            - { name: cloudsql, mountPath: /cloudsql }
        # Cloud SQL Proxy sidecar（unix socket 模式）
        - name: cloud-sql-proxy
          image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.11.0
          args:
            - "--unix-socket=/cloudsql"
            - "$(SQL_CONN)"
          env:
            - name: SQL_CONN
              valueFrom: { configMapKeyRef: { name: app-config, key: SQL_CONN } }
          securityContext: { runAsNonRoot: true }
          volumeMounts:
            - { name: cloudsql, mountPath: /cloudsql }
      volumes:
        - name: cloudsql
          emptyDir: {}
```

> Job 在 sidecar 模式下，app 容器跑完 proxy 不會自己結束。對 demo 而言可接受（Job 會卡在 Running）。若要乾淨退出，把 proxy 改用 `--exit-zero-on-sigterm` 並在 app 跑完後送訊號；為簡潔本指南略過，跑完看 log 出現 `Seeding...` 完成即可手動 `kubectl delete job db-migrate-seed`。

---

## 8. 部署四個服務（Deployment + Service）

每個 Deployment = 「app 容器 + Cloud SQL Proxy sidecar」，並用 `ticketing-ksa`。以下用 `transaction` 當完整範例，其餘三個只是換 image / DB 名 / 服務 URL。

把下面存成 `k8s/transaction.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: transaction-service
spec:
  replicas: 1
  selector: { matchLabels: { app: transaction-service } }
  template:
    metadata:
      labels: { app: transaction-service }
    spec:
      serviceAccountName: ticketing-ksa
      containers:
        - name: app
          image: REGION-docker.pkg.dev/PROJECT_ID/ticketing/transaction:v1
          ports: [{ containerPort: 8080 }]
          env:
            - { name: ENV, value: "production" }
            - name: SQL_CONN
              valueFrom: { configMapKeyRef: { name: app-config, key: SQL_CONN } }
            - { name: TRANSACTION_DB_HOST,     value: "/cloudsql/$(SQL_CONN)" }
            - { name: TRANSACTION_DB_NAME,     value: "transaction_db" }
            - { name: TRANSACTION_DB_USER,     value: "postgres" }
            - { name: TRANSACTION_DB_PASSWORD, valueFrom: { secretKeyRef: { name: app-secrets, key: DB_PASSWORD } } }
            - { name: JWT_SECRET_KEY,   valueFrom: { secretKeyRef: { name: app-secrets, key: JWT_SECRET_KEY } } }
            - { name: JWT_ALGORITHM,    value: "HS256" }
            - { name: INTERNAL_API_KEY, valueFrom: { secretKeyRef: { name: app-secrets, key: INTERNAL_API_KEY } } }
            # 跨服務呼叫（K8s 內部 DNS，ClusterIP 預設 80 port）
            - { name: ACCOUNT_SERVICE_URL, value: "http://account-service" }
            - { name: EVENT_SERVICE_URL,   value: "http://event-service" }
            - { name: TICKET_SERVICE_URL,  value: "http://ticket-service" }
          readinessProbe:
            httpGet: { path: /, port: 8080 }
            initialDelaySeconds: 10
            periodSeconds: 10
        - name: cloud-sql-proxy
          image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.11.0
          args: ["--unix-socket=/cloudsql", "$(SQL_CONN)"]
          env:
            - name: SQL_CONN
              valueFrom: { configMapKeyRef: { name: app-config, key: SQL_CONN } }
          securityContext: { runAsNonRoot: true }
          volumeMounts: [{ name: cloudsql, mountPath: /cloudsql }]
      volumes:
        - name: cloudsql
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: transaction-service
spec:
  selector: { app: transaction-service }
  ports: [{ port: 80, targetPort: 8080 }]
```

**其餘三個服務**照抄上面，改這些地方：

| 服務 | Deployment/Service 名 | image | DB env 前綴 / DB name | 跨服務 URL env |
|------|----------------------|-------|----------------------|----------------|
| account | `account-service` | `.../account:v1` | `ACCOUNT_DB_*` / `account_db` | 不需要（account 不主動呼叫別人） |
| event | `event-service` | `.../event:v1` | `EVENT_DB_*` / `event_db` | 不需要 |
| ticket | `ticket-service` | `.../ticket:v1` | `TICKET_DB_*` / `ticket_db` | `ACCOUNT_SERVICE_URL`, `EVENT_SERVICE_URL`（ticket 內部會呼叫 account/event） |
| transaction | `transaction-service` | `.../transaction:v1` | `TRANSACTION_DB_*` / `transaction_db` | `ACCOUNT_SERVICE_URL`, `EVENT_SERVICE_URL`, `TICKET_SERVICE_URL` |

> account / event / ticket / transaction 全部都要帶 `JWT_SECRET_KEY`、`INTERNAL_API_KEY`（驗 token / 跨服務）。account 與 event 也都要 `ENV=production` 與自己的 DB env + proxy sidecar。

---

## 9. Ingress（單一外部 IP + 子網域路由）

```bash
# 先保留一個全域靜態 IP（Ingress 用）
gcloud compute addresses create ticketing-ip --global
export INGRESS_IP=$(gcloud compute addresses describe ticketing-ip --global --format='value(address)')
echo "Ingress IP = $INGRESS_IP"   # 用這個 IP 配 nip.io，免買網域
```

`k8s/ingress.yaml`（把 `<IP>` 換成 `$INGRESS_IP`）：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ticketing-ingress
  annotations:
    kubernetes.io/ingress.global-static-ip-name: "ticketing-ip"
spec:
  rules:
    - host: account.<IP>.nip.io
      http: { paths: [{ path: /, pathType: Prefix, backend: { service: { name: account-service, port: { number: 80 } } } }] }
    - host: event.<IP>.nip.io
      http: { paths: [{ path: /, pathType: Prefix, backend: { service: { name: event-service, port: { number: 80 } } } }] }
    - host: txn.<IP>.nip.io
      http: { paths: [{ path: /, pathType: Prefix, backend: { service: { name: transaction-service, port: { number: 80 } } } }] }
    - host: ticket.<IP>.nip.io
      http: { paths: [{ path: /, pathType: Prefix, backend: { service: { name: ticket-service, port: { number: 80 } } } }] }
```

### 套用所有 manifest

因為 YAML 裡有 `REGION` / `PROJECT_ID` / `<IP>` 佔位，最簡單的方法是用 `sed` 或 `envsubst` 取代後再 apply：

```bash
# 範例：用 sed 取代後 apply（每個檔都做）
sed -e "s/REGION/$REGION/g" -e "s/PROJECT_ID/$PROJECT_ID/g" k8s/transaction.yaml | kubectl apply -f -
# account / event / ticket / migrate-job 同理
sed "s/<IP>/$INGRESS_IP/g" k8s/ingress.yaml | kubectl apply -f -

# 先跑 migration job（等它完成）
kubectl logs -f job/db-migrate-seed -c migrate
```

---

## 10. 驗證

```bash
kubectl get pods                       # 每個 pod 應為 2/2 Running（app + proxy）
kubectl get ingress ticketing-ingress  # 等 ADDRESS 出現（GKE Ingress 佈署需 3~5 分鐘）

# 健康檢查（換成你的 IP）
curl http://account.$INGRESS_IP.nip.io/
curl http://event.$INGRESS_IP.nip.io/
curl http://txn.$INGRESS_IP.nip.io/
curl http://ticket.$INGRESS_IP.nip.io/

# 登入拿 token（mock employee 在 scripts/mock_data.yaml）
curl -X POST http://account.$INGRESS_IP.nip.io/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"employeeId":"<某個 mock employeeId>","password":"<密碼>","role":null}'

# 用 token 打報名資格（驗證 transaction → event 跨服務 internal key 有通）
curl http://txn.$INGRESS_IP.nip.io/v1/events/<eventId>/eligibility \
  -H "Authorization: Bearer <token>"
```

> 跨服務驗證重點：`eligibility` / 報名會讓 transaction 去呼叫 event 的 `/v1/internal/events/{id}`（帶 X-Internal-Key）。若回 500 且 log 顯示 EventService 401，代表 `INTERNAL_API_KEY` 兩邊不一致或 event 的 internal endpoint 沒部署。

---

## 11. 前端部署（另一個 repo）

前端是獨立 repo（`event-ticketing-system-frontend`）。最省事的雲端做法二選一：

- **Cloud Run（容器化 nginx）**：`docker build` 前端 → push Artifact Registry → `gcloud run deploy frontend --image ... --allow-unauthenticated --region $REGION`。
- **Firebase Hosting / Cloud Storage 靜態托管**：`npm run build` 後把 `dist/` 上傳。

不論哪種，前端的 API base URL 要設成上面四個子網域：

```
VITE_ACCOUNT_API=http://account.<IP>.nip.io
VITE_EVENT_API=http://event.<IP>.nip.io
VITE_TRANSACTION_API=http://txn.<IP>.nip.io
VITE_TICKET_API=http://ticket.<IP>.nip.io
```

> 注意 CORS：account / event 已開 `allow_origins=["*"]`；transaction / ticket 的 `main.py` **沒有加 CORS middleware**，瀏覽器直接打會被擋。Demo 前請在 transaction / ticket 的 `app/main.py` 加上 `CORSMiddleware`（與 account 相同寫法）。正式環境 `allow_origins` 應改成前端實際網域。

---

## 12. 成本控制與清理（重要！Free Trial 會燒額度）

- **GKE Autopilot** 按實際 Pod 用量計費；8 個容器（4 app + 4 proxy，各 0.25 vCPU）約對齊架構圖估算。
- **Cloud SQL db-f1-micro** 最便宜；不用時可 `gcloud sql instances patch $SQL_INSTANCE --activation-policy=NEVER` 停機省錢，要 demo 再 `--activation-policy=ALWAYS`。
- **Ingress LB + 靜態 IP** 會持續計費（靜態 IP 未綁定時反而更貴），demo 結束記得釋放。

**Demo 結束後全部清掉（避免續扣）：**

```bash
kubectl delete -f k8s/ --recursive               # 或逐一 delete
gcloud container clusters delete $CLUSTER --region=$REGION
gcloud sql instances delete $SQL_INSTANCE
gcloud compute addresses delete ticketing-ip --global
gcloud artifacts repositories delete $AR_REPO --location=$REGION
```

---

## 13. 替代方案：Cloud Run（更便宜、更快、適合純 demo）

若不需要展示 K8s（架構分數可能略少，但省錢省事）：每個服務 `gcloud run deploy <svc> --image ... --add-cloudsql-instances $SQL_CONN --set-env-vars ENV=production,..._DB_HOST=/cloudsql/$SQL_CONN,... --region $REGION --allow-unauthenticated`。Cloud Run 內建 Cloud SQL 連線（unix socket，路徑同樣 `/cloudsql/<conn>`），可 scale-to-zero，閒置不收錢。跨服務 URL 改成各 Cloud Run service 的 `*.run.app` 網址即可。**前置 2.1（event DB 修正）一樣必要。**

---

## 14. 常見問題

| 症狀 | 可能原因 / 解法 |
|------|----------------|
| Pod `CrashLoopBackOff`，log 顯示 DB 連線失敗 | proxy sidecar 還沒起好就連 DB；確認 `ENV=production`、`*_DB_HOST=/cloudsql/<conn>`、KSA 綁定正確（`roles/cloudsql.client`）。 |
| `exec format error` | image 是 ARM；務必用 Cloud Build（amd64）而非本機 `docker build`。 |
| transaction 報名回 500，log 有 `EventService ... 401` | `INTERNAL_API_KEY` 兩服務不一致，或 event 沒部署 `/v1/internal/events/{id}`。 |
| 前端 fetch 被 CORS 擋 | transaction / ticket 的 `main.py` 加 `CORSMiddleware`（見第 11 節）。 |
| Ingress 一直沒 ADDRESS | GKE Ingress 佈署需數分鐘；`kubectl describe ingress` 看事件；確認靜態 IP 是 **global**。 |
| migration job 卡 Running 不結束 | sidecar 模式正常；看到 seed 完成 log 即可手動刪 job。 |

---

# 附錄 A：接手隊友既有部署（Cloud Run）— 接手前必讀

> 現況：隊友為了讓**前端先測**，已用 **Cloud Run**（不是 GKE）部署了四個後端服務，並建立了 Cloud SQL + 灌了 mock 測試資料；GKE 叢集**已建立但（推測）為空**。本附錄說明「已做什麼／怎麼查證／我能接什麼／絕對不要動什麼」。上面 §1~§14 的 GKE 流程屬於**之後（週末）可選的遷移目標**，不是現在要從零重跑。

## A.0 ⚠️ 機密處理（先做）
隊友提供的 Cloud SQL 密碼規則為 **`<服務名>!DB1`**（例：`account!DB1`、`event!DB1`、`transaction!DB1`、`ticket!DB1`）。
**請勿把真實密碼 commit 進 repo。** 建議：把密碼放本機未追蹤的筆記或 GCP **Secret Manager**；若一定要記在檔案，請建立 `docs/secrets.local.md` 並加入 `.gitignore`。本附錄只記「規則」不記完整明文。

## A.1 隊友已完成（依其留言與提供資訊）
- 以 **Cloud Run** 部署四個服務（`asia-east1`）：
  - Account：`https://account-api-75541019693.asia-east1.run.app`
  - Event：`https://event-service-75541019693.asia-east1.run.app`
  - Transaction：`https://transaction-service-75541019693.asia-east1.run.app`
  - Ticket：`https://ticket-service-75541019693.asia-east1.run.app`
- 已**建立 GKE 叢集**（但服務跑在 Cloud Run，叢集內應無工作負載）。
- 已建立 **Cloud SQL** 並灌入 **mock 測試資料**（前端正在用）。
- Cloud SQL 採**每服務一組 DB 使用者**，密碼規則 `<服務名>!DB1`（與本指南主文示範的單一 `postgres` 使用者不同，遷移時要注意）。

## A.2 怎麼查證現況（你目前只做過 auth login，先盤點再動手）

> **重點觀念：雲端資源跟「哪台電腦」無關。** 你和隊友用**同一個 Google 帳號**，所有 Cloud Run / Cloud SQL / GKE / Artifact Registry 都建立在**同一個 GCP 專案**裡。隊友用另一台電腦不影響你——只要你的 `gcloud` 指到同一個專案，下面所有 `describe/list` 指令在你電腦上看到的就是隊友建好的同一份資源。你不需要他的電腦。
>
> 你電腦上**唯一拿不到**的是：隊友本機當時用來部署的「程式碼狀態 / `.env` 機密」。所以**不要假設「線上跑的 = 你本機 repo 的程式碼」**（見 A.3 第 3 步的提醒）。

```bash
# 0) 先確認你連到「正確的專案」（很可能不是你 gcloud 預設的那個）
gcloud projects list                       # 看你帳號能存取哪些專案，找出有這套系統的那個
gcloud config set project <PROJECT_ID>     # 設成隊友部署的專案
gcloud config set compute/region asia-east1
gcloud config get-value project            # 再次確認

# 快速確認「設對專案了」：這行應列出 account-api / event-service / ... 四個服務
gcloud run services list --region=asia-east1

# 1) Cloud Run：列出服務 + 看每個服務的 image / env / 連到哪個 Cloud SQL
gcloud run services list --region=asia-east1
for S in account-api event-service transaction-service ticket-service; do
  echo "===== $S ====="
  gcloud run services describe $S --region=asia-east1 \
    --format="yaml(spec.template.spec.containers[0].image, \
                   spec.template.spec.containers[0].env, \
                   spec.template.metadata.annotations)"
done
# 重點看：image tag、ENV、各 *_DB_* 變數、以及
# annotation run.googleapis.com/cloudsql-instances（= 連到的 Cloud SQL 連線名稱）

# 2) Cloud SQL：實例 / 連線名稱 / 資料庫 / 使用者
gcloud sql instances list
gcloud sql instances describe <INSTANCE_NAME> --format="value(connectionName,ipAddresses)"
gcloud sql databases list --instance=<INSTANCE_NAME>   # 應有 account_db/event_db/transaction_db/ticket_db
gcloud sql users list --instance=<INSTANCE_NAME>        # 確認是不是 account/event/transaction/ticket 四個 user

# 3) GKE：叢集是否存在、是否真的空
gcloud container clusters list
gcloud container clusters get-credentials <CLUSTER_NAME> --region=asia-east1
kubectl get deploy,svc,ingress -A    # 除了 kube-system 等系統元件，應該沒有我們的服務

# 4) Artifact Registry：image 在哪、有哪些 tag
gcloud artifacts repositories list
gcloud artifacts docker images list asia-east1-docker.pkg.dev/<PROJECT_ID>/<REPO>

# 5) 健康檢查（四個 Cloud Run URL 都應回 JSON）
for U in account-api event-service transaction-service ticket-service; do
  echo "== $U =="; curl -s https://$U-75541019693.asia-east1.run.app/ ; echo
done

# 6) 看 log 確認 DB 連線正常（尤其 Event —— 它原本沒有 production 分支，要確認隊友怎麼讓它連上）
gcloud run services logs read event-service --region=asia-east1 --limit=50
#   若上面指令在你的 gcloud 版本不存在，改用：
#   gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=event-service' --limit=50 --freshness=1d
```

> **特別查證 Event**：本指南 §2.1 指出 `event/app/core/database.py` 原本沒有 production 分支。若隊友是在**未套用該修正**的情況下部署，Event 連 Cloud SQL 很可能是靠別的方式（例如改用 TCP/公開 IP，或他自己已經補了 production 分支）。請從 step 1 的 env 與 step 6 的 log 確認 Event 實際用什麼方式連 DB——這會決定你之後重部署要不要先補 §2.1。

## A.3 我可以接手的工作（建議順序）

1. **盤點（A.2）**：先把 image tag、env、Cloud SQL 連線名稱、四個 user、GKE 叢集名稱記下來。
2. **驗證跨服務整合是否真的通**（最關鍵）：用 Cloud Run URL 走一次報名流程——
   ```bash
   # 登入拿 token（mock 帳號在 scripts/mock_data.yaml）
   curl -X POST https://account-api-75541019693.asia-east1.run.app/v1/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"employeeId":"<mock員編>","password":"<密碼>","role":null}'
   # 用 token 打 transaction 的 eligibility（會觸發 transaction → event 的 internal 呼叫）
   curl https://transaction-service-75541019693.asia-east1.run.app/v1/events/<eventId>/eligibility \
     -H "Authorization: Bearer <token>"
   ```
   若這步 500、log 顯示 `EventService ... 401/404`，代表**隊友的部署版本早於我們的 Plan B 修改**（Event 還沒有 `/v1/internal/events/{id}`、或 transaction 還在帶 user token）。→ 進第 3 步。
3. **把我們這次的程式修正部署成 Cloud Run 新 revision**（可回滾、不影響現有流量直到你切換）：
   - **先對齊程式碼來源（重要）**：線上跑的 image 是隊友從**他的電腦**build 的，未必等於你本機 repo 的內容，也未必有 push 上 git。動手前先：(a) `git fetch && git status` 確認你和隊友在同一個 branch / commit；(b) 用 A.2 step 1 看線上服務的 **image tag**，再 `gcloud artifacts docker images describe <image>:<tag> --format='value(image_summary)'`（或看 Cloud Build 紀錄 `gcloud builds list --limit=10`）回推它是從哪個版本 build 的。**確認「線上版本」與「你要部署的版本」差異後再 build**，避免覆蓋掉隊友尚未 push 的修改。
   - 需要部署的修正：Event 的 `/v1/internal/events/{id}` internal 端點 + `verify_internal_key`、`event/database.py` production 分支（§2.1）、Transaction 的 EventClient 改用 X-Internal-Key、transaction/ticket 的 CORS、response model 等。
   - 用**新的 image tag**（例：`v2`）重 build：`gcloud builds submit --config cloudbuild.yaml --substitutions=_TAG=v2,...`（見 §4）。
   - 部署新 revision（沿用既有服務名與既有 env，不要改 URL）：
     ```bash
     gcloud run deploy event-service \
       --image asia-east1-docker.pkg.dev/<PROJECT_ID>/<REPO>/event:v2 \
       --region asia-east1
     # transaction-service 同理
     ```
   - Cloud Run 會自動建立新 revision；測通後流量已在新版，**有問題可一鍵 rollback 到舊 revision**（Console → Revisions，或 `gcloud run services update-traffic ... --to-revisions=<舊>=100`）。
4. **（週末，可選）遷移到既有 GKE 叢集**：用主指南 §5.1~§10，但**沿用既有 Cloud SQL 與 Artifact Registry**（不要重建）。GKE 跑起來、驗證通過後再決定是否把流量從 Cloud Run 切走；**確認 GKE 穩定前不要刪 Cloud Run**。
5. **補資料（如需要）**：只用 upsert，不要 reset（見 A.4）。

## A.4 千萬不要做（會弄壞現有功能或重複計費）

- ❌ **不要再 `gcloud container clusters create-auto`**：叢集已存在，重建會報錯或多花錢。
- ❌ **不要再 `gcloud sql instances create`**：實例已存在且有前端在用的測試資料。
- ❌ **不要改 Cloud SQL 使用者密碼**：四個 Cloud Run 服務正用 `<服務名>!DB1` 連線，改了它們會全部連不上。
- ❌ **不要刪除 Cloud Run 服務、也不要改它們的 URL/服務名**：前端已經把這四個 URL 寫進設定。
- ❌ **不要對共用的 Cloud SQL 跑 `python scripts/seed_all.py --reset`**：`--reset` 會清掉前端正在測試的資料。要補資料就用不帶 `--reset` 的 upsert，並先在群組講一聲。
- ❌ **不要用相同 image tag 原地覆蓋**：請用新 tag（v2、v3…），才能保留可回滾的 revision。
- ❌ **不要把 DB 密碼 commit 進 repo**（見 A.0）。
- ⚠️ 隊友說「mock 資料若干擾前端可刪」——刪之前**先跟前端確認**，避免刪到他們正在測的活動/帳號。

## A.5 現況（Cloud Run）與主指南（GKE）的差異對照

| 項目 | 隊友現況（Cloud Run） | 本指南主文（GKE，遷移目標） |
|------|----------------------|----------------------------|
| 運算 | Cloud Run（scale-to-zero、最省事） | GKE Autopilot（對齊架構圖、架構分數較高） |
| Cloud SQL 連線 | Cloud Run 內建 `--add-cloudsql-instances`（unix socket `/cloudsql/<conn>`） | Cloud SQL Auth Proxy sidecar（unix socket） |
| DB 使用者 | **每服務一組** user，密碼 `<服務名>!DB1` | 主文示範用單一 `postgres`（遷移時改成沿用四個 user 即可） |
| 對外路由 | 四個 `*.run.app` 網址 | GKE Ingress + 子網域（nip.io） |

> 遷移到 GKE 時，把每個 Deployment 的 `*_DB_USER` / `*_DB_PASSWORD` 改成對應的四組 user 與密碼（從 Secret 注入），其餘照 §8 即可。
