# 第 1 週後端地基 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 做出第 1 週的後端地基：能用 Docker Compose 啟動的 FastAPI 後端、給前端的假資料 API、資料表、84004 收運點與座標匯入、歷史 GPS 匯入、`d1`～`d7` 星期對應的結論、部署主機與 `https` 網址。

**Architecture:** 照 `docs/architecture/backend-architecture.md`。一份程式碼、`api` 程序（FastAPI）、PostgreSQL + PostGIS。HTTP 層只做驗證與組裝，資料匯入放在 `app/modules/ingestion/`。第 1 週 API 回固定假資料，讓前端先開工。

**Tech Stack:** Python 3.12、FastAPI、Pydantic v2、SQLAlchemy 2.0、GeoAlchemy2、Alembic、psycopg 3、pytest、Docker Compose、`postgis/postgis`、Cloudflare Tunnel（`cloudflared`）。

**Spec:** `docs/architecture/backend-architecture.md`（Approved 2026-11-22）；工作分配見 `docs/plans/2026-11-22-backend-work-plan.md`。

## 白話版（先看這段）

這份是**第 1 週的施工說明書**，給寫程式的人照著做。只想知道誰做什麼，看 `docs/plans/2026-11-22-backend-work-plan.md` 就好。

第 1 週做完，要看得到這 5 件事：

1. 打 `docker compose up`，後端就跑起來。
2. 前端打得到 API，拿到**假資料**（先讓 App 開工）。
3. 2 萬個收運點和座標都進了資料庫。
4. 舊的 GPS 資料都進了資料庫，新的也繼續在收。
5. 知道 84004 的 `d1`～`d7` 是不是星期一到星期日。

| Task | 一句話 | 誰 |
|---|---|---|
| 1 | 後端骨架：能啟動、`/health` 會回應、log 不記使用者位置 | 架構師 |
| 2 | 定好 7 支 API 長什麼樣子，先回假資料 | 架構師 |
| 3 | 建 4 張資料表 | 後端 A |
| 4 | 把收運點和座標匯進資料庫 | 後端 A |
| 5 | 把舊的 GPS 匯進資料庫 | 後端 B |
| 6 | 用 GPS 確認 `d1`～`d7` 是星期幾 | 後端 B |
| 7 | 部署主機 + 對外的 `https` 網址 | 後端 A + 後端 B |

**順序：** Task 1 先做完，其他人才開工。唯一例外：後端 B **第一天**就把 GPS 收集程式搬到部署主機（Task 7 Step 5）。

## 決策（2026-11-22 拷問後確認）

| # | 決定 | 沒選的方案 | 為什麼 |
|---|---|---|---|
| 1 | 歷史 GPS 的 `collected_at`（抓到的時間）讀**原始紀錄**（快照檔名或舊 SQLite 欄位）。讀不到就停下報錯 | 用 `observed_at + 2 分鐘` 估 | 用 `at` 重播過去、做 ETA 評估，都靠這個時間判斷「當時看得到哪些 GPS」，估的會偷看到未來 |
| 2 | v1 **鎖定一份 84004**，把下載日期和 sha256 記進 `docs/research/geocoding-local-match-trial.md`。要換版本就整批重建 | 現在就設計跨版本的穩定 `id` | `source_index` 是「排第幾筆」，換版本會錯位；但 4 週內變動機率低，第 1 週已經很滿 |
| 3 | Task 6 維持**第 1 週**完成 | 延到第 2 週週三 | 架構師決定 |
| 4 | 資料表存 84004 原始的 `day_index`，轉星期幾交給設定 | 直接存 `weekday` | 匯入不用等 Task 6 的結論 |
| 5 | 可疑座標（約 81 筆）保留座標，但標 `geocode_level = suspect`，推薦時排除 | 刪掉座標 | 資料不丟，人工確認後可以放回 |
| 6 | `db`、`api` 的 port 只開給本機（`127.0.0.1`），外面只能走 Tunnel | 開給整個網路 | 部署主機可能在學校 Wi-Fi，不要把資料庫露出去 |
| 7 | `config.py` 自己讀 repo 根目錄的 `.env`（小函式，不加套件）；環境變數優先 | 加 `python-dotenv` 或 `pydantic-settings` | 不在已同意的套件清單內 |
| 8 | 匯入函式不自己 commit，由 CLI commit | 函式內 commit | 測試的 rollback 才有效；「地址對不上就整批不寫」才做得到 |

## 範圍外（第 1 週不做）

- 84004 跨版本的穩定身分。
- 每 5 分鐘抓 GPS 的 worker（第 3 週）。
- TGOS 補座標、人工檢查 81 筆可疑座標。
- 資源回收的推薦（v1 只推薦一般垃圾）。
- 國定假日的判斷（第 2 週推薦邏輯再做，規則見 `backend-architecture.md` §1）。

## Global Constraints

- Python 3.12（Docker 映像 `python:3.12-slim`）。
- 只用 spec §9 列的套件：SQLAlchemy 2.0、GeoAlchemy2、Alembic、psycopg 3、httpx、pytest，加上 FastAPI、Pydantic、uvicorn。第 1 週用不到 `anthropic`，先不裝。版本在 Task 1 用 `pip freeze` 鎖進 `backend/requirements.lock`。
- 時間：資料庫一律 `timestamptz`；對外輸出 ISO 8601 含 `+08:00`；臺中市資料裡沒有時區的時間一律當成 `Asia/Taipei`。
- 座標：WGS84（EPSG:4326）；API 的座標陣列順序是 `[lon, lat]`（GeoJSON 慣例）。
- **不把使用者精確位置寫進 log**（`AGENTS.md` §9.4）：access log 不可以印出 query string 或 request body。
- 密碼只放 `.env`；`.env` 不進 Git，`.env.example` 只放變數名稱。
- 模組之間只呼叫對方的 `service.py`；模組函式把「現在」當參數，不直接讀系統時鐘（spec §6）。
- 錯誤格式統一：`{"error": {"code": "...", "message": "..."}}`。
- 不把表定時間當實際到達時間；不把過期 GPS 當即時位置。
- 組員多用 Windows：文件裡的指令要能在 PowerShell 5.1 跑（不用 `&&`、不用 `<` 重新導向、用 `curl.exe` 不用 `curl`）。`pytest` 指令都在 `backend/` 目錄下執行。
- 主機上跑測試和匯入 CLI 時，連 `localhost:5432`；容器內的 `api` 連 `db:5432`。`.env.example` 兩種都列（`DATABASE_URL` 給容器、`HOST_DATABASE_URL` 與 `TEST_DATABASE_URL` 給主機）。
- `docker-compose.yml` 的 port 一律寫成 `127.0.0.1:<port>:<port>`（決策 6）。
- Commit message 用英文（`AGENTS.md` §1）。

