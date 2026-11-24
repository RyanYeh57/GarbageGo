# 開工前準備清單

> **建立日期：** 2026-11-22
> **用途：** 4 位組員第一次開工前要準備的東西。照著打勾，每項都有「怎麼確認好了」。
> **相關：** 誰做什麼看 `docs/plans/2026-11-22-backend-work-plan.md`。

## 1. 所有人

| ☐ | 準備 | 怎麼確認好了 |
|---|---|---|
| ☐ | GitHub 帳號，請架構師加進 `RyanYeh57/GarbageGo` | 打得開 repo 頁面，而且能推自己的分支上去 |
| ☐ | Git | PowerShell 打 `git --version` 有出版本號 |
| ☐ | 把 repo 抓下來 | `git clone https://github.com/RyanYeh57/GarbageGo.git` |
| ☐ | 讀一頁工作計畫 | `docs/plans/2026-11-22-backend-work-plan.md` |

## 2. 後端的人（架構師、後端 A、後端 B）

### 2.1 要裝的

| ☐ | 準備 | 為什麼 | 怎麼確認好了 |
|---|---|---|---|
| ☐ | **Python 3.12** | 和 Docker 裡的版本一樣 | `py -3.12 --version` 顯示 `Python 3.12.x` |
| ☐ | **Docker Desktop** | 跑資料庫和後端。Windows 要開 WSL2，第一次裝可能要重開機 | `docker compose version` 有出版本號 |
| ☐ | 編輯器（例如 VS Code） | 寫程式 | — |

### 2.2 第一次跑起來

在 repo 根目錄，用 PowerShell：

```powershell
copy .env.example .env          # 打開 .env，填 POSTGRES_USER、POSTGRES_PASSWORD，和網址裡的 USER:PASS
docker compose up -d --build
curl.exe http://localhost:8000/health
```

**成功的樣子：** `{"status":"ok","db":"ok","latest_gps_at":null}`

在自己電腦跑測試（虛擬環境放在 repo 外面，才不會被 commit）：

```powershell
py -3.12 -m venv $env:USERPROFILE\venvs\garbagego
& $env:USERPROFILE\venvs\garbagego\Scripts\Activate.ps1
cd backend
pip install -r requirements.lock
pip install -e . --no-deps
pytest -q
```

**成功的樣子：** 最後一行是 `5 passed`（之後測試會變多）。

> ⚠️ `.env` 裡有密碼，**不要 commit**。`.gitignore` 已經擋住了，但 `git add` 時還是看一下。

### 2.4 本機資料（第 1 週週五之後）

資料包做好之前，本機資料庫是空的，這是正常的。做好之後：

