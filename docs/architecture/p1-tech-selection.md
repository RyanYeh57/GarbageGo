# P1 技術選型決策單

> **狀態：** Decided（D1–D5 已於 2026-11-22 全部決定；部分事項仍待查證，見各節）
> **建立日期：** 2026-11-13
> **對應：** `DESIGN.md` §10 Technology Decisions、工作清單 P1
> **用途：** 列出開工前必須先定的技術選項。每題最多兩個選項，附建議。決定後填「決定」欄，再同步更新 `DESIGN.md` §10。

## 0. 總覽

| # | 要決定什麼 | 選項 A | 選項 B | 建議 | 決定 | 卡住的工作 |
|---|---|---|---|---|---|---|
| D1 | 地圖組合（底圖＋步行路線） | 台灣底圖組合：MapLibre（Android）+ 國土測繪中心「臺灣通用電子地圖」+ Valhalla 步行路線（OSM 路網） | Google 組合：Maps SDK for Android + Routes API | **A** | ☑ **A**（2026-11-22） | W3、W9 |
| D2 | 地址轉座標（Geocoding） | ~~TGOS 批次比對~~ | ~~Nominatim~~ | — | ☑ **已定：臺中市 GIS 門牌資料本地比對為主，TGOS 為備援**（2026-11-16） | W2（最卡） |
| D3 | 前端框架 | ~~React + Vite~~ | ~~Vue + Vite~~ | — | ☑ **已定：Android App（Jetpack Compose + MVVM）**（2026-11-16） | W9 |
| D4 | LLM 供應商 | Claude API（Haiku 5.5） | Gemini API 免費額度 | **A** | ☑ **A**（2026-11-22） | W7 |
| D5 | 後端與資料庫（確認既有方向） | 照舊：Python + FastAPI + PostgreSQL/PostGIS，Docker Compose | 改用其他 | **A** | ☑ **A**（2026-11-22） | P2、全部 |

**不在 P1 決定（YAGNI，等資料再說）：**

- ETA 模型技術：等 W4 Baseline 做完，由後端 B 依資料品質提案。
- RAG／Vector Store：W8 是選做，先不選。

> **重要：D1 和 Google 綁在一起。** Google 條款不允許把 Google 的地址座標或路線結果用在非 Google 地圖上（見 D1 說明）。D2 已定用臺中市門牌資料（非 Google），所以 D2 不受 D1 影響；但 D1 選 A 時，任何地方都不能改用 Google Geocoding 或 Routes。

---

## D1. 地圖組合（底圖＋步行路線）

需求：每次查詢要算使用者走到 5–10 個候選點的步行時間，並在 Android App 顯示地圖（D3 已定 Android）。**必須支援台中市。**

| 比較 | A. 台灣底圖組合 | B. Google 組合 |
|---|---|---|
| 底圖 | 國土測繪中心「臺灣通用電子地圖」（NLSC EMAP），用 MapLibre Native Android + `maplibre-compose` 以 raster tile 顯示 | Google Maps SDK for Android + `maps-compose` |
| 步行路線 | Valhalla（開源路線引擎）的 pedestrian 模式，用 FOSSGIS 公開伺服器，路網來自 OSM。App 只呼叫我們的後端，由後端呼叫 Valhalla | Google Routes API |
| 台中實測（2026-11-13） | ✅ 底圖：台中車站 z16 圖磚回 HTTP 200，是真的地圖圖片<br>✅ 步行：台中車站附近兩點，Valhalla 算出 1.44 km、1,102 秒（約時速 4.7 km），路名有建國路、雙十路一段、太平路，還有斑馬線和樓梯路段；OSRM foot 算出 1.41 km、1,134 秒，兩者差約 3% | 未實測 |
| 費用 | 免費，不用申請 Key | Maps SDK 要 API Key 與啟用帳單的 Google Cloud 專案。Routes Essentials 每月免費 10,000 次，之後每 1,000 次 $5；Pro 等級每月免費 5,000 次，之後 $10。**要開帳單帳戶** |
| 授權／條款 | 底圖：政府資料開放授權條款第 1 版，「無需申請」；標示「內政部國土測繪中心」並註明授權條款，未標示視為未授權。⚠️ data.gov.tw 資料集只寫 zoom 15 以下的開放圖磚，EMAP 本體到 zoom 19；**zoom 16 以上是否同授權、手機 App 是否適用，官方頁面都沒寫（未驗證）**。步行：要標示 OSM 出處，帶可辨識的 User-Agent | **Google 結果不能搭配非 Google 地圖**（Service Specific Terms 3.3、1.3、11.3，存檔版 2024-05-15，現行版未能讀取） |
| 限制 | 步行伺服器是**公開示範機**，最多每秒 1 次、不能大量使用，沒有服務保證。底圖不能大量抓下來放在自己的伺服器 | 依上列額度 |
| 路網品質 | OSM 路網。台中車站一帶實測完整；郊區可能較不完整（Chen 2026 抽樣研究），**沒有找到台中人行道完整度的數據** | 通常較完整 |
| 風險 | 示範機可能變慢或停用；`maplibre-compose` 仍是 0.x 版，minor 版更新可能不相容，**版本要鎖死** | 綁定 Google，D2 也必須用 Google |