## Review Focus

1. **使用者位置出現在 log**：`/stops/nearby?lat=24.1&lon=120.6` 這種請求，uvicorn 預設 access log 會印出完整網址。預期 log 只有方法、路徑、狀態碼。→ Task 1 `test_access_log_has_no_query_string`。
2. **時區**：GPS 的 `20261103T193953` 沒有時區。預期存成 `2026-11-03T19:39:53+08:00`，不是 UTC 19:39。→ Task 5 `test_parse_time_is_taipei`。
3. **座標超出範圍**：App 傳 `lat=999`。預期 422，錯誤格式符合 Global Constraints。→ Task 2 `test_invalid_lat_returns_error_format`。
4. **84004 重複資料**：84004 有 64 筆重複列。預期兩筆都匯入、不當機，每筆有自己的 `source_index`。→ Task 4 `test_duplicate_rows_both_imported`。
5. **壞掉的快照檔**：歷史快照有一份是 0 筆；也可能有不是陣列或不是合法 JSON 的檔案。預期跳過並計數，不中斷整批匯入。→ Task 5 `test_import_skips_empty_and_invalid_files`。

---

## 檔案總覽

| 檔案 | 責任 | Task |
|---|---|---|
| `backend/pyproject.toml`、`backend/requirements.lock`、`backend/Dockerfile` | 套件、版本、映像 | 1 |
| `backend/app/main.py` | 建立 app、掛 routers、錯誤處理 | 1、2 |
| `backend/app/core/config.py` | 從環境變數讀設定 | 1、6 |
| `backend/app/core/clock.py` | `TAIPEI` 時區、臺中時間格式解析 | 1、5 |
| `backend/app/core/logging.py` | 不含 query string 的 access log | 1 |
| `backend/app/db/session.py` | 連線、`get_session` dependency | 1 |
| `backend/app/db/models.py`、`backend/alembic.ini`、`backend/app/db/migrations/` | 資料表與版本 | 3 |
| `backend/app/api/health.py` | `GET /health` | 1、5 |
| `backend/app/api/schemas.py` | ★ 前後端 API 合約（Pydantic） | 2 |
| `backend/app/api/fixtures.py` | 第 1 週假資料 | 2 |
| `backend/app/api/{stops,recommendations,routes,chat}.py` | 假資料 endpoints（`/stops/{stop_id}/eta` 也放在 `stops.py`） | 2 |
| `backend/app/modules/ingestion/stops.py` | 84004 + 座標匯入 | 4 |
| `backend/app/modules/ingestion/gps.py` | GPS 解析與歷史匯入 | 5 |
| `backend/analysis/weekday_mapping.sql` | `d1`～`d7` 對應分析 | 6 |
| `scripts/geocode/match.py`、`village_check.py` | 加輸出欄位給匯入用 | 4 |
| `docker-compose.yml`、`db/init/01-test-db.sql`、`.env.example` | 啟動環境 | 1、3、7 |
| `docs/architecture/deploy-host.md` | 部署主機操作手冊 | 7 |
| `backend/tests/...` | 測試（依模組分資料夾） | 全部 |

---

### Task 1: 後端骨架、Docker Compose、`/health`、無位置 log

**負責：** 架構師

**白話：** 做出一個能跑的空殼後端。打開 `/health` 會回「我活著、資料庫通不通」。log 只記「哪個網址、成功沒」，不記使用者在哪裡。

**Files:**
- Create: `backend/pyproject.toml`、`backend/requirements.lock`、`backend/Dockerfile`
- Create: `backend/app/__init__.py`、`backend/app/main.py`、`backend/app/core/{__init__,config,clock,logging}.py`、`backend/app/db/{__init__,session}.py`、`backend/app/api/{__init__,health}.py`
- Create: `docker-compose.yml`、`.env.example`、`db/init/01-test-db.sql`
- Test: `backend/tests/conftest.py`、`backend/tests/test_health.py`、`backend/tests/core/test_logging.py`、`backend/tests/core/test_config.py`

**Interfaces:**
- Produces:
  - `app.core.config.load_dotenv(path: Path) -> dict[str, str]`：讀 `KEY=VALUE` 行，略過空行和 `#` 開頭；檔案不存在回空 dict（決策 7）
  - `app.core.config.Settings`（dataclass）：`database_url: str`、`host_database_url: str`、`test_database_url: str`、`schedule_day_index_to_iso_weekday: dict[int, int]`，預設 `{1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7}`（Task 6 依結論改，寫在程式裡，不從環境變數讀）。值的來源：`os.environ` 優先，其次 repo 根目錄 `.env`
  - `app.core.config.get_settings() -> Settings`（`functools.lru_cache`）
  - `app.core.clock.TAIPEI = ZoneInfo("Asia/Taipei")`
  - `app.db.session.get_engine(url: str | None = None) -> Engine`、`app.db.session.get_session() -> Iterator[Session]`（FastAPI dependency；測試用 `app.dependency_overrides` 換掉）
  - `app.main.create_app() -> FastAPI`；模組層 `app = create_app()`
  - `GET /health` → `{"status": "ok", "db": "ok" | "error", "latest_gps_at": null}`（Task 2 換成 `HealthResponse`，Task 5 填 `latest_gps_at`）

- [ ] **Step 1: 建 `pyproject.toml`**：依賴 `fastapi`、`uvicorn[standard]`、`pydantic>=2`、`sqlalchemy>=2`、`geoalchemy2`、`alembic`、`psycopg[binary]>=3`、`httpx`；`[project.optional-dependencies] dev = ["pytest"]`。在 Python 3.12 venv 跑 `pip install -e ".[dev]"`，再 `pip freeze --exclude-editable > requirements.lock`。

- [ ] **Step 2: 寫失敗的測試**

```python
# backend/tests/test_health.py
def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["db"] in {"ok", "error"}

# backend/tests/core/test_logging.py
import logging

def test_access_log_has_no_query_string(client, caplog):
    caplog.set_level(logging.INFO, logger="garbagego.access")
    client.get("/health?lat=24.123456&lon=120.654321")
    assert "/health" in caplog.text
    assert "24.123456" not in caplog.text and "120.654321" not in caplog.text
```

