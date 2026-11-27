# Docker 使用說明（組員版）

> **給誰：** 全部組員（後端、前端都要看 §1–§3）。
> **最後更新：** 2026-11-27
> **相關：** 部署主機細節看 `docs/architecture/deploy-host.md`。

用 Docker 一次開好兩樣東西：

| 服務 | 是什麼 | 本機網址 |
|---|---|---|
| `db` | 資料庫（PostgreSQL + PostGIS） | `127.0.0.1:5432` |
| `api` | 後端（FastAPI），啟動時會自動建好資料表 | `http://127.0.0.1:8000` |
| `tunnel`（選用） | Cloudflare 公開 `https` 網址，上線測試用 | 見 §5 |

---

## 1. 先裝好

| ☐ | 裝什麼 | 怎麼確認 |
|---|---|---|
| ☐ | Git | `git --version` 有版本號 |
| ☐ | **Docker Desktop**（Windows 要開 WSL2，第一次裝可能要重開機） | `docker compose version` 有版本號 |
| ☐ | Python 3.12（**要匯入資料或跑測試才需要**） | `py -3.12 --version` |

---

## 2. 下載程式（用 `main`）

第一次：

```powershell
git clone https://github.com/RyanYeh57/GarbageGo.git
cd GarbageGo
```

之後要更新：

```powershell
git switch main
git pull
```

---

## 3. 第一次啟動

在 repo 根目錄：

```powershell
copy .env.example .env
```

打開 `.env`，填這幾個（自己取帳號密碼，只在你電腦用）：

| 欄位 | 填什麼 |
|---|---|
| `POSTGRES_USER`、`POSTGRES_PASSWORD` | 自己取 |
| 3 個網址裡的 `USER:PASS` | 換成上面的帳號密碼 |

> ⚠️ `.env` 有密碼，**不要 commit**（`.gitignore` 已經擋住）。
> ⚠️ 網址要寫 `127.0.0.1`，**不要改成 `localhost`**。寫 `localhost` 的話，Windows 每次連線會卡 10 秒以上。

啟動：

```powershell
docker compose up -d --build
```

第一次會下載映像檔，要等幾分鐘。後端會**等資料庫準備好才啟動**，所以不會一開始就噴錯。

確認：

```powershell
curl.exe http://127.0.0.1:8000/health
```

**成功：** `{"status":"ok","db":"ok","latest_gps_at":null}`

`latest_gps_at` 是 `null`，代表資料庫還是空的，這是正常的。API 說明頁在 <http://127.0.0.1:8000/docs>。

---

## 4. 匯入開發資料（要真資料才做）

1. 跟架構師要 `garbagego-devdata-v1.zip`，解壓到 `%USERPROFILE%\garbagego-data\`（**放 repo 外面**）。
2. 建 Python 虛擬環境（放 repo 外面）：

```powershell
py -3.12 -m venv $env:USERPROFILE\venvs\garbagego
& $env:USERPROFILE\venvs\garbagego\Scripts\Activate.ps1
cd backend
pip install -r requirements.lock
pip install -e . --no-deps
```

3. 匯入（`<sha256>` 抄資料包裡的 `README.txt`）：

```powershell
$D = "$env:USERPROFILE\garbagego-data\garbagego-devdata-v1"
python -m app.modules.ingestion.stops --stops $D\84004.json --geocode $D\geocode\all.csv --suspects $D\geocode\suspects.csv --expect-sha256 <sha256> --dataset-at 2026-11-16T09:21:00+08:00
python -m app.modules.ingestion.gps $D\gps
```

**成功：** `/health` 的 `latest_gps_at` 是 `README.txt` 寫的那一天。

---

## 5. 上線測試（公開 `https` 網址）

給手機或組員從外面連。**不用 Cloudflare 帳號、不用固定 IP。**

```powershell
docker compose --profile tunnel up -d
docker compose logs tunnel | Select-String "https://.*trycloudflare.com"
```

用**最後一行**的網址，等 30 秒左右再測：

| 測什麼 | 怎麼做 | 成功 |
|---|---|---|
| 健康檢查 | 開 `https://<網址>/health` | 和 §3 一樣 |
| API 說明頁 | 開 `https://<網址>/docs` | Swagger 頁面 |
| 外網 | **手機關 Wi-Fi，用行動網路**開上面的網址 | 一樣能開 |

| ⚠️ 注意 | 說明 |
|---|---|
| 網址會變 | `tunnel` 容器一重啟（重開機、重開 Docker）網址就換。換了要重新貼到群組 |
| 網址是公開的 | 拿到的人都能打 API。**只貼在組內群組** |
| 不保證不斷線 | 只適合測試和 Demo |
| 學校網路可能擋 | 連不上就改用手機熱點 |
| 關掉公開網址 | `docker compose stop tunnel`（後端照跑） |

---

## 6. App 連後端（前端）

| 用什麼 | 後端網址 |
|---|---|
| 模擬器 | `http://10.0.2.2:8000` |
| 實機（USB） | 先跑 `adb reverse tcp:8000 tcp:8000`，再用 `http://127.0.0.1:8000` |
| 實機（外網） | §5 的 `https` 網址 |

> 本機是 `http`，App 的開發版要允許 `http`。

---

## 7. 常用指令

| 要做什麼 | 指令 |
|---|---|
| 開 | `docker compose up -d` |
| 拉了新程式後重開 | `docker compose up -d --build` |
| 看狀態 | `docker compose ps`（`db` 要是 `healthy`） |
| 看後端訊息 | `docker compose logs api --tail 50` |
| 關（資料留著） | `docker compose stop` |
| 跑測試 | 進 §4 的虛擬環境，`cd backend`，`pytest -q` |
| **清空資料庫重來** | `docker compose down -v` ⚠️ **整個資料庫會刪掉**，只能在自己電腦用 |

---

## 8. 常見問題

| 看到什麼 | 原因 | 怎麼辦 |
|---|---|---|
| `failed to connect to the docker API` | Docker Desktop 沒開 | 打開 Docker Desktop，等左下角變綠再試 |
| `port is already allocated`（5432 或 8000） | 電腦上已經有別的資料庫或程式占用 | 關掉那個程式，或問架構師 |
| `pytest` 好像當掉 | `.env` 寫了 `localhost` | 改成 `127.0.0.1` |
| `/health` 連不上 | 後端還在啟動，或啟動失敗 | 等 10 秒；還不行就看 `docker compose logs api --tail 50` |
| `api` 一直重啟 | `.env` 的帳號密碼和網址裡的對不上 | 對照 §3 改好，再 `docker compose up -d` |
| 改了 `.env` 密碼後連不上資料庫 | 資料庫第一次建立時就記住舊密碼了 | 改回舊密碼；或 `docker compose down -v` 清空重來 |
| `https` 網址打不開 | 剛開還沒好，或網路擋 | 等 30 秒；還不行換手機熱點 |