**已定 A（2026-11-22）。** 理由：

- 底圖和步行路線都在台中實測過，可以用。
- 免費、不用申請，也不會被 Google 條款綁住 D2。

**A 的備案（依序）：**

1. 示範機不夠用時，改用 Docker 在自己電腦跑 Valhalla，只載台灣的 OSM 資料，就沒有次數限制。
2. 也可以改用 OpenRouteService。要先申請 Key，新網址是 `api.heigit.org/openrouteservice`。但 2026-10 有人回報它的 foot-walking 會逾時，官方 10-21 說已修好，**我們沒有實測**。

**看過但不建議的台灣服務：**

| 服務 | 為什麼不用 |
|---|---|
| TGOS 地圖 API | 是它自己的 JS 地圖（網頁用），沒有 Android 版；Key 綁網域；個人只能用一般圖資 |
| osmdroid（Android 地圖套件） | GitHub 已於 2024-11-20 封存，不再更新；也沒有官方 Compose 版 |
| TGOS 步行路徑（`walkRoute`） | 標示「試辦」，只能透過 TGOS 的 JS API 用，查不到額度和條款，沒有實測 |
| 國土測繪中心 | 只有底圖，沒找到路線 API |
| TDX（交通部） | 是大眾運輸路線規劃，沒看到純步行 API |

**不管選哪個都要做：**

- **一次查詢只發 1 個請求。** 候選點有 5–10 個時，逐點查要等 5–10 秒。要改用 Valhalla 的 matrix（一對多）功能一次算完，這個**還沒實測**，W3 開工時先測。
- 步行路線 API 失敗時，降級成「直線距離 × 繞路係數 ÷ 步行速度」，畫面標示「粗估」。
- 步行結果要做 cache（暫存），減少 API 呼叫次數。

**D1 選 A 時，Android 端要注意：**

- 後端直接回傳解碼後的路線座標，App 用 `maplibre-compose` 的 `LineLayer` 畫線。Valhalla 的 encoded polyline 精度是 6（不是 Google 的 5），後端解碼要用 1e6（**未查官方文件，W3 實測確認**）。
- EMAP 圖磚是 256 px，`rememberRasterTileSource` 預設 `tileSize = 512`，要改成 256（**推論，未實測**）。
- Android 9 以上預設擋 `http://`。開發時後端若用 http，用 `network_security_config.xml` 只對開發網域開放，不要全域開。圖磚一律用 `https://`。
- 地圖畫面要顯示底圖與 OSM 的出處標示。
- 不做大範圍離線預載底圖。
- 寄信問國土測繪中心：zoom 16 以上與手機 App 是否可用、有無用量上限。拿到書面回覆前，App 先限制最大 zoom 15 或接受風險。

---

## D2. 地址轉座標（Geocoding）

需求：84004 收運點共 **20,090 筆只有地址、沒有座標**，要一次轉好存進 PostGIS（見 `docs/research/opendata-api-check.md`）。有些地址是地標寫法（例如「某某路 123 號前」），轉換成功率一定不是 100%。

**已定（2026-11-16）：臺中市 GIS 門牌資料本地比對為主，TGOS 為備援。**

本地比對：把臺中市官方門牌座標資料下載進 PostGIS，用 84004 的地址去對門牌，對到就拿它的座標。不用呼叫外部 API。

> 注意：83558 是垃圾車 GPS 動態資料，**不是**門牌資料。本地比對要用下表的門牌資料集。83558 之後可用來抽查轉出的座標是否合理（車有沒有在附近停）。