```python
# backend/tests/core/test_config.py
def test_load_dotenv_skips_comments(tmp_path):
    p = tmp_path / ".env"
    p.write_text("# note\n\nA=1\nB=x=y\n", encoding="utf-8")
    assert load_dotenv(p) == {"A": "1", "B": "x=y"}

def test_load_dotenv_missing_file(tmp_path):
    assert load_dotenv(tmp_path / "nope.env") == {}
```

`client` fixture（`conftest.py`）：`TestClient(create_app())`。

- [ ] **Step 3: 跑測試確認失敗**

Run: `pytest tests/test_health.py tests/core/test_logging.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'app.main'`）

- [ ] **Step 4: 實作**
  - `app/core/logging.py`：`AccessLogMiddleware`，logger `garbagego.access`，格式 `"{method} {path} {status} {ms}ms"`，`path` 只用 `request.url.path`。
  - `/health` 的 `db`：透過 `get_session` 執行 `SELECT 1`；任何例外回 `"error"`，**不回 500**（資料庫掛了也要看得到 `/health`）。

- [ ] **Step 5: 跑測試確認通過**

Run: `pytest -v`
Expected: 4 passed（還沒開資料庫時 `db` 為 `"error"`，測試仍通過）

- [ ] **Step 6: Docker Compose**
  - `db`：`postgis/postgis:16-3.4`，`restart: unless-stopped`，volume `pgdata`，掛 `./db/init:/docker-entrypoint-initdb.d`，port `127.0.0.1:5432:5432`，環境變數來自 `.env`。
  - `api`：build `./backend`，`command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log`，`env_file: .env`，`depends_on: [db]`，`restart: unless-stopped`，port `127.0.0.1:8000:8000`。
  - `db/init/01-test-db.sql`：`CREATE DATABASE garbagego_test;`
  - `.env.example`：`POSTGRES_USER=`、`POSTGRES_PASSWORD=`、`POSTGRES_DB=garbagego`、`DATABASE_URL=postgresql+psycopg://USER:PASS@db:5432/garbagego`、`HOST_DATABASE_URL=postgresql+psycopg://USER:PASS@localhost:5432/garbagego`、`TEST_DATABASE_URL=postgresql+psycopg://USER:PASS@localhost:5432/garbagego_test`。
  - `Dockerfile`：`python:3.12-slim`；`pip install -r requirements.lock`，再 `pip install --no-deps .`。

- [ ] **Step 7: 驗證整個環境**

Run（repo 根目錄）：`copy .env.example .env`（填入密碼）→ `docker compose up -d --build` → `curl.exe http://localhost:8000/health`
Expected: `{"status":"ok","db":"ok","latest_gps_at":null}`；`docker compose logs api` 裡只有 `GET /health 200 …ms` 這種行，沒有 uvicorn 預設的 access log。

- [ ] **Step 8: Commit**

```bash
git add backend/ docker-compose.yml .env.example db/init/
git commit -m "feat(backend): add FastAPI skeleton with Docker Compose and health check"
```

---

### Task 2: API 合約（`schemas.py`）與假資料 endpoints

**負責：** 架構師（和前端一起對規格）

**白話：** 先講好「App 問什麼、後端回什麼」。這週後端回的都是寫死的假資料，前端照著做畫面，不用等真的邏輯。

**Files:**
- Create: `backend/app/api/schemas.py`、`backend/app/api/fixtures.py`、`backend/app/api/{stops,recommendations,routes,chat}.py`
- Modify: `backend/app/main.py`（掛 routers、exception handlers）、`backend/app/api/health.py`（改用 `HealthResponse`）
- Test: `backend/tests/api/test_contract.py`

**Interfaces:**
- Consumes: Task 1 `create_app()`、`TAIPEI`
- Produces（`app.api.schemas`；欄位名稱就是前後端合約，之後要改先通知前端）：

| Model | 欄位 |
|---|---|
| `GeocodeLevel`（str Enum） | `exact`、`approx_suffix`、`approx_base_number`、`approx_nearby_number` |
| `WasteKind`（str Enum） | `general`、`recycle` |
| `EtaStatus`（str Enum） | `live`、`schedule_only`、`stale`、`passed`、`no_data` |
| `ScheduleSlot` | `kind: WasteKind`、`start: time`、`end: time` |
| `StopCandidate` | `id: int`、`area: str`、`village: str`、`address: str`、`lat: float`、`lon: float`、`geocode_level: GeocodeLevel`、`today_slots: list[ScheduleSlot]`、`distance_m: int` |
| `WeeklySlot` | `weekday: int`（ISO：1=星期一…7=星期日）、`kind: WasteKind`、`start: time`、`end: time` |
| `StopDetail` | `id`、`area`、`village`、`address`、`lat`、`lon`、`geocode_level`（同上）、`car_licence: str`、`weekly: list[WeeklySlot]` |
| `EtaEstimate` | `status: EtaStatus`；`eta`、`eta_low`、`eta_high`、`data_time`、`scheduled_start`、`scheduled_end`：`datetime \| None`；`method: str \| None` |
| `WalkEstimate` | `duration_s: int`、`distance_m: int`、`method: Literal["valhalla", "fallback"]` |
| `RecommendationRequest` | `lat: float`（-90～90）、`lon: float`（-180～180）、`at: datetime \| None = None`、`deadline: datetime \| None = None`、`radius_m: int = 500`（100～2000） |
| `RecommendationItem` | `stop: StopCandidate`、`walk: WalkEstimate`、`eta: EtaEstimate`、`slack_s: int \| None`、`feasible: bool`、`risks: list[str]`（值只能是 `gps_stale`、`schedule_only`、`approx_location`、`walk_fallback`）、`reason: str` |
| `RecommendationResponse` | `at: datetime`、`primary: RecommendationItem \| None`、`alternatives: list[RecommendationItem]`（最多 2）、`message: str \| None` |
| `WalkRoute` | `method`、`duration_s`、`distance_m`（同 `WalkEstimate`）、`coordinates: list[tuple[float, float]]`（`[lon, lat]`） |
| `ChatRequest` | `message: str`（1～500 字）、`lat: float`、`lon: float`、`at: datetime \| None = None` |
| `ChatResponse` | `reply: str`、`tool_results: list[dict]`、`at: datetime` |
| `HealthResponse` | `status: Literal["ok"]`、`db: Literal["ok", "error"]`、`latest_gps_at: datetime \| None` |
| `ErrorBody` / `ErrorResponse` | `code: str`、`message: str` / `error: ErrorBody` |

