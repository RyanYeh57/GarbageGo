# 工作項目總表（重新分配用）

> **建立日期：** 2026-11-25
> **狀態：** 待分配。「誰」那欄還是空的，架構師填好後再同步回各文件。
> **來源：** `docs/plans/2026-11-22-backend-work-plan.md`、`docs/architecture/backend-architecture.md` §8、`docs/plans/2026-11-22-week1-backend-foundation.md` Task 7、`docs/architecture/p1-tech-selection.md` §6。
> **分配原則：** 同一組（同一個字母）盡量給同一個人。一支 API 由一個人從 HTTP 做到模組和測試，拆給不同人容易互相卡住。

## 0. 要先決定的事

| 編號 | 事情 | 為什麼急 |
|---|---|---|
| 0-1 | **Demo 日期** | 時程要從這天倒推 |
| 0-2 | **誰的電腦當部署主機** | 不急：大家先各自開發，最後再部署。Demo 前要定 |
| 0-3 | API 規格的 4 個缺口：可疑座標、沒座標、沒車號、TGOS 座標的品質等級 | 做 App 的人要知道怎麼顯示。細節見 `docs/architecture/api-reference.md` §4 |

## A. 部署主機

> 各自開發期間用不到，**最後再做**。GPS 舊收集程式一直在另一位組員的電腦上收資料，不用急著搬。

| 編號 | 工作 | 誰 |
|---|---|---|
| A1 | 主機設定：Docker 開機自動啟動、電腦不睡眠、跑起後端 | |
| A2 | 開 Cloudflare `https` 網址，用手機測，做重開機測試，寫操作手冊 | |
| A3 | **跟負責收集的組員拿最新的 `garbage.db` 並匯入**（ETA 評估和 Demo 前要做；目前資料庫裡的 GPS 只到 2026-11-19 06:52，是舊的複製檔） | |
| A4 | 每週備份資料庫 | |
| A5 | 每天看 `/health`，GPS 斷了就處理 | |
| A6 | GPS worker 放進 Docker，取代舊程式 | |

## B. 資料

| 編號 | 工作 | 誰 |
|---|---|---|
| B1 | 資料包 `garbagego-devdata-v1.zip` 上傳組內 Google Drive，在群組通知（也提醒大家把 `.env` 的 `localhost` 改成 `127.0.0.1`） | |
| B3 | Demo 前檢查 84004 有沒有出新版本（`DESIGN.md` §11 第 11 點） | |

## C. 找點與步行

| 編號 | 工作 | 誰 |
|---|---|---|
| C1 | `GET /stops/nearby` 改用真資料 | |
| C2 | `GET /stops/{id}` 改用真資料 | |
| C3 | 算步行時間（Valhalla；Valhalla 掛了就用直線粗估） | |
| C4 | `GET /routes/walk` 步行路線 | |
| C5 | 實測 Valhalla 一次算 5–10 個點 | |

## D. GPS 與 ETA

| 編號 | 工作 | 誰 |
|---|---|---|
| D1 | 判斷垃圾車「到點」→ 寫進 `stop_arrivals` | |
| D2 | 只用表定時間的 ETA（Schedule Baseline） | |
| D3 | `GET /stops/{id}/eta` 改成真的：即時 GPS → 歷史 → 表定 | |
| D4 | ETA 評估（MAE、RMSE、趕上率），只能用測試段資料（`DESIGN.md` §8.1） | |

## E. 推薦與對話

| 編號 | 工作 | 誰 |
|---|---|---|
| E1 | `POST /recommendations` 真的推薦邏輯 + 測試 | |
| E2 | 申請 Claude API Key，把 Key 的名稱寫進 `.env.example`（不放真的 Key） | |
| E3 | `POST /chat`：讓 Claude 呼叫我們的工具 | |
| E4 | 整合、文件、Demo 腳本 | |

## F. App

| 編號 | 工作 | 誰 |
|---|---|---|
| F1 | App 骨架、地圖底圖、接假資料、設定頁可以改後端網址 | |
| F2 | 寄信問國土測繪中心：能不能放大到 16 級以上、能不能用在 App | |
| F3 | 附近點列表、地圖標點、推薦畫面 | |
| F4 | 步行路線畫線；顯示資料時間和風險（**包含新的 `historical` 狀態**） | |
| F5 | 對話畫面 | |

## G. 全組

| 編號 | 工作 | 誰 |
|---|---|---|
| G1 | 每週五合進 `main`，App → 後端 → 資料庫整條跑一次 | 全部 |
| G2 | Demo 備援資料、修 bug | |
| G3 | Demo 彩排 | 全部 |

## H. 小 bug

| 編號 | 工作 | 誰 |
|---|---|---|
| H1 | 匯入參數 `--allow-new-dataset` 沒有檢查資料表是不是空的 | |
| H2 | `/health` 的最新 GPS 時間，沒擋掉「未來的時間」 | |

## 已經做完（不用分）

| 項目 |
|---|
| Task 1–6：後端骨架、假資料 API、資料表、匯入收運點、匯入舊 GPS、確認 `d1`～`d7` |
| `GET /health` 已經是真的 |
| API 文件、本機門牌比對、TGOS 申請、資料包製作 |
| B2 TGOS 補座標：上傳檔、篩選與匯入程式（PR #14），補 263 點，共 19,479 點有座標、611 點沒有 |

## 參考：舊的分法

| 組 | 舊負責人 |
|---|---|
| F | anjyuelee |
| E | RyanYeh57 |
| A、C | hobartXIII |
| D | Ian1114 |
