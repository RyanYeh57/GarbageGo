# API 說明（v0）

> **建立日期：** 2026-11-24
> **讀者：** 前端（接 API）、後端（把假資料換成真的）
> **依據：** `backend/app/api/schemas.py`（欄位以這個檔為準）。範例是 2026-11-24 實際呼叫得到的回應。
> **相關：** 分工與設計理由看 `docs/architecture/backend-architecture.md` §4、§6。

## 一分鐘看懂

| API | 做什麼 | 現在回什麼 | 負責人 | 預計換成真的 |
|---|---|---|---|---|
| `GET /health` | 檢查後端、資料庫、最新 GPS 時間 | ✅ **真的** | Ian1114（後端 B） | 已完成 |
| `GET /stops/nearby` | 找我附近的收運點 | 假資料 | hobartXIII（後端 A） | 第 2 週 |
| `GET /stops/{id}` | 一個收運點的一週時段 | 假資料 | hobartXIII（後端 A） | 第 2 週 |
| `GET /stops/{id}/eta` | 垃圾車大概幾點到這個點 | 假資料 | Ian1114（後端 B） | 第 2～3 週 |
| `POST /recommendations` | 推薦我去哪個點倒垃圾（含備案） | 假資料 | RyanYeh57（架構師） | 第 2 週 |
| `GET /routes/walk` | 走過去的路線（畫在地圖上） | 假資料 | hobartXIII（後端 A） | 第 3 週 |
| `POST /chat` | 用打字問 AI 助理 | 假資料 | RyanYeh57（架構師） | 第 3 週 |

前端 anjyuelee 負責接上面全部的 API。

**假資料長這樣：** 永遠回同樣 3 個點（id `1001`、`1002`、`1003`），地址寫「示範路」、車牌寫 `TEST-0001`、說明文字開頭有 `[假資料]`。**傳什麼位置都一樣。**

**自動產生的規格頁：** 後端跑起來後，打開 `http://<後端網址>/docs`，可以直接在網頁上試打每支 API。

## 1. 共通規則

### 1.1 時間

| 規則 | 說明 |
|---|---|
| 輸出 | 一律臺北時間，結尾是 `+08:00`，例如 `2026-11-24T19:03:00+08:00` |
| 輸入 `at` | 可選。ISO 8601 格式；**沒寫時區就當臺北時間**。沒給就用現在 |
| `at` 有什麼用 | 假裝現在是某個時間。晚上、週日沒車時，也能用歷史資料 Demo |
| 只有時刻的欄位 | `start`、`end` 是 `"19:00:00"`，沒有日期 |

接受 `at` 的 API：`/stops/nearby`、`/stops/{id}/eta`、`/recommendations`、`/chat`。

### 1.2 位置

| 規則 | 說明 |
|---|---|
| `lat` | 緯度，−90～90 |
| `lon` | 經度，−180～180 |
| 路線座標 | `[lon, lat]`，**經度在前**（GeoJSON 的順序） |
| 隱私 | 後端 log 只記方法、路徑、狀態碼，**不記使用者位置** |

### 1.3 錯誤

所有錯誤都是同一個格式：

```json
{"error": {"code": "validation_error", "message": "lat: Input should be less than or equal to 90"}}
```

| HTTP 狀態碼 | `code` | 什麼時候 |
|---|---|---|
| 422 | `validation_error` | 參數格式錯，或超出範圍（例如 `lat=999`） |
| 404 | `stop_not_found` | 收運點 id 不存在 |
| 404 | `not_found` | 網址打錯 |

錯誤訊息**不會**重複你傳的值（避免把位置印出來）。

## 2. 各支 API

### 2.1 `GET /health` — 後端還活著嗎

**用途：** App 啟動時檢查連不連得上；Ian1114（後端 B）每天看 GPS 收集有沒有停。

**參數：** 無

**回應：**

| 欄位 | 意思 |
|---|---|
| `status` | 永遠是 `ok`（回得出來就代表後端活著） |
| `db` | `ok` 或 `error`（資料庫連不上） |
| `latest_gps_at` | 資料庫裡最新一筆 GPS 的時間；沒資料是 `null` |

```json
{"status": "ok", "db": "ok", "latest_gps_at": "2026-11-19T06:49:59+08:00"}
```

⚠️ `latest_gps_at` 太舊（例如超過 30 分鐘）＝ GPS 收集停了，不是後端壞了。

### 2.2 `GET /stops/nearby` — 我附近有哪些收運點

**用途：** 地圖標點、附近點列表。

**參數：**

| 參數 | 必填 | 意思 |
|---|---|---|
| `lat`、`lon` | ✅ | 使用者位置 |
| `radius` | | 搜尋半徑（公尺），100～2000，預設 500 |
| `at` | | 見 §1.1 |

**回應：** 收運點陣列，每個點：

| 欄位 | 意思 |
|---|---|
| `id` | 收運點 id，給 `/stops/{id}` 用 |
| `area`、`village`、`address` | 行政區、里、地址 |
| `lat`、`lon` | 收運點座標 |
| `geocode_level` | 座標多準，見 §3.1 |
| `today_slots` | 今天的收運時段：`kind`（`general` 一般垃圾／`recycle` 回收）、`start`、`end` |
| `distance_m` | 直線距離（公尺）。**只是參考**，推薦看的是步行時間 |