Endpoints（第 1 週全部回 `fixtures.py` 的資料；`at` 沒給時用現在的臺北時間）：

| Endpoint | 參數 | 回傳 | 之後換成真的 |
|---|---|---|---|
| `GET /stops/nearby` | `lat`、`lon`、`radius`（預設 500，100～2000）、`at` | `list[StopCandidate]` | 後端 A |
| `GET /stops/{stop_id}` | — | `StopDetail`；不在假資料 → 404 `stop_not_found` | 後端 A |
| `GET /stops/{stop_id}/eta` | `at` | `EtaEstimate`；不在假資料 → 404 `stop_not_found` | 後端 B |
| `POST /recommendations` | `RecommendationRequest` | `RecommendationResponse` | 架構師 |
| `GET /routes/walk` | `from_lat`、`from_lon`、`to_lat`、`to_lon` | `WalkRoute` | 後端 A |
| `POST /chat` | `ChatRequest` | `ChatResponse`（固定假回答，`tool_results=[]`） | 架構師 |

- [ ] **Step 1: 寫失敗的測試**

```python
# backend/tests/api/test_contract.py
def test_nearby_returns_candidates(client):
    r = client.get("/stops/nearby", params={"lat": 24.1477, "lon": 120.6736})
    assert r.status_code == 200
    assert {"id", "address", "lat", "lon", "geocode_level", "today_slots", "distance_m"} <= set(r.json()[0])

def test_recommendation_shape(client):
    r = client.post("/recommendations", json={"lat": 24.1477, "lon": 120.6736})
    body = r.json()
    assert r.status_code == 200
    assert body["primary"]["eta"]["status"] in {"live", "schedule_only", "stale", "passed", "no_data"}
    assert len(body["alternatives"]) <= 2

def test_at_param_is_echoed(client):
    r = client.post("/recommendations", json={"lat": 24.1477, "lon": 120.6736, "at": "2026-11-23T11:00:00Z"})
    assert r.json()["at"] == "2026-11-23T19:00:00+08:00"

def test_datetimes_have_taipei_offset(client):
    r = client.post("/recommendations", json={"lat": 24.1477, "lon": 120.6736})
    assert r.json()["at"].endswith("+08:00")

def test_invalid_lat_returns_error_format(client):
    r = client.get("/stops/nearby", params={"lat": 999, "lon": 120.6})
    assert r.status_code == 422
    assert set(r.json()) == {"error"}
    assert set(r.json()["error"]) == {"code", "message"}
    assert r.json()["error"]["code"] == "validation_error"

def test_unknown_stop_404(client):
    r = client.get("/stops/999999999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "stop_not_found"

def test_walk_route_coordinates_are_lon_lat(client):
    r = client.get("/routes/walk", params={"from_lat": 24.1477, "from_lon": 120.6736, "to_lat": 24.15, "to_lon": 120.68})
    lon, lat = r.json()["coordinates"][0]
    assert 119 < lon < 123 and 21 < lat < 26

def test_stop_eta_shape(client):
    stop_id = client.get("/stops/nearby", params={"lat": 24.1477, "lon": 120.6736}).json()[0]["id"]
    r = client.get(f"/stops/{stop_id}/eta")
    assert r.status_code == 200
    assert r.json()["status"] in {"live", "schedule_only", "stale", "passed", "no_data"}
    assert {"eta", "eta_low", "eta_high", "data_time", "scheduled_start", "scheduled_end", "method"} <= set(r.json())

def test_openapi_lists_all_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/health", "/stops/nearby", "/stops/{stop_id}", "/stops/{stop_id}/eta", "/recommendations", "/routes/walk", "/chat"} <= set(paths)
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `pytest tests/api -v`
Expected: FAIL（404 或 import error）

- [ ] **Step 3: 實作**
  - `fixtures.py`：3 個臺中車站附近的假收運點（1 個 `exact`、1 個 `approx_nearby_number`、1 個只有表定時段）；推薦結果 1 筆可行的主推薦 + 1 筆備案（`risks` 含 `schedule_only`）。
  - `main.py` exception handlers：`RequestValidationError` → 422 `validation_error`；`HTTPException` → 原狀態碼，`code` 取 `detail`。
  - 所有輸出的 datetime 先轉成 `TAIPEI` 再序列化（共用一個 Pydantic serializer，不要每個 model 各寫一次）。

- [ ] **Step 4: 跑測試確認通過**

Run: `pytest -v`
Expected: 全部 passed

- [ ] **Step 5: 和前端對規格**：`docker compose up -d --build` 後打開 `http://localhost:8000/docs` 一起看。要改欄位就回 Step 1 先改測試。

- [ ] **Step 6: Commit**

```bash
git add backend/app backend/tests/api
git commit -m "feat(api): add v0 API contract with fixture responses"
```

---

### Task 3: 資料表與 migration

**負責：** 後端 A

**白話：** 建 4 張表：收運點、每週時段、GPS 紀錄、實際到點紀錄。同一台車同一個時間的 GPS 只存一次。

**Files:**
- Create: `backend/app/db/models.py`、`backend/alembic.ini`、`backend/app/db/migrations/env.py`、`backend/app/db/migrations/versions/0001_initial.py`
- Modify: `backend/tests/conftest.py`（加 `db_engine`、`db_session`）、`docker-compose.yml`（`api` 啟動前先 migrate）、`docs/architecture/backend-architecture.md` §5
- Test: `backend/tests/db/test_schema.py`

**Interfaces:**
- Consumes: Task 1 `get_engine`
- Produces（`app.db.models`）：

| Table | 欄位 | 約束 / 索引 |
|---|---|---|
| `collection_stops` | `id` int PK、`source_index` int、`area` text、`village` text、`caption` text、`task_type` text、`car_licence` text NULL（84004 有 6 筆空白）、`geom` geometry(Point,4326) NULL、`geocode_source` text NULL（`local`／`tgos`／`manual`）、`geocode_level` text NULL（`exact`／`approx_suffix`／`approx_base_number`／`approx_nearby_number`／`suspect`）、`source_dataset_at` timestamptz | `source_index` UNIQUE；`geom` GiST |
| `collection_schedules` | `id` PK、`stop_id` FK → `collection_stops.id`、`day_index` smallint（1–7，**84004 原始 `d1`～`d7`**）、`kind` text（`general`／`recycle`）、`start_time` time、`end_time` time | (`stop_id`, `day_index`, `kind`) UNIQUE |
| `vehicle_observations` | `id` bigint PK、`car` text、`line_id` text、`observed_at` timestamptz、`collected_at` timestamptz、`geom` geometry(Point,4326)、`speed` int NULL、`over_speed` bool NULL、`location_text` text、`source` text（`api`／`historical`）、`raw` jsonb | (`car`, `observed_at`) UNIQUE；`observed_at` B-tree；`geom` GiST |
| `stop_arrivals` | `id` PK、`stop_id` FK、`car` text、`service_date` date、`arrived_at` timestamptz、`method` text | (`stop_id`, `car`, `service_date`) UNIQUE |

