# GarbageGo 初版架構草稿

> **Status:** Proposed / Pending Approval  
> **Version:** v0.1  
> **Scope:** 附近收運點查詢、垃圾車 ETA 估計與到點可行性推薦

## 1. Architecture Direction

第一版預計採用：

> **模組化單體架構（Modular Monolith）+ PostgreSQL/PostGIS**

系統先以一個可部署的 Backend 應用程式承載多個職責清楚的模組。模組之間透過明確的介面溝通，但第一版不拆成多個獨立微服務。

資料層預計使用 PostgreSQL 儲存結構化資料，使用 PostGIS 支援收運點、車輛位置與使用者位置的空間查詢。

本文件是架構草稿，不代表技術選型已完成核准，也不代表相關功能已經實作。

## 2. Why This Architecture

### 2.1 選擇模組化單體

- 專案目前仍在 Proposal 與資料可行性驗證階段。
- 目前沒有足夠需求證明需要微服務。
- 單一應用程式比較容易開發、測試、部署與除錯。
- GIS、ETA 與 Recommendation Engine 可以先保持獨立責任。
- 未來若某個模組有獨立擴充需求，再考慮拆成服務。

### 2.2 選擇 PostgreSQL/PostGIS

- PostgreSQL 適合儲存路線、車輛、收運點、排程與觀測資料。
- PostGIS 可以支援附近收運點與空間範圍查詢。
- 即時資料與歷史 JSON 可以轉換成同一套標準資料模型。
- 可以保留原始 JSON，方便日後重新處理與追查資料來源。
- 先使用單一資料庫，避免第一版引入不必要的資料同步複雜度。

## 3. Logical Components

```text
User / Web UI
      ↓
Backend API / Application Layer
      ↓
LLM Agent / Orchestrator（可選，非數值計算核心）
      ↓
Recommendation Engine
   ┌──┴──────────────┐
   ↓                 ↓
GIS Engine        ETA Engine
   ↑                 ↑
   └──────┬──────────┘
          ↓
Data Access Layer
          ↓
PostgreSQL + PostGIS
          ↑
Data Acquisition & Validation
   ┌──────┴──────────────┐
   ↓                     ↓
Official API       Historical JSON
```

### 3.1 Data Acquisition

負責：

- 取得官方垃圾車 API 資料。
- 讀取歷史 JSON 資料。
- 記錄資料來源與匯入時間。
- 將不同輸入轉成同一種內部資料格式。
- 處理 API 失敗、資料缺失與重複資料。

### 3.2 Data Validation and Normalization

負責：

- 檢查必要欄位是否存在。
- 驗證時間格式與時區假設。
- 驗證座標範圍與座標系統。
- 保留 `observed_at` 與 `collected_at`。
- 將 API 欄位轉成系統內部使用的標準欄位。
- 保留原始 JSON 供追查與重新處理。

### 3.3 GIS Engine

負責：

- 搜尋使用者附近的候選收運點。
- 查詢收運點與路線的空間關係。
- 估計使用者到收運點的步行時間。
- 支援未來替換不同的地圖或路徑服務。

GIS Engine 不應只使用直線距離代表實際步行時間。

### 3.4 ETA Engine

負責：

- 根據目前車輛觀測資料估計垃圾車 ETA。
- 使用歷史資料建立 Baseline。
- 評估資料新鮮度與 ETA 不確定性。
- 在資料不足時回傳明確的降級狀態。

第一版先考慮：

1. Schedule Baseline。
2. 歷史同路線或相近時段平均。
3. Distance / Speed Baseline。
4. 完成資料評估後，再決定是否導入 Machine Learning。

### 3.5 Recommendation Engine

負責：

- 排除已不符合清運條件的候選點。
- 計算時間餘裕。
- 根據 ETA、步行時間、資料品質與風險排序。
- 找出替代收運點。
- 產生可追溯的推薦依據。

核心概念：

```text
slack = truck_ETA - walking_time - safety_buffer
```

`slack > 0` 只代表目前資料下具備可行性，不代表一定能趕上。

### 3.6 LLM Agent / Orchestrator

LLM Agent 預計負責：

- 理解使用者自然語言需求。
- 判斷需要哪些工具。
- 協調 GIS、ETA 與 Recommendation Engine。
- 將工具結果轉成繁體中文說明。

LLM Agent 不負責：

- 自行猜測 GPS 座標。
- 自行產生步行時間。
- 自行產生垃圾車 ETA。
- 取代 GIS、ETA 或推薦邏輯。