```json
[{"id": 1001, "area": "西區", "village": "示範里", "address": "臺中市西區示範路1號",
  "lat": 24.1481, "lon": 120.6742, "geocode_level": "exact",
  "today_slots": [{"kind": "general", "start": "19:00:00", "end": "19:10:00"},
                  {"kind": "recycle", "start": "19:00:00", "end": "19:10:00"}],
  "distance_m": 75}]
```

### 2.3 `GET /stops/{id}` — 這個點一週哪幾天收

**用途：** 收運點詳細頁。

**參數：** 網址裡的 `id`。不存在 → 404 `stop_not_found`。

**回應：** 和 §2.2 一樣的基本欄位（沒有 `today_slots`、`distance_m`），再加：

| 欄位 | 意思 |
|---|---|
| `car_licence` | 負責的垃圾車車牌 |
| `weekly` | 一週的時段：`weekday`（1＝星期一 … 7＝星期日）、`kind`、`start`、`end` |

```json
{"id": 1001, "area": "西區", "village": "示範里", "address": "臺中市西區示範路1號",
 "lat": 24.1481, "lon": 120.6742, "geocode_level": "exact", "car_licence": "TEST-0001",
 "weekly": [{"weekday": 1, "kind": "general", "start": "19:00:00", "end": "19:10:00"}]}
```

### 2.4 `GET /stops/{id}/eta` — 垃圾車大概幾點到

**用途：** 收運點詳細頁顯示預計到達時間。Ian1114（後端 B）也用它單獨測 ETA。

**參數：** 網址裡的 `id`（不存在 → 404），可選 `at`。

**回應（ETA 結果，最重要的格式）：**

| 欄位 | 意思 |
|---|---|
| `status` | 這個估計靠什麼算的，見 §3.2 |
| `eta` | 預計到達時間 |
| `eta_low`、`eta_high` | 最早、最晚可能幾點到（不確定的範圍） |
| `data_time` | 用到的 GPS 是幾點的資料；沒用 GPS 是 `null` |
| `scheduled_start`、`scheduled_end` | 表定時段。⚠️ **表定不等於實際到達** |
| `method` | 用哪個方法算：`schedule`（照表定）、`distance_speed`（距離÷速度）、`historical_avg`（歷史平均） |

用即時 GPS（`live`）：

```json
{"status": "live", "eta": "2026-11-24T19:03:00+08:00",
 "eta_low": "2026-11-24T19:01:00+08:00", "eta_high": "2026-11-24T19:08:00+08:00",
 "data_time": "2026-11-24T18:48:00+08:00",
 "scheduled_start": "2026-11-24T19:00:00+08:00", "scheduled_end": "2026-11-24T19:10:00+08:00",
 "method": "distance_speed"}
```

只有表定時間（`schedule_only`）：`eta` 是時段中間，範圍就是表定時段。

```json
{"status": "schedule_only", "eta": "2026-11-24T19:45:00+08:00",
 "eta_low": "2026-11-24T19:40:00+08:00", "eta_high": "2026-11-24T19:50:00+08:00",
 "data_time": null,
 "scheduled_start": "2026-11-24T19:40:00+08:00", "scheduled_end": "2026-11-24T19:50:00+08:00",
 "method": "schedule"}
```

假資料：`1001` 是 `live`、`1002` 是 `stale`、`1003` 是 `schedule_only`。

### 2.5 `POST /recommendations` — 我該去哪個點

**用途：** App 主畫面，告訴使用者去哪裡、為什麼、有什麼風險。

**Body（JSON）：**

| 欄位 | 必填 | 意思 |
|---|---|---|
| `lat`、`lon` | ✅ | 使用者位置 |
| `at` | | 見 §1.1 |
| `deadline` | | 最晚幾點要倒完 |
| `radius_m` | | 搜尋半徑，100～2000，預設 500 |

```json
{"lat": 24.148, "lon": 120.674, "at": "2026-11-24T18:50:00"}
```

**回應：**

| 欄位 | 意思 |
|---|---|
| `at` | 用哪個時間算的 |
| `primary` | 主推薦；全部趕不上時是 `null` |
| `alternatives` | 備案，最多 2 個 |
| `message` | 特殊狀況的說明，例如國定假日停收、全部趕不上；平常是 `null` |

`primary` 和每個備案的內容：

| 欄位 | 意思 |
|---|---|
| `stop` | 收運點（同 §2.2 的一個點） |
| `walk` | 走過去要多久：`duration_s`（秒）、`distance_m`、`method`（`valhalla` 真實路線／`fallback` 直線粗估） |
| `eta` | 垃圾車幾點到（同 §2.4） |
| `slack_s` | 到了之後還能等幾秒。正的＝來得及。算不出來是 `null` |
| `feasible` | 來不來得及 |
| `risks` | 風險標籤，見 §3.3。空陣列＝沒有已知風險 |
| `reason` | 給使用者看的一句話理由 |