- 測試 fixtures：`db_engine`（session scope）對 `TEST_DATABASE_URL` 跑 `alembic upgrade head`；`db_session` 每個測試開一個 transaction，結束時 rollback。
- **和 spec 的差異（架構師決定）：** spec §5 寫 `weekday`，這裡改存 `day_index`（84004 原始值），轉成星期幾交給 `Settings.schedule_day_index_to_iso_weekday`。這樣 Task 6 的結論出來前，匯入不用等。

- [ ] **Step 1: 寫失敗的測試**

```python
# backend/tests/db/test_schema.py
from sqlalchemy import inspect, text

def test_tables_exist(db_engine):
    names = set(inspect(db_engine).get_table_names())
    assert {"collection_stops", "collection_schedules", "vehicle_observations", "stop_arrivals"} <= names

def test_observation_unique_car_time(db_session):
    sql = text("INSERT INTO vehicle_observations (car, observed_at, collected_at, geom, source, raw) "
               "VALUES ('KED-1385', '2026-11-03 19:39:53+08', now(), ST_SetSRID(ST_MakePoint(120.5, 24.2), 4326), 'api', '{}') "
               "ON CONFLICT (car, observed_at) DO NOTHING")
    db_session.execute(sql)
    db_session.execute(sql)
    assert db_session.execute(text("SELECT count(*) FROM vehicle_observations")).scalar() == 1

def test_stop_geom_nullable(db_session):
    db_session.execute(text("INSERT INTO collection_stops (source_index, area, village, caption, task_type, car_licence) "
                            "VALUES (0, '中區', '中華里', '中華路一段143號', '沿街', '312-UX')"))
    assert db_session.execute(text("SELECT geom IS NULL FROM collection_stops")).scalar() is True
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `docker compose up -d db`，再 `pytest tests/db -v`
Expected: FAIL（表不存在）

- [ ] **Step 3: 實作** models 與 `0001_initial`（第一行 `CREATE EXTENSION IF NOT EXISTS postgis`）。`docker-compose.yml` 的 `api.command` 改成 `sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log"`（這行在容器內的 sh 執行，不受 PowerShell 限制）。

- [ ] **Step 4: 跑測試確認通過**

Run: `pytest -v`
Expected: 全部 passed

- [ ] **Step 5: 更新 spec**：`backend-architecture.md` §5 的 `weekday` 改成 `day_index`，加一句「轉成星期幾由設定決定，見 `docs/research/opendata-api-check.md` §10」。

- [ ] **Step 6: Commit**

```bash
git add backend/ docker-compose.yml docs/architecture/backend-architecture.md
git commit -m "feat(db): add initial PostGIS schema and migrations"
```

---

### Task 4: 84004 收運點與座標匯入

**負責：** 後端 A

**白話：** 把 2 萬個收運點、每週時段、算好的座標放進資料庫。地址對不上就整批不寫，避免座標配錯點。

**Files:**
- Modify: `scripts/geocode/match.py:142-150`（迴圈抽成 `build_results`，每列加 `source_index`）
- Modify: `scripts/geocode/village_check.py`（計算抽成函式；多一個輸出 `suspects.csv`）
- Modify: `scripts/geocode/test_match.py`
- Create: `backend/app/modules/__init__.py`、`backend/app/modules/ingestion/{__init__,stops}.py`
- Test: `backend/tests/ingestion/test_stops.py`、`backend/tests/ingestion/fixtures/`（小份 `pts.json`、`geocode.csv`、`suspects.csv`）

**Interfaces:**
- Consumes: Task 3 `collection_stops`、`collection_schedules`、`db_session`
- Produces:
  - `match.build_results(pts: list[dict], codes: dict, by_key: dict, by_prefix: dict) -> list[dict]`：每列多一個 `source_index`（= 該筆在 84004 陣列中的位置，從 0 起），放在第一欄
  - `village_check.find_suspects(rows: list[dict], cent_by_village: dict, threshold_m: float = 3000) -> list[tuple[int, int]]`：回傳 `(source_index, 距離公尺)`；CLI 多一個參數：`python -I -X utf8 village_check.py <addr_csv> <all_csv> <suspects_out_csv>`，輸出欄位 `source_index,distance_m`
  - `app.modules.ingestion.stops.parse_schedule(record: dict) -> list[tuple[int, str, time, time]]`：從 `g_d{i}_time_s/e`（`general`）、`r_d{i}_time_s/e`（`recycle`）攤平成 `(day_index, kind, start, end)`；空字串跳過；不是合法 `HH:MM` 就跳過該時段
  - `ImportReport`（dataclass）：`stops: int`、`with_geom: int`、`suspects: int`、`schedules: int`、`skipped_slots: int`
  - `import_stops(session, stops: list[dict], geocode_rows: dict[int, dict], suspects: set[int], dataset_at: datetime) -> ImportReport`
  - `file_sha256(path: Path) -> str`
  - CLI：`python -m app.modules.ingestion.stops --stops <84004.json> --geocode <all.csv> --expect-sha256 <值> [--suspects <suspects.csv>] [--dataset-at <ISO 時間>] [--allow-new-dataset]`，連 `HOST_DATABASE_URL`，成功後 commit，印出 `ImportReport` 和 sha256
  - 匯入規則：
    - `import_stops` 不 commit（決策 8）。
    - `--stops` 檔的 sha256 不等於 `--expect-sha256` → 印出實際值並結束（exit 1），什麼都不寫；加 `--allow-new-dataset` 才繼續（決策 2，等於換版本，要先整批重建）。
    - `car_licence` 是空字串 → 存 `NULL`，收運點照樣匯入。
    - 以 `source_index` upsert，重跑結果相同；時段先刪該點舊的再寫入。
    - `geocode_rows[i]["caption"]` 必須等於 `stops[i]["caption"]`，不同就 `ValueError("caption mismatch at source_index i")`，整批不寫入（防止座標對錯列）。
    - 有座標 → `geom`、`geocode_source="local"`、`geocode_level` 取 `level`。
    - 在 `suspects` 內 → 仍存 `geom`，但 `geocode_level="suspect"`（推薦時排除）。
    - 沒座標 → `geom`、`geocode_*` 為 NULL。