**門牌資料來源（2026-11-16 核對）：**

| 項目 | 臺中市 GIS 門牌點位（建議用） | 舊版 110 年 2 月 |
|---|---|---|
| 資料集 | <https://data.gov.tw/dataset/169806>（臺中市政府數位發展局） | <https://data.gov.tw/dataset/137998>（臺中市政府民政局） |
| 內容 | 每月一版，最新 115 年 1 月；data.gov.tw 上的檔案只是**目錄 CSV**，真正月檔在目錄裡的 Google Drive 連結 | 約 1,191,053 點（第三方記載，未驗證） |
| 座標 | TWD97 與 WGS84 都有（TWD97 是否為 EPSG:3826 未驗證） | 同左 |
| 欄位 | 13 欄，已拆欄：村里、鄰、街、路段、地區、巷、弄、號、TWD97、WGS84；數字為全形（2026-11-16 下載 115 年 1 月版確認，1,316,674 筆） | 已拆欄：村里、鄰、街_路段、地區、巷、弄、號、座標；**沒有完整地址字串** |
| 授權 | 政府資料開放授權條款第 1 版，免費、免登入 | 同左 |

**流程：**

1. 下載最新門牌月檔，匯入 PostGIS。
2. 把 84004 的地址拆成「路段、巷、弄、號」，再正規化（見下方）。
3. 對門牌資料比對。對到 → 存座標，標記來源 `local`。
4. 對不到的 → 送 TGOS 批次比對，標記來源 `tgos`。
5. 還是對不到 → 列清單人工處理，**不可自己猜座標**。
6. 先抽 200 筆跑完整流程，看成功率，再跑全部 20,090 筆。

**試跑結果（2026-11-16，Implemented / Unverified）：** 全部 20,090 筆中 **95.6% 本地就拿到座標**（完全相同 88.9%），約 **4.4%（874 筆）要送 TGOS 或人工**。座標還沒人工核對。細節見 `docs/research/geocoding-local-match-trial.md`，腳本在 `scripts/geocode/`。

**比對要處理的坑：**

| 坑 | 處理 |
|---|---|
| 全形數字（例如「３２２巷」）、中文數字（例如「十一樓」） | 轉成半形阿拉伯數字；但**路名裡的中文數字不能轉**（例如「十七路」） |
| 臺／台 | 兩邊都統一成「臺」 |
| 「123 號前」「旁」「對面」 | 去掉後綴再比對到 123 號。座標會有幾公尺偏差，要標記為近似 |
| 「之 1」、樓層、室、附 | 先去掉樓層和室；「之」格式多種，要測試 |
| 亂碼列（■、?、∮） | 匯入時排除 |
| 舊門牌、里鄰調整 | 門牌檔只有最新門牌。對不到時可查臺中市民政局新舊門牌對照（<https://www.civil.taichung.gov.tw/21953/Nodelist>，格式未驗證） |
| 資料版本落差 | 84004 的資料時間不明，門牌用最新月檔 |

**TGOS 備援：**

- 流程：註冊 TGOS 會員 → 申請「批次門牌地址比對服務」→ 審核後拿 API Key；每日 1 萬筆，72 小時內寄下載連結（<https://www.gov.tw/News_Content_2_371654>，頁面更新 2026-11-02）。
- 只送本地對不到的地址，量應遠小於 20,090 筆。
- 風險：**學生或個人能不能申請：未驗證**；有部落格說舊的批次 API Key 已失效、要改申請「全國門牌地址定位服務」（未驗證）。申請前先向 TGOS 確認。

**不採用 Nominatim：** OSM 台灣門牌資料較少，準確度可能很差；官方也不鼓勵大量 geocoding。

**為什麼不用 Google Geocoding：** 20,090 筆超過每月免費 10,000 次，超出部分約 $50。而且座標最多只能存 30 天，跟「存進 PostGIS 長期查詢」的設計衝突。

---

## D3. 前端框架

**已定（2026-11-16）：Android App，採用 Jetpack Compose + MVVM。** 原本的 React / Vue 網頁選項不再考慮。

- MVVM：畫面（Compose）只負責顯示，資料與邏輯放在 ViewModel，方便測試。
- 地圖套件隨 D1：選 A 用 MapLibre（`maplibre-compose`），選 B 用 Google `maps-compose`。
- App 只呼叫我們的 FastAPI 後端，不直接呼叫 Valhalla、Geocoding 或 LLM，Key 都留在後端。