| ☐ | 步驟 |
|---|---|
| ☐ | 跟架構師要 Google Drive 連結，下載 `garbagego-devdata-v1.zip` |
| ☐ | 解壓到 `%USERPROFILE%\garbagego-data\`（**放 repo 外面**，才不會被 commit） |
| ☐ | 照下面匯入 |

先開好 §2.2 的虛擬環境，再用 PowerShell：

```powershell
docker compose up -d --build     # api 啟動時會自動建資料表
cd backend
$D = "$env:USERPROFILE\garbagego-data\garbagego-devdata-v1"
python -m app.modules.ingestion.stops --stops $D\84004.json --geocode $D\geocode\all.csv --suspects $D\geocode\suspects.csv --expect-sha256 <README.txt 裡的值>
python -m app.modules.ingestion.gps $D\gps
curl.exe http://localhost:8000/health
```

**成功的樣子：** `/health` 的 `latest_gps_at` 落在 `README.txt` 寫的那一天。

資料包升版（例如 `v2`）時，本機重建：

```powershell
docker compose down -v           # ⚠️ 會刪掉整個資料庫，只能在自己電腦用，部署主機不能用
docker compose up -d --build
```

然後重做上面的匯入（把 `v1` 改成新版號）。

> 1 天份 GPS 只夠開發用。`d1`～`d7` 驗證、ETA 評估要在部署主機用全部資料跑。

### 2.3 各自要多準備的

| 誰 | ☐ | 準備 | 注意 |
|---|---|---|---|
| 後端 A | ☐ | **一台不關機的電腦**當部署主機 | Docker Desktop 設開機自動啟動；Windows 電源設定「睡眠：永不」 |
| 後端 A | ☐ | 臺中市門牌資料（約 157 MB） | 下載方式見 `docs/research/geocoding-local-match-trial.md` |
| 後端 B | ☐ | **舊的 GPS 快照檔** | 之前收集程式存下來的那些 |
| 後端 B | ☐ | **每份快照是幾點抓的** | 檔名或 SQLite 裡要找得到。⚠️ **找不到就先告訴架構師**，不能用檔案修改時間代替 |
| 後端 B | ☐ | 把 GPS 收集程式搬到部署主機 | **第一天就做**。晚一天搬，就少一天資料 |
| 後端 A | ☐ | 共用資料包：收運點與座標 | Task 4 Step 5b，週五前 |
| 後端 B | ☐ | 共用資料包：1 天份 GPS | Task 5 Step 5b，週五前 |
| 架構師 | ☐ | Claude API Key | 第 3 週才用。只放在 `.env`，不能寫進程式 |

## 3. 前端的人

### 3.1 要裝的

| ☐ | 準備 | 為什麼 | 怎麼確認好了 |
|---|---|---|---|
| ☐ | **Android Studio**（最新版） | 寫 App：Kotlin + Jetpack Compose | 能建一個空的 Compose 專案並跑起來 |
| ☐ | **一支 Android 手機**（或模擬器） | 實機才測得到定位和 `https` 網址 | 手機開「開發人員選項 → USB 偵錯」，Android Studio 看得到這支手機 |
| ☐ | **Docker Desktop、Python 3.12** | 在自己電腦跑後端和資料庫 | 照 §2.1 裝，跑過 §2.2 的第一段（`pytest` 那段可以跳過），資料包出來後做 §2.4 |

**App 連自己電腦的後端：**

| 用什麼 | 後端網址 |
|---|---|
| 模擬器 | `http://10.0.2.2:8000` |
| 實機（USB） | 先跑 `adb reverse tcp:8000 tcp:8000`，再用 `http://127.0.0.1:8000` |

> 本機是 `http`，部署主機是 `https`。App 的**開發版**要允許 `http`。

### 3.2 地圖要知道的

| ☐ | 項目 | 內容 |
|---|---|---|
| ☐ | 地圖套件 | MapLibre Native Android + maplibre-compose（還在 0.x，**版本要鎖定**） |
| ☐ | 底圖網址 | `https://wmts.nlsc.gov.tw/wmts/EMAP/default/GoogleMapsCompatible/{z}/{y}/{x}` |
| ☐ | 圖磚大小 | 這個底圖是 **256×256**，`rememberRasterTileSource` 預設是 512，**要改成 256** |
| ☐ | 標示來源 | 地圖上一定要顯示「**內政部國土測繪中心**」 |
| ☐ | 寄信問授權 | 問國土測繪中心：放大到 **16 級以上**、**用在手機 App** 可不可以。問到之前，先限制最多 15 級 |

### 3.3 第 1 週先做

| ☐ | 做什麼 | 注意 |
|---|---|---|
| ☐ | App 骨架、地圖顯示底圖 | — |
| ☐ | **設定頁可以改後端網址** | Cloudflare 網址重開就會變，不能寫死在 App 裡 |
| ☐ | 接假資料 API | 等架構師做完 Task 2，再照 `http://<後端網址>/docs` 的規格接 |

## 4. 架構師要先做的（其他人才能開工）

| ☐ | 事情 |
|---|---|
| ☐ | 把 3 位組員加進 GitHub repo |
| ☐ | 建組內 Google Drive 資料夾，給後端 A、後端 B 上傳權限，其他人可下載 |
| ☐ | merge PR #9（計畫文件） |
| ☐ | 在自己電腦裝好 Docker，跑過 §2.2，確認 Task 1 沒問題 |
| ☐ | 決定組員分工名單、Demo 日期、誰的電腦當部署主機，填進 `backend-work-plan.md` |