- [ ] **Step 1: 寫失敗的測試**

```python
# scripts/geocode/test_match.py 新增
def test_build_results_carries_source_index():
    pts = [{"area": "中區", "village": "中華里", "task_type": "沿街", "caption": "中華路一段143號"},
           {"area": "中區", "village": "中華里", "task_type": "沿街", "caption": "中華路一段145號"}]
    rows = build_results(pts, {}, {}, {})
    assert [r["source_index"] for r in rows] == [0, 1]
    assert list(rows[0])[0] == "source_index"

def test_find_suspects_threshold():
    rows = [{"source_index": "0", "lon": "120.68", "lat": "24.14", "village": "中華里", "village_ok": "False"},
            {"source_index": "1", "lon": "120.68", "lat": "24.14", "village": "中華里", "village_ok": "True"}]
    cents = {"中華里": [(120.68, 24.18)]}          # 約 4.4 km
    assert [i for i, _ in find_suspects(rows, cents)] == [0]
```

```python
# backend/tests/ingestion/test_stops.py
import pytest
from datetime import time
from sqlalchemy import text
from app.modules.ingestion.stops import parse_schedule, import_stops, run_cli

def test_parse_schedule_flattens_days():
    rec = {"g_d1_time_s": "15:25", "g_d1_time_e": "15:30", "g_d2_time_s": "", "g_d2_time_e": "",
           "r_d1_time_s": "15:25", "r_d1_time_e": "15:30"}
    assert parse_schedule(rec) == [(1, "general", time(15, 25), time(15, 30)),
                                   (1, "recycle", time(15, 25), time(15, 30))]

def test_parse_schedule_skips_bad_time():
    assert parse_schedule({"g_d1_time_s": "25:99", "g_d1_time_e": "15:30"}) == []

def test_import_counts_and_null_geom(db_session, small_inputs):      # fixture：3 筆，1 筆沒座標
    report = import_stops(db_session, *small_inputs)
    assert (report.stops, report.with_geom) == (3, 2)

def test_import_is_idempotent(db_session, small_inputs):
    import_stops(db_session, *small_inputs)
    import_stops(db_session, *small_inputs)
    assert db_session.execute(text("SELECT count(*) FROM collection_stops")).scalar() == 3

def test_duplicate_rows_both_imported(db_session, dup_inputs):       # fixture：兩筆內容完全相同
    assert import_stops(db_session, *dup_inputs).stops == 2

def test_suspect_level(db_session, small_inputs):
    stops, geo, _, at = small_inputs
    import_stops(db_session, stops, geo, {0}, at)
    assert db_session.execute(text("SELECT geocode_level FROM collection_stops WHERE source_index = 0")).scalar() == "suspect"

def test_caption_mismatch_aborts(db_session, small_inputs):
    stops, geo, sus, at = small_inputs
    geo[0] = {**geo[0], "caption": "別的地址"}
    with pytest.raises(ValueError, match="caption mismatch"):
        import_stops(db_session, stops, geo, sus, at)

def test_blank_car_licence_is_null(db_session, small_inputs):   # fixture 第 3 筆 car_licence 為 ""
    import_stops(db_session, *small_inputs)
    assert db_session.execute(text("SELECT car_licence IS NULL FROM collection_stops WHERE source_index = 2")).scalar() is True

def test_cli_refuses_unexpected_sha256(tmp_path, small_files):
    code = run_cli(["--stops", small_files.stops, "--geocode", small_files.geocode, "--expect-sha256", "0" * 64])
    assert code == 1
```

`run_cli(argv: list[str]) -> int` 是 CLI 的進入點（`main` 呼叫它），方便測試；`small_files` 是 fixture 檔案路徑。

`small_inputs` / `dup_inputs`（`backend/tests/ingestion/conftest.py`）：從 `fixtures/` 讀檔，回傳 `(stops, geocode_rows, suspects, dataset_at)`。

- [ ] **Step 2: 跑測試確認失敗**

Run（repo 根目錄）：`python -I -X utf8 scripts/geocode/test_match.py`；（`backend/`）`pytest tests/ingestion/test_stops.py -v`
Expected: 新測試 FAIL

- [ ] **Step 3: 實作** `build_results`、`find_suspects`、`ingestion/stops.py`。`main()` 改成呼叫這兩個函式，原本的報表輸出不變。

- [ ] **Step 4: 跑測試確認通過**

Run: 同 Step 2
Expected: 全部 passed（含原本 8 個 geocode 測試）

- [ ] **Step 5: 跑真資料**：照 `docs/research/geocoding-local-match-trial.md` 下載資料，重跑 `match.py`、`village_check.py`（加 `suspects.csv` 參數），再跑匯入 CLI（第一次用 `--allow-new-dataset`）。
Expected: `stops=20090`、`with_geom` 約 19,216、`suspects` 約 81、`skipped_slots` 至少 1（84004 有 1 筆時間格式異常）。若和文件不同，**記錄實際值**到 `geocoding-local-match-trial.md`，不要改成文件上的數字。同時記下 84004 的**下載日期和 sha256**——這就是 v1 鎖定的版本（決策 2），之後重跑都要帶 `--expect-sha256`。

- [ ] **Step 6: Commit**

```bash
git add scripts/geocode backend/app/modules backend/tests/ingestion docs/research/geocoding-local-match-trial.md
git commit -m "feat(ingestion): import 84004 collection points with local geocodes"
```

---

### Task 5: GPS 解析與歷史 GPS 匯入；`/health` 顯示最新 GPS 時間

**負責：** 後端 B

**白話：** 把舊程式收了一個月的 GPS（約 98 萬筆）放進資料庫。每筆都要知道「車在幾點、在哪裡」和「我們幾點抓到的」。壞掉的檔案跳過，不要整批停掉。

**前置條件：** 後端 B 先找到舊收集程式存的快照（`opendata-api-check.md` §3：每次抓取都整份存下），並確認**每份快照的抓取時間存在哪裡**（檔名或 SQLite 欄位）。把快照整理成「每份一個 JSON 檔、內容是 83558 API 的原始陣列」，旁邊放一份 `collected_at.csv`（欄位 `file,collected_at`，ISO 8601 含時區），放在部署主機的資料夾（不進 Git）。**找不到抓取時間就停下來告訴架構師，不要用檔案修改時間代替**（決策 1：檔案一複製，修改時間就變了）。