---

## D4. LLM 供應商

需求：要支援 Tool Calling（讓 LLM 呼叫我們寫的工具），數字一律來自工具。查詢量是 Demo 等級。

| 比較 | A. Claude API（`claude-haiku-5-5`） | B. Gemini API 免費額度 |
|---|---|---|
| 費用 | 輸入 $0.10、輸出 $0.50（每 100 萬 tokens，2026-11-03 價目）。新帳號有免費試用額度（金額未標示） | 新帳號從免費額度開始，有幾個 Flash 模型標示免費 |
| 限制 | 要儲值；有一般的 rate limit | 免費額度很低，第三方資料說某些 Flash 模型只有 5 次/分、20 次/天（**未驗證**）。官方頁沒寫免費額度能不能用 function calling |
| Tool Calling | 支援 | 支援（免費額度是否可用未確認） |
| 風險 | 要有人出一點錢 | 開發和 Demo 時可能因為額度用完而卡住；Gemini 2.5 系列 2026-12-01 起改導到新模型 |

**已定 A：Claude API（2026-11-22）。** 理由是 Gemini 免費額度太低，會卡開發和 Demo。價格與模型 ID 在 W7 申請 Key 時再到官方頁面確認一次。

> 揭露：本文件由 Claude 協助撰寫，建議 A 可能有偏向疑慮；上表數字均附來源，請自行判斷。

**不管選哪個都要做：**

- **不用 Agent 框架**（例如 LangChain），直接用官方 SDK 的 tool calling（KISS）。
- LLM 呼叫包在一個介面後面，之後要換供應商只改一處（`DESIGN.md` §2.4 Maintainability：外部服務可替換）。
- API Key 放 `.env`，不能進 Git。

---

## D5. 後端與資料庫（確認既有方向）

`DESIGN.md` §3.2、§10 已提出：Modular Monolith（模組化單體，一個後端程式）＋ Python + FastAPI ＋ PostgreSQL/PostGIS，部署用單一應用程式加資料庫。

**已定照舊（A，2026-11-22）。** 補一點：用 Docker Compose 一鍵啟動後端和資料庫，方便 4 個人環境一致。

---

## 6. 決定後要做的事

| 動作 | 誰 | 何時 |
|---|---|---|
| 下載最新臺中市門牌月檔、匯入 PostGIS、抽 200 筆跑本地比對看成功率（D2） | 後端 A 或後端 B | W2 開工時 |
| 申請 TGOS 會員與 API Key（D2 備援），先確認學生能否申請 | 後端 A 或後端 B | **盡快**（審核要時間） |
| 實測 Valhalla matrix 一次算 5–10 點（D1 選 A 時） | 全端或後端 | W3 開工時 |
| 寄信問國土測繪中心 zoom 16 以上與 App 使用授權（D1 選 A 時） | 前端（Android） | 決定後一週內 |
| 做 MapLibre + EMAP 圖磚的最小 Android 試作，確認 `tileSize` 與出處標示（D1 選 A 時） | 前端（Android） | W9 開工前 |
| 申請 LLM API Key | 全端 | W7 前 |
| 把 Key 名稱寫進 `.env.example`（不放真的 Key） | 後端 | P2 |
| 更新 `DESIGN.md` §10 與 Change Log | 主導決定的人 | ✅ 2026-11-22 已更新 |

## 7. 資料來源（核對日期 2026-11-13）