第一版也可以先不加入 LLM，先驗證資料與推薦核心邏輯。

## 4. Proposed Data Model

第一版預計使用以下概念資料表：

| Table | Purpose |
|---|---|
| `vehicle_observations` | 儲存官方 API 與歷史 JSON 的車輛觀測資料 |
| `collection_stops` | 儲存收運點位置與基本資訊 |
| `collection_schedules` | 儲存收運時段、路線與排程 |
| `routes` | 儲存路線與路線識別資訊 |
| `eta_predictions` | 儲存 ETA、資料時間與不確定性 |
| `recommendation_requests` | 儲存可選的查詢與推薦結果記錄 |

`vehicle_observations` 預計包含：

| Field | Meaning |
|---|---|
| `line_id` | 路線識別資訊 |
| `car_id` | 車輛識別資訊 |
| `observed_at` | API 或歷史資料描述的時間 |
| `collected_at` | 系統收到或匯入資料的時間 |
| `location` | 原始位置欄位 |
| `x` / `y` | 座標欄位 |
| `speed_value` | 車速資料 |
| `over_speed` | 超速狀態 |
| `source` | `api` 或 `historical` |
| `raw_payload` | 原始 JSON，預計使用 JSONB 儲存 |

實際欄位、資料型別、主鍵與索引需要在資料盤點後確認。

## 5. Main Data Flows

### 5.1 API and Historical Data Ingestion

```text
API / Historical JSON
        ↓
Parse
        ↓
Validate fields, time, and coordinates
        ↓
Normalize to canonical schema
        ↓
Store raw payload and normalized record
        ↓
Update GIS / ETA input data
```

### 5.2 Recommendation Query

```text
User query and location
        ↓
Understand request
        ↓
Find candidate collection stops
        ↓
Estimate walking time
        ↓
Estimate truck ETA
        ↓
Assess freshness and uncertainty
        ↓
Calculate slack and feasibility
        ↓
Rank recommendations and alternatives
        ↓
Return evidence, timestamps, and limitations
```

### 5.3 Degraded Data Flow

當 API 失敗、GPS 過期或資料不足時：

1. 標記資料狀態。
2. 降低推薦信心或標記為不確定。
3. 改用明確標示的排程或歷史 Baseline（若適用）。
4. 沒有足夠依據時，不產生精確 ETA。
5. 回傳資料限制與可用的替代方案。

## 6. Deployment Direction

第一版預計以單一應用程式與單一資料庫部署：

```text
Backend Application
  ├── API Layer
  ├── Application Services
  ├── Domain Modules
  └── Data Access Layer

PostgreSQL + PostGIS

Optional:
  ├── Scheduled Data Ingestion Worker
  └── Web UI / Map Frontend
```

資料匯入工作可以先使用簡單排程執行。當資料量、查詢量或執行時間增加後，再評估是否需要獨立 Worker、Queue 或拆分服務。

## 7. Future Split Conditions

目前不預先拆微服務。只有在下列情況成立時，才重新評估：

- Data Acquisition 需要獨立排程與擴充。
- ETA Engine 需要獨立模型服務或不同部署週期。
- GIS 查詢量與 API 查詢量需要分開擴展。
- Recommendation Engine 需要被多個產品共用。
- 單體部署已造成明確的效能、可靠性或維護問題。

拆分時仍應保留清楚的資料契約、時間戳、來源與不確定性資訊。

## 8. Open Decisions

以下項目尚未定案：

- Backend 是否採用 Python + FastAPI。
- PostgreSQL/PostGIS 的正式版本與部署方式。
- 步行路徑服務供應商。
- API 與歷史資料的匯入頻率。
- 歷史資料保存期限與隱私處理方式。
- ETA Baseline 的欄位、時間切分與評估方法。
- 是否需要 Message Queue 或獨立 Worker。
- LLM Provider、Tool Calling 與 RAG 是否納入 MVP。

## 9. Verification Plan

架構正式採用前，應完成：

1. 驗證官方 API 欄位、座標系統與更新頻率。
2. 驗證歷史 JSON 是否能穩定轉換成標準資料模型。
3. 使用固定測試資料驗證 GIS 查詢與 ETA Baseline。
4. 測試 API 失敗、資料過期、座標缺失與沒有可行候選點的情境。
5. 比較最近收運點策略與時間可行性推薦策略。
6. 完成技術選型後，更新 `DESIGN.md` 的 Decision Status。