**Files:**
- Create: `backend/app/modules/ingestion/gps.py`
- Modify: `backend/app/core/clock.py`、`backend/app/api/health.py`
- Test: `backend/tests/ingestion/test_gps.py`、`backend/tests/ingestion/fixtures/snapshots/`（`ok.json`：含 `SAMPLE` 的陣列；`empty.json`：`[]`；`not_array.json`：`{}`；`broken.json`：`[{`；`collected_at.csv`：4 個檔都有時間）。`snapshot_dir` fixture 把這個資料夾複製到 `tmp_path` 再用

**Interfaces:**
- Consumes: Task 3 `vehicle_observations`、`db_session`；Task 1 `TAIPEI`、`get_session`
- Produces:
  - `app.core.clock.parse_taichung_time(s: str) -> datetime`：`YYYYMMDDTHHMMSS` → 帶 `TAIPEI` 時區的 datetime；格式錯 `ValueError`
  - `Observation`（dataclass）：`car: str`、`line_id: str`、`observed_at: datetime`、`lon: float`、`lat: float`、`speed: int | None`、`over_speed: bool | None`、`location_text: str`、`raw: dict`
  - `parse_observation(raw: dict) -> Observation | None`：以下回 `None`——缺 `car` 或 `time`、時間格式錯、`X`/`Y` 不是數字、經度不在 119–123 或緯度不在 21–26（這也擋掉 (0,0)）。`OverSpeed` 的 `"Y"`/`"N"` → `True`/`False`，其他 → `None`
  - `insert_observations(session, obs: Iterable[Observation], collected_at: datetime, source: str) -> int`：回傳實際新增筆數（`ON CONFLICT (car, observed_at) DO NOTHING`）
  - `GpsImportReport`（dataclass）：`files`、`skipped_files`、`parsed`、`rejected`、`inserted`
  - `import_snapshot_dir(session, path: Path) -> GpsImportReport`：`collected_at` 讀 `path / "collected_at.csv"`；`source="historical"`；空陣列、不是陣列、JSON 壞掉都算 `skipped_files`；**有任何 `.json` 檔在 `collected_at.csv` 裡找不到** → 開始寫入前就 `ValueError`，訊息列出檔名
  - `insert_observations`、`import_snapshot_dir` 不 commit（決策 8）
  - CLI：`python -m app.modules.ingestion.gps <snapshot_dir>`，連 `HOST_DATABASE_URL`，成功後 commit
  - 每 5 分鐘抓 API 的 worker 是第 3 週的事；但到時候要直接用 `parse_observation` 和 `insert_observations`。

- [ ] **Step 1: 寫失敗的測試**

```python
# backend/tests/ingestion/test_gps.py
import pytest
from datetime import datetime
from sqlalchemy import text
from app.core.clock import TAIPEI, parse_taichung_time
from app.modules.ingestion.gps import parse_observation, insert_observations, import_snapshot_dir

SAMPLE = {"lineid": "24908", "car": "KED-1385", "time": "20261103T193953", "location": "臺中市龍井區 龍昌路",
          "X": "120.504613", "Y": "24.210510", "SpeedValue": "37", "OverSpeed": "N"}
NOW = datetime(2026, 11, 22, 12, 0, tzinfo=TAIPEI)

def test_parse_time_is_taipei():
    assert parse_taichung_time("20261103T193953").isoformat() == "2026-11-03T19:39:53+08:00"

def test_parse_observation_ok():
    o = parse_observation(SAMPLE)
    assert (o.car, o.lon, o.lat, o.speed, o.over_speed) == ("KED-1385", 120.504613, 24.21051, 37, False)

@pytest.mark.parametrize("patch", [{"time": "2026-11-03"}, {"X": "abc"}, {"X": "0", "Y": "0"}, {"Y": "40"}, {"car": ""}])
def test_parse_observation_rejects(patch):
    assert parse_observation({**SAMPLE, **patch}) is None

def test_insert_dedupes(db_session):
    o = parse_observation(SAMPLE)
    assert insert_observations(db_session, [o, o], collected_at=NOW, source="api") == 1

def test_import_skips_empty_and_invalid_files(db_session, snapshot_dir):
    r = import_snapshot_dir(db_session, snapshot_dir)
    assert (r.files, r.skipped_files, r.inserted) == (4, 3, 1)

def test_collected_at_comes_from_csv(db_session, snapshot_dir):
    import_snapshot_dir(db_session, snapshot_dir)      # collected_at.csv：ok.json → 2026-11-03T19:42:00+08:00
    got = db_session.execute(text("SELECT collected_at FROM vehicle_observations")).scalar()
    assert got.isoformat() == "2026-11-03T19:42:00+08:00"

def test_missing_collected_at_aborts(db_session, snapshot_dir):
    (snapshot_dir / "extra.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="extra.json"):
        import_snapshot_dir(db_session, snapshot_dir)

def test_health_shows_latest_gps(client_with_db, db_session):
    insert_observations(db_session, [parse_observation(SAMPLE)], collected_at=NOW, source="api")
    assert client_with_db.get("/health").json()["latest_gps_at"] == "2026-11-03T19:39:53+08:00"
```

`client_with_db`（`conftest.py`）：`TestClient`，並用 `app.dependency_overrides[get_session]` 換成同一個 `db_session`，這樣看得到還沒 commit 的資料。

- [ ] **Step 2: 跑測試確認失敗**

Run: `pytest tests/ingestion/test_gps.py -v`
Expected: FAIL

- [ ] **Step 3: 實作** `gps.py`、`parse_taichung_time`；`/health` 用 `SELECT max(observed_at) FROM vehicle_observations` 填 `latest_gps_at`。

- [ ] **Step 4: 跑測試確認通過**

Run: `pytest -v`
Expected: 全部 passed

- [ ] **Step 5: 跑真資料**：在部署主機匯入全部歷史快照。
Expected: `inserted` 接近 `docs/research/opendata-api-check.md` 記錄的 980,775 筆（加上之後新收的）；`/health` 的 `latest_gps_at` 是最近一次收集時間。把實際數字記到 `opendata-api-check.md`。

- [ ] **Step 6: Commit**

```bash
git add backend/app backend/tests/ingestion docs/research/opendata-api-check.md
git commit -m "feat(ingestion): parse 83558 GPS records and import historical snapshots"
```

---