| 項目 | 來源 | 備註 |
|---|---|---|
| Google 價格與免費額度 | <https://developers.google.com/maps/billing-and-pricing/pricing>、<https://developers.google.com/maps/billing-and-pricing/overview> | 頁面無更新日期 |
| Google Geocoding 快取 30 天 | <https://developers.google.com/maps/documentation/geocoding/policies> | 頁面無更新日期 |
| Google 不得搭配非 Google 地圖 | Service Specific Terms 存檔版（Last modified 2024-05-15） | 現行版未能讀取，需再確認 |
| TGOS 批次比對 1 萬筆/日 | <https://www.gov.tw/News_Content_2_371654> | 頁面更新 2026-11-02；個人資格未驗證 |
| 臺中市 GIS 門牌點位（每月一版） | <https://data.gov.tw/dataset/169806>、<https://opendata.taichung.gov.tw/search/50168dd2-4239-4f3e-89cf-f706617f0436> | 2026-11-16 核對；詮釋資料更新 2026-04-20；最新 115 年 1 月；月檔欄位未驗證 |
| 臺中市門牌 110 年 2 月版欄位 | <https://data.gov.tw/dataset/137998> | 詮釋資料更新 2026-06-15 |
| 臺中門牌資料的格式坑 | <https://hackmd.io/@osm-tw/import-taichung-address> | 第三方（OSM 台灣社群），年份未顯示 |
| 內政部門牌資料不整批開放 | <https://data.gov.tw/suggests/80423>、<https://data.gov.tw/suggests/21721> | 舊回覆，日期未驗證 |
| Nominatim 使用規範 | <https://operations.osmfoundation.org/policies/nominatim/> | 規範可能隨時變動 |
| OSM 底圖使用規範 | <https://operations.osmfoundation.org/policies/tiles/> | 無 SLA |
| 臺灣通用電子地圖 WMTS（免費、無需申請） | <https://www.nlsc.gov.tw/NLSC_Content.aspx?n=11987&s=183225>；授權 <https://data.gov.tw/dataset/25108> | 頁面更新 2026-11-12；圖磚網址 `https://wmts.nlsc.gov.tw/wmts/EMAP/default/GoogleMapsCompatible/{z}/{y}/{x}`，最大 zoom 19；2026-11-13 實測 HTTP 200 |
| FOSSGIS OSRM 使用規範 | <https://routing.openstreetmap.de/about.html> | 每秒最多 1 次、要標示出處；2026-11-13 台中實測 HTTP 200 |
| FOSSGIS Valhalla 使用規範 | <https://github.com/valhalla/valhalla/discussions/3373> | 2021 年維護者貼文，可能已過時；2026-11-13 台中實測 HTTP 200 |
| TGOS 地圖 API、步行路徑 | <https://api.tgos.tw/TGOS_MAP_API/docs/site/web/Application>、<https://api.tgos.tw/TGOS_MAP_API/docs/site/web/Route> | 步行路徑標示試辦，未實測 |
| ORS 網址變更、foot-walking 問題 | <https://ask.openrouteservice.org/t/deprecating-api-openrouteservice-org-in-favour-of-api-heigit-org/7912>、<https://ask.openrouteservice.org/t/foot-walking-foot-hiking-hang-on-api-heigit-org-cycling-regular-driving-car-works/8097> | 免費額度未驗證 |
| OSM 台灣路網完整度 | <https://www.frontiersin.org/journals/built-environment/articles/10.3389/fbuil.2026.1857817/full> | 郊區道路抽樣不完整；無台中人行道數據 |
| NLSC EMAP 圖層、zoom 與授權範圍 | <https://wmts.nlsc.gov.tw/wmts>（GetCapabilities）、<https://maps.nlsc.gov.tw/S09SOA/pro/Wmts_ajax_main.jsp>、<https://data.gov.tw/license> | 2026-11-16 核對；data.gov.tw 資料集寫 zoom 15 以下；App 使用與用量上限官方未寫 |
| MapLibre Compose 0.20.0（BSD-3-Clause） | <https://github.com/maplibre/maplibre-compose>、Maven Central `org.maplibre.compose:maplibre-compose` | 2026-10-10 發布；Android 為 Beta；0.x 版可能不相容 |
| MapLibre Native Android | Maven Central `org.maplibre.gl:android-sdk` | Maven 13.7.1（2026-10-15）與 GitHub Releases 標示的 13.5.4 不一致，以 Maven 為準 |
| osmdroid 已封存 | <https://github.com/osmdroid/osmdroid> | 2024-11-20 封存；最後版本 6.1.20 |
| Google maps-compose 9.0.1、需 Key 與帳單 | <https://github.com/googlemaps/android-maps-compose>、<https://developers.google.com/maps/documentation/android-sdk/get-api-key> | 2026-10-08 發布 |
| Android 預設擋 cleartext HTTP | <https://developer.android.com/privacy-and-security/security-config> | Android 9 以上 |
| Claude 價格 | Claude API 官方模型表（2026-11-03）；<https://platform.claude.com/docs/en/about-claude/pricing> | 新用戶有免費試用額度 |
| Gemini 免費額度 | <https://aistudio.google.com/docs/billing>、<https://aistudio.google.com/docs/pricing> | 免費 RPM/RPD 官方未列出 |
