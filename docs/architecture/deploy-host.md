# 部署主機操作手冊

> 對應：`docs/plans/2026-11-22-week1-backend-foundation.md` Task 7、`backend-architecture.md` §2.1。
> 狀態：**Implemented / Unverified**（`https` 網址電腦端與手機行動網路都已測通；重開機測試要等正式部署主機，見 §7）。

**白話：** 後端跑在一台不關機的電腦上。Cloudflare Tunnel 從這台電腦**主動連出去**，換到一個 `https` 網址，手機就連得到。所以**不用固定 IP**，也不用開防火牆或設定路由器。

---

## 1. 第一次設定（每台主機做一次）

| ☐ | 做什麼 | 怎麼確認 |
|---|---|---|
| ☐ | 裝 Docker Desktop | `docker compose version` 會印出版本號 |
| ☐ | Docker Desktop → Settings → General → 勾 **Start Docker Desktop when you sign in to your computer** | 重開機登入後，工作列出現 Docker 圖示 |
| ☐ | Windows 設定 → 系統 → 電源 → 插電時的「睡眠」設 **永不** | `powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE` 的「AC 電源設定索引」是 `0x00000000` |
| ☐ | clone repo，在 repo 根目錄建 `.env`（欄位看 `.env.example`；**不要 commit**） | `git status` 看不到 `.env` |
| ☐ | 第一次啟動：`docker compose up -d --build` | `curl http://127.0.0.1:8000/health` 回 `"status":"ok"` |

**⚠️ Docker Desktop 要等 Windows 登入後才會啟動。** 重開機後如果停在登入畫面，後端不會起來。要嘛每次重開機後登入一次，要嘛設 Windows 自動登入（較不安全，請主機擁有者自己決定）。

---

## 2. 開 `https` 網址

`tunnel` 服務放在 `profiles: ["tunnel"]`，平常 `docker compose up -d` **不會**開它，要另外加 `--profile tunnel`：

```
docker compose --profile tunnel up -d
```

只要開過一次，它就跟 `db`、`api` 一樣是 `restart: unless-stopped`，重開機後會自己回來。

---

## 3. 找網址

```
docker compose logs tunnel
```

找這一段（網址每次都不一樣）：

```
INF +--------------------------------------------------------------------------------------------+
INF |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
INF |  https://angle-gig-jan-freeze.trycloudflare.com                                            |
INF +--------------------------------------------------------------------------------------------+
```

PowerShell 只抓網址那一行：

```
docker compose logs tunnel | Select-String "https://.*trycloudflare.com"
```

**容器重啟過好幾次時會有好幾行，用最後一行。**

剛拿到網址時可能要等幾秒到半分鐘才連得上。

---

## 4. 測試網址

| 測什麼 | 怎麼做 | 成功長這樣 |
|---|---|---|
| 健康檢查 | 打開 `https://<網址>/health` | `{"status":"ok","db":"ok","latest_gps_at":...}` |
| API 說明頁 | 打開 `https://<網址>/docs` | Swagger UI 頁面 |
| 外網 | **手機關掉 Wi-Fi，用行動網路**打開上面兩個網址 | 結果跟上面一樣 |

用同一個 Wi-Fi 測不算，因為那可能沒有真的繞到外網。

---

## 5. 網址變了怎麼辦

免帳號的 Quick Tunnel，**只要 `tunnel` 容器重啟，網址就會換**。重開機、Docker 重啟、`docker compose restart tunnel` 都會。

1. 照 §3 拿新網址。
2. 用 §4 確認新網址能用。
3. 把新網址貼到組內群組，通知前端。
4. 前端在 App 設定頁改「後端網址」，不用重新打包。

要網址永遠不變，需要 Cloudflare 帳號＋自己的網域（named tunnel）。目前不做。

---

## 6. 日常檢查與注意事項

| 項目 | 做法 |
|---|---|
| 每天看一次 | 打開 `/health`。`latest_gps_at` 超過 30 分鐘沒更新就處理（第 3 週 worker 上線後才有意義） |
| 看服務狀態 | `docker compose --profile tunnel ps`，三個服務都要是 `Up` |
| 關掉公開網址 | `docker compose stop tunnel`（`db`、`api` 照跑，只剩本機能連） |
| 網址是公開的 | 拿到網址的人都能打 API 和 `/docs`。**只貼在組內群組，不要貼到公開的地方** |
| 服務條款 | Cloudflare 說免帳號 tunnel **沒有保證不斷線**，只適合測試與 Demo |
| 學校／公司網路 | 有些網路會擋 `cloudflared` 往外連。`logs tunnel` 一直出現連線錯誤時，改用手機熱點或家裡網路 |

### 每週備份（尚未實測）

```
docker compose exec db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > /tmp/backup.sql.gz'
docker compose cp db:/tmp/backup.sql.gz ./backups/backup-YYYYMMDD.sql.gz
```

檔案存在且大小不是 0 才算成功，然後複製到雲端硬碟。`backups/` 還沒加進 `.gitignore`（要先問架構師），在那之前**不要** `git add` 這個資料夾。

---

## 7. 測試紀錄

| 日期 | 主機 | 測什麼 | 結果 |
|---|---|---|---|
| 2026-11-25 | 試用主機（非正式部署主機） | `cloudflared` `2026.10.7` 建立 Quick Tunnel；電腦端 `curl https://<網址>/health` | ✅ `{"status":"ok","db":"ok",...}`；`/docs` 回 200 |
| 2026-11-25 | 試用主機 | 手機行動網路打 `/health` | ✅ 正常 |
| 2026-11-25 | 試用主機 | 重開機後不手動操作服務，3 分鐘內 `/health` 自己恢復 | ⏭️ 不測：試用主機的 Docker 自動啟動（關）和睡眠（插電 15 分鐘）不能改，必定失敗。**改到正式部署主機做完 §1 後再測** |