### Task 6: 確認 `d1`～`d7` 對應星期幾

**負責：** 後端 B
**前置條件：** Task 4、Task 5 的真資料都已匯入。

**白話：** 84004 的時段寫成 `d1`～`d7`，沒說是星期幾。我們用 GPS 看「排在 `d1` 的點，車子都是星期幾真的經過」，就知道答案。

**⚠️ 風險：** Task 6 排在後端 B 這條線的最後面，要等 Task 3、4、5 都做完。Task 4 慢一天，這裡就慢一天。週五還沒做完，後端 B 當天回報，在週五整合會上決定怎麼辦。

**Files:**
- Create: `backend/analysis/weekday_mapping.sql`
- Modify: `docs/research/opendata-api-check.md`（§10 寫結論）、`backend/app/core/config.py`（預設值）
- Test: `backend/tests/core/test_config.py`（Task 1 已建立，這裡加一個測試）

**方法：** 抽 1,000 個有座標、`geocode_level <> 'suspect'` 的收運點（`ORDER BY md5(id::text) LIMIT 1000`，結果可重現）。對每個點的每個一般垃圾時段，看它的 `car_licence` 那台車，有沒有在「時段前後 30 分鐘內、離點 100 公尺內」出現（`ST_DWithin(o.geom::geography, s.geom::geography, 100)`）。用 100 公尺是因為 2026-11-06 以前每 10 分鐘才抓一次（`opendata-api-check.md` §3），50 公尺太容易漏掉；這裡只比較各星期的相對高低，不求準確到點。日期用 `observed_at AT TIME ZONE 'Asia/Taipei'`。

輸出 7×7 表：列是 `day_index`（1–7），欄是 ISO 星期（`EXTRACT(ISODOW FROM ...)`），格子是「排了這個 `day_index` 的點，在該星期有被車經過的天數比例」。

- [ ] **Step 1: 寫 SQL**，產出上面那張 7×7 表。

- [ ] **Step 2: 執行**

Run（repo 根目錄）：
```
docker compose cp backend/analysis/weekday_mapping.sql db:/tmp/weekday_mapping.sql
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/weekday_mapping.sql'
```
Expected: 7×7 表。若 `d1`=星期一，對角線的比例應明顯高於同一列其他格。

- [ ] **Step 3: 記錄結論**：在 `opendata-api-check.md` §10 貼表、寫抽樣方法、結論與限制（例如週三只有 41 筆、週日 0 筆，樣本少）。結論只寫表上看得到的。
  - WHEN 表上看不出明顯的對角線 THEN 先維持 `d1`＝星期一，§10 寫「未確認」，並通知架構師。

- [ ] **Step 4: 先寫測試再改設定**

```python
# backend/tests/core/test_config.py
def test_day_index_mapping_matches_research():
    # 數值照 opendata-api-check.md §10 的結論填
    assert get_settings().schedule_day_index_to_iso_weekday == {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7}
```

照結論改測試裡的期望值和 `config.py` 的預設值，跑 `pytest tests/core -v` 確認通過。

- [ ] **Step 5: Commit**

```bash
git add backend/analysis backend/app/core/config.py backend/tests/core docs/research/opendata-api-check.md
git commit -m "docs(research): verify 84004 day index to weekday mapping"
```

---

### Task 7: 部署主機與 `https` 網址

**負責：** 後端 A（主機）＋ 後端 B（GPS 收集搬家）

**白話：** 找一台不關機的電腦跑後端，再用 Cloudflare 開一個 `https` 網址，讓手機連得到。重開機後要自己恢復，每週備份一次資料庫。

**Files:**
- Modify: `docker-compose.yml`（加 `tunnel` 服務）
- Create: `docs/architecture/deploy-host.md`（主機操作手冊）
- Modify: `docs/architecture/project-structure.txt`（加 `deploy-host.md`）

**Interfaces:**
- Produces: 前端能連的 `https://<隨機名稱>.trycloudflare.com`。`tunnel` 服務：映像 `cloudflare/cloudflared:<當天鎖定的版本>`，`command: tunnel --no-autoupdate --url http://api:8000`，`profiles: ["tunnel"]`，`restart: unless-stopped`。

- [ ] **Step 1: 主機設定**：Docker Desktop 設開機自動啟動；Windows 電源設定「睡眠：永不」；clone repo、建 `.env`、`docker compose up -d --build`。
- [ ] **Step 2: 開 tunnel**：`docker compose --profile tunnel up -d`，用 `docker compose logs tunnel` 找網址。把「網址長什麼樣、在 log 哪一行」寫進手冊。
- [ ] **Step 3: 驗證**：用**手機行動網路**（不是同一個 Wi-Fi）打開 `https://<網址>/health`。
Expected: `{"status":"ok","db":"ok",...}`
- [ ] **Step 4: 重開機測試**：重開主機，不手動操作，等 3 分鐘。
Expected: `/health` 自己恢復。網址可能變了，手冊寫下怎麼拿新網址、怎麼通知前端。
- [ ] **Step 5: GPS 收集搬家**（後端 B，**第一天就做**，不用等其他 Task）：把現有收集程式搬到這台主機，設成開機自動執行（Windows 工作排程器）；隔天確認快照檔有持續增加。第 3 週 worker 上線並確認有寫入後，才停掉舊程式。
- [ ] **Step 6: 備份**：手冊寫下每週備份指令並實際做一次：
```
docker compose exec db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > /tmp/backup.sql.gz'
docker compose cp db:/tmp/backup.sql.gz ./backups/backup-YYYYMMDD.sql.gz
```
Expected: 檔案存在且大小不是 0。`backups/` 加進 `.gitignore`（改設定檔，先問架構師）。
- [ ] **Step 7: Commit**

```bash
git add docker-compose.yml docs/architecture/deploy-host.md docs/architecture/project-structure.txt
git commit -m "chore(deploy): add Cloudflare quick tunnel and deploy host runbook"
```

---

## 順序與並行

| 誰 | 順序 |
|---|---|
| 架構師 | Task 1 → Task 2（Task 1 合進 `main` 後，其他人才開工） |
| 後端 A | Task 7 Step 1 主機設定（可馬上做）→ 等 Task 1 → Task 3 → Task 4 → Task 7 其餘 |
| 後端 B | Task 7 Step 5 GPS 搬家（**第一天**）→ 等 Task 3 → Task 5 → 等 Task 4 → Task 6 |

每個 Task 開自己的分支（例如 `feat/backend-skeleton`），完成後開 PR 合進 `main`。