```json
{"at": "2026-11-24T18:50:00+08:00",
 "primary": {"stop": {"id": 1001, "...": "..."},
             "walk": {"duration_s": 90, "distance_m": 75, "method": "valhalla"},
             "eta": {"status": "live", "...": "..."},
             "slack_s": 600, "feasible": true, "risks": [],
             "reason": "[假資料] 走路 2 分鐘，車子用即時 GPS 估計，時間最寬裕。"},
 "alternatives": [{"stop": {"id": 1003, "...": "..."}, "risks": ["schedule_only"], "...": "..."}],
 "message": null}
```

### 2.6 `GET /routes/walk` — 走過去的路線

**用途：** 在地圖上畫步行路線。

**參數（全部必填）：** `from_lat`、`from_lon`（起點）、`to_lat`、`to_lon`（終點）

**回應：** `duration_s`、`distance_m`、`method`（同 §2.5 的 `walk`），再加：

| 欄位 | 意思 |
|---|---|
| `coordinates` | 路線上的點，`[lon, lat]` 陣列，照順序連起來就是路線 |

```json
{"duration_s": 300, "distance_m": 350, "method": "fallback",
 "coordinates": [[120.674, 24.148], [120.6741, 24.14805], [120.6742, 24.1481]]}
```

假資料只回起點、中點、終點 3 個點。

### 2.7 `POST /chat` — 問 AI 助理

**用途：** 對話畫面。AI 會用後端的真實資料回答，**不自己編時間或地點**。

**Body（JSON）：**

| 欄位 | 必填 | 意思 |
|---|---|---|
| `message` | ✅ | 使用者的問題，1～500 字 |
| `lat`、`lon` | ✅ | 使用者位置 |
| `at` | | 見 §1.1 |

**回應：**

| 欄位 | 意思 |
|---|---|
| `reply` | AI 的回答 |
| `tool_results` | AI 回答時查了哪些資料（給 App 顯示依據用）；現在是空陣列 |
| `at` | 用哪個時間 |

```json
{"reply": "[假資料] 這是第 1 週的固定回答，之後會換成真的 AI 助理。", "tool_results": [], "at": "2026-11-24T18:50:00+08:00"}
```

## 3. 代碼對照

### 3.1 `geocode_level`：座標多準

| 值 | 意思 | App 建議 |
|---|---|---|
| `exact` | 地址完全對到門牌 | 正常顯示 |
| `approx_suffix` | 去掉「號前」「號旁」才對到 | 正常顯示 |
| `approx_base_number` | `263之1號` 對不到，用 `263號` | 正常顯示 |
| `approx_nearby_number` | 用同一條路最近的門牌（差 10 號以內） | 標「位置是大概的」 |

### 3.2 ETA `status`

| 值 | 意思 | 推薦怎麼處理 |
|---|---|---|
| `live` | 用 15 分鐘內的即時 GPS 算的 | 正常 |
| `schedule_only` | 沒有可用 GPS，只能照表定時間（第 1～2 週都是這個） | 可推薦，標風險 |
| `stale` | 有 GPS，但超過 15 分鐘沒更新 | 可推薦，標「GPS 過期」 |
| `passed` | 車已經過了 | 不推薦 |
| `no_data` | 今天不收，或這個點沒有座標 | 不推薦 |

### 3.3 推薦的 `risks`

| 值 | 意思 |
|---|---|
| `gps_stale` | 車子的 GPS 太舊 |
| `schedule_only` | 只有表定時間，沒有即時 GPS |
| `approx_location` | 收運點座標是大概的 |
| `walk_fallback` | 步行時間是直線粗估，不是真實路線 |

## 4. 換成真資料前要先決定的事

下面這些地方，`schemas.py` 的規格和資料庫裡的真資料對不上。換成真資料時會出錯，**要 RyanYeh57（架構師）和 anjyuelee（前端）一起決定**才能改（規格改了，前端也要跟著改）。

| # | 問題 | 會怎樣 | 影響的 API |
|---|---|---|---|
| 1 | 資料庫有 81 個點的 `geocode_level` 是 `suspect`（座標可疑），但 §3.1 沒有這個值 | 回傳這些點時會出錯 | `/stops/*`、`/recommendations` |
| 2 | TGOS、人工補的座標要用什麼 `geocode_level` 還沒定 | 同上 | 同上 |
| 3 | `lat`、`lon` 規定一定要有值，但 874 個點沒有座標 | `/stops/{id}` 查到這些點會出錯（`/stops/nearby` 用位置搜尋，本來就找不到它們） | `/stops/{id}` |
| 4 | `car_licence` 規定一定要有值，但資料庫裡有 6 個點是空的（`NULL`） | `/stops/{id}` 查到這些點會出錯 | `/stops/{id}` |

## 5. 改規格的規則

- 欄位名稱就是前後端的約定。**要改任何欄位，先告訴 RyanYeh57（架構師）和 anjyuelee（前端）。**
- 改了 `schemas.py`，同步更新這份文件和相關測試。
