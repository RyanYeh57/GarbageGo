# Related Work：AI 與相關技術

本章整理與 GarbageGo 相關的八篇研究，涵蓋垃圾車與公車預估抵達時間（Estimated Time of Arrival，ETA）、GIS 步行路線與旅行時間，以及大型語言模型（Large Language Model，LLM）的工具使用與 Agent 流程。下文的 Findings 是原作者在各自實驗條件下報告的結果，未經本專題重現；對 GarbageGo 的應用建議則是本章根據文獻與現有設計所作的分析。GarbageGo 相關功能仍為 Planned，尚無本專題的實驗結果。

## 1. 預估抵達時間與車輛行程預測

### 1.1 ETA 的用途與基本概念

ETA 是根據目前可取得的資訊，估計車輛抵達指定地點的時間。對垃圾清運服務而言，民眾需要知道的不只是車輛預定何時抵達，也包括車輛目前的行駛情況，以及自己前往收運點是否還有足夠時間。預定時刻屬於排程資訊，而 ETA 是根據資料與模型產生的估計，兩者都不等同於實際抵達時間。

既有研究使用歷史旅行時間、車輛 GPS、路線、站點及其他影響因素進行預測。Chen 等人以垃圾清運車的站點間行程時間建立預測方法 [B1]；Zhang 等人則以公車 GPS 與行車相關特徵研究到站時間預測 [B2]。由於車輛行駛狀況會變動，預測結果仍存在誤差，使用時應保留資料時間與適當的風險說明。

### 1.2 垃圾清運車相關研究

Chen、Hwang 與 Kung [B1] 針對臺灣民眾於指定地點等待垃圾清運車的情境，提出結合資料分群與特徵選擇的旅行時間預測系統。研究系統包括車載設備、車隊管理伺服器、資料分析伺服器與民眾使用的行動裝置。模型利用歷史站點間行程資訊建立預測；系統接收車輛及查詢資料後，提供垃圾車預估抵達時間。

研究在分群後為各群建立線性迴歸模型，並以先前站點間的實際行程時間預測下一段行程時間；實驗資料為新竹市四月至十月的垃圾車行程紀錄。作者比較有無分群的線性迴歸、神經網路等組合，其分群搭配線性迴歸的方法優於未分群的線性迴歸與神經網路，但並非所有比較組合中準確率最高者。作者同時考量運算時間與應用需求，說明採用較簡單模型的理由 [B1, §3.2–4.1]。

原文另描述系統在新竹市的應用：其 App 可依使用者位置顯示附近收運點，讓使用者選取站點查看預估抵達時間 [B1, §4.2]。這說明垃圾車 ETA 與附近站點查詢已有實際研究；此處僅轉述論文發表時的系統狀態，未確認該 App 目前是否仍在營運。

此研究對 GarbageGo 的參考價值在於垃圾清運領域的路線、站點及歷史行程資料如何支持 ETA。其實驗情境與資料來自新竹；能否套用至臺中，仍需確認臺中資料的更新頻率、歷史紀錄、車輛與站點關聯及實際到點時間是否足夠。

### 1.3 公車或其他車輛的 ETA 相關研究

Zhang 等人 [B2] 使用中國南昌市 220 路公車於 2021 年 10 月 20 日的 GPS 資料研究到站時間預測，以改良 Whale Optimization Algorithm 搜尋 Long Short-Term Memory 模型的超參數，形成 IWOA–LSTM 方法。研究分行車方向與時段分析資料，將溫度、相對濕度與一小時降水量納入天氣特徵；雖然討論道路與交通等影響因素，並非每項因素都被量化為獨立輸入特徵 [B2, §3.3.5–4.2.1]。作者將方法與 BP、LSTM 及 WOA–LSTM 比較，在該案例中報告較佳預測表現。

此研究展示時序資料、影響因素及模型比較可如何用於 ETA 分析，也提供 MAE、RMSE 等評估指標的參考。然而其案例僅使用單一路線、單日資料，不能據此確認跨季節、跨路線或垃圾車情境的效果。公車與垃圾車的停靠目的、停留時間及行駛條件亦不同。LSTM 等方法需要合適的歷史資料，GarbageGo 仍應先確認資料品質，再決定是否有必要採用複雜模型；原文的性能敘述不等於本專題已完成模型重現。

另需注意，原文 §2.3 Step 3 寫到以 LSTM 的「test set mean square error」作為 IWOA 的適應值。依此文字，文中所稱測試集參與了超參數搜尋，因此不能僅憑報告的指標認定模型已通過完全獨立於調參程序的測試。本章將此視為評估設計的限制，不據此判定論文資料虛假；GarbageGo 後續應依專案規範分離訓練、驗證及最終測試資料，避免資料洩漏。

Rawat 等人 [B8] 使用紐約市 MTA SIRI 公車 GPS 資料，選取班次最多的 20 條路線，以加入路線嵌入（route embedding）的 LSTM 預測到站時間，並將預測器放入多代理模擬，讓公車自行決定是否跳站，以減少車輛串連（bus bunching）。作者以各路線的歷史平均 ETA 作為 Baseline，報告 LSTM 的 MAE 約 2.02 分鐘，較 Baseline 的 2.83 分鐘改善約 28.5% [B8, §3.2, §3.10, §4.1]。

此研究與 GarbageGo 的關聯，在於它以歷史平均作為比較基準，與 `DESIGN.md` 規劃的 Historical Statistical Baseline 類似，也處理了 GPS 輪詢缺口的補值問題。但它仍是公車情境；作者亦指出模型只適用於已訓練的路線，序列開頭觀測不足時 ETA 準確度可能較低 [B8]。此外，原文 §3.10 同時描述「依日期排序以避免時間資料洩漏」與「依路線分層切分」，本章無法從文字確認兩者如何搭配，因此對其時間外推能力仍保留判斷。

### 1.4 小結：文獻比較與對 GarbageGo 的啟示

論文 [B1] 以新竹垃圾車歷史行程為基礎，情境較接近本專題；論文 [B2]、[B8] 則以公車 GPS 及 LSTM 探討時序預測，[B8] 並以歷史平均作為 Baseline。這些研究提供不同複雜度的參考，但 [B2] 的單日資料與測試集調參方式、[B8] 的路線限定與資料切分描述，都限制了結果的外推。GarbageGo 預計先評估排程、歷史統計及距離／速度等 Baseline，再視資料條件比較其他方法；這些方法目前仍屬規劃，尚未完成實驗。

推薦時，垃圾車 ETA 還需結合使用者步行時間、資料新鮮度及安全緩衝。若 GPS 過期、站點關聯不明或真實到點時間不足，系統應呈現限制，不能把排程時間視為已驗證的即時預測。

## 2. GIS 路徑規劃與步行時間估計

### 2.1 行人路網與步行時間的基本概念

使用者前往收運點的時間與距離，受到實際可通行路徑、路口連接及個人步行速度等因素影響。兩點之間的直線距離可以作為初步空間篩選的參考，但無法完整反映實際行人路徑。GIS 路網分析可用於描述路徑與可達性；步行時間估計則需要考量路線與速度假設 [B3]、[B4]。

### 2.2 GIS 步行路線規劃相關研究

Al Shammas 等人 [B4] 提出以 GIS 建立行人路線的方法，並將步行舒適度納入路線規劃。研究在西班牙馬德里建立人行道與穿越道路的路網，結合遮蔭、溫度及使用者偏好，計算步行舒適度並產生路線。研究透過陰影計算及不同條件下的路線分析進行驗證。

對 GarbageGo 而言，這篇研究說明路線分析需要考量人行道與路口連接，對估計使用者如何走到收運點具有參考價值。但該研究主要目標是步行舒適度，而非直接驗證前往垃圾收運點的步行時間；研究亦指出樹木遮蔭及部分行人穿越資訊不足。GarbageGo 是否納入舒適度因素仍須考量資料可用性，目前不預設實作。

### 2.3 步行時間估計相關研究

Fink 等人 [B3] 於 2024 年發表 Helsinki 地區 2023 年旅行時間矩陣，估計網格位置之間以步行、自行車、大眾運輸及汽車移動所需時間。研究以 `r5py`／R5 與 OpenStreetMap 等資料計算路線。汽車與大眾運輸部分考量不同時段；步行部分則設定一般與較慢兩種速度，並使用包含道路穿越等成本的路網計算，不能將整份多運具矩陣的時段變化全部解讀成步行時間的動態預測。

資料集採門到門的行程時間概念，例如大眾運輸納入前往站點與轉乘等待。作者將抽樣的起訖點組合與 Google Directions API 結果比較，同時明確表示後者不被視為真實值。雖然主要輸入使用開放資料，部分自行車速度資料及汽車速度修正資料具有存取或授權條件，不能把全部輸入都描述為無條件公開可用 [B3, Methods; Technical Validation]。

這篇研究可支持 GarbageGo 考量不同步行速度與完整行程時間，而不只用直線距離比較收運點。然而 Helsinki 路網、地理環境與資料來源不同於臺中，該矩陣不能直接用作臺中步行時間；GarbageGo 仍需確認當地路網資料與估計方式。

### 2.4 小結：文獻比較與對 GarbageGo 的啟示

論文 [B4] 著重行人路網與舒適路線；論文 [B3] 則比較不同步行速度下的旅行時間。前者提醒 GarbageGo 留意人行道與路口連接，後者提供考量步行速度差異的方向。GarbageGo 預計將步行時間與車輛 ETA 一起納入時間餘裕評估，但兩者都是估計值；路網缺漏、個人差異與資料延遲都可能造成誤差。步行路徑服務與驗證方式尚未定案。

## 3. LLM Agent 與 Tool Calling

### 3.1 基本概念

LLM 可以協助理解自然語言問題並產生文字回覆；Tool Calling 則讓模型能以約定格式請求外部工具提供查詢或計算結果。Agent 可依任務需求協調工具與處理其回傳資訊，但工具可用性、資料品質及工具調用是否正確仍須檢查 [B5]、[B6]。

在 GarbageGo 的規劃中，LLM Agent 預計負責理解需求、協調工具及說明結果；收運點搜尋、步行路徑、ETA 與推薦判斷由對應模組提供依據。此處描述的是規劃中的職責分工，並非已實作的功能。

### 3.2 Toolformer：語言模型使用外部工具

Schick 等人 [B5] 提出 Toolformer，研究如何讓語言模型透過自我監督學習使用外部 API。該方法在 CCNet 子集上產生候選工具調用、執行工具，再根據結果是否降低後續文字的預測損失篩選資料，並以加入工具調用的文本微調 GPT-J。研究使用的工具包括計算機、Wikipedia 搜尋、問答、翻譯及回傳目前日期的行事曆 API。作者在問答、算術等零樣本任務比較模型表現；工具使用在多項任務有幫助，但並非所有任務與所有比較模型皆獲改善，例如多語問答未一致優於原始 GPT-J [B5, §2–4]。

Toolformer 為「語言模型透過外部工具取得資訊或執行專門任務」提供研究參考。但它研究的是模型學習工具使用的方法，不代表 GarbageGo 必須自行訓練 Toolformer。論文亦指出其方法當時不支援將多個工具串接，也無法進行互動式工具使用，因此不能單憑此研究推論完整 Agent 流程已被驗證。

### 3.3 ReAct：結合推理與行動

Yao 等人 [B6] 提出 ReAct，讓語言模型交替產生推理與行動，並根據外部環境或工具的觀察結果繼續處理任務。研究使用問答、事實查核、文字遊戲與網頁操作等任務，探討推理與行動結合的效果。例如，模型可透過 Wikipedia API 取得外部資訊，再據此回應問題。

ReAct 對 GarbageGo 的參考在於：面對使用者查詢時，Agent 可依需求選擇工具、取得結果並調整後續處理。不過，原研究未驗證垃圾清運、臺中資料或本專案的推薦流程；其分析也顯示推理錯誤、重複行動及搜尋結果不足可能導致失敗。因此這是可供參考的流程概念，不代表本專案已採用 ReAct，也不保證每次工具調用都正確。

### 3.4 LLMAP：LLM 理解需求、演算法規劃路線

Yuan 等人 [B7] 指出，直接讓 LLM 作為 Agent 規劃路線時，難以處理大量地圖與 POI 資料；純圖搜尋方法則不易理解自然語言偏好。LLMAP 因此讓 LLM 擔任 Parser，從使用者文字中擷取要去的 POI 類型、時間限制、任務先後關係與偏好權重，再交由 MSGS 圖搜尋演算法，在時間限制、營業時間與任務順序等條件下計算路線。作者以涵蓋 14 個國家、27 個城市的 1,000 筆路線請求評估十餘種 LLM，報告 LLMAP 在多項指標上優於 LLM-as-Agent 方法 [B7, Abstract, §1, §5]。

原文 §4.4 另指出，LLM 擷取 POI、時間限制與任務關係的表現較好，但從文字推估數值型偏好權重時較不精確，例如「I am in a hurry」可能對應 0.7 至 0.9 的不同權重；§4.5 則展示模糊或歧義指令造成的誤解，需透過對話修正。作者在 Limitations 說明，POI 類型增加時，MSGS 的運算量會顯著上升。

此研究對 GarbageGo 的參考在於分工方式：LLM 負責理解需求並轉為結構化參數，距離與路線等數值由演算法計算，與 `DESIGN.md` 不讓 LLM 自行推測 ETA 與步行時間的原則一致。§4.4 的結果也提醒，LLM 轉換出的參數仍需檢查。不過 LLMAP 處理的是一般 POI 行程規劃，未涉及垃圾車 ETA 或收運點可行性，不能作為本專題流程的驗證。

### 3.5 小結：文獻比較與對 GarbageGo 的啟示

Toolformer [B5] 著重模型如何學習使用 API，ReAct [B6] 則探討交替進行推理、行動及觀察；LLMAP [B7] 進一步示範由 LLM 解析需求、由專門演算法完成路線計算的分工。GarbageGo 可參考其概念，讓 LLM 使用外部模組的結果生成說明；工具失敗、資料過期或資訊不足時，仍需要由系統明確處理並回報限制。三篇均未驗證本專題情境，LLM Provider、Agent 實作方式與是否使用特定框架均尚未定案。

綜合本章八篇文獻，既有研究分別提供垃圾車／公車 ETA、路網旅行時間與 LLM 工具協作方法；它們的研究目標與評估情境不同，尚不能直接構成本專題「使用者現在走向哪個收運點較可行」的驗證證據。因此，本章提出的研究切入點，是依 `DESIGN.md` 將車輛 ETA、步行時間、資料新鮮度與安全緩衝整合為候選點可行性判斷，再規劃與最近點策略等 Baseline 比較。這是本章根據所選文獻作出的初步歸納，並非證明整個領域從未研究類似問題；完整 Research Gap 仍應由 C 的領域章節與 A 的整合內容共同確認。

## 4. Article Summary Table

| Ref. | Year | Problem | AI Method | Domain Knowledge | Dataset | Findings | Limitation |
|---|---:|---|---|---|---|---|---|
| [B1] | 2019 | 預測垃圾車到達收運點的時間 | 自適應分群、特徵選擇與各群線性迴歸 | 臺灣定時定點清運及車輛路線 | 新竹市四月至十月垃圾車行程紀錄 | 分群搭配線性迴歸優於未分群的線性迴歸及神經網路；並考量運算時間 | 並非所有比較組合中準確率最高；不同城市的資料條件與效能仍須驗證 |
| [B2] | 2024 | 預測公車抵達時間 | IWOA 搜尋 LSTM 超參數 | 公車路線、站點、時段與天氣因素 | 南昌 220 路公車 2021 年 10 月 20 日 GPS 資料 | 作者在該案例報告 IWOA–LSTM 優於所比較模型 | 單日、單一路線；原文以所稱 test set 誤差調參，獨立測試與泛化能力須另驗證 |
| [B3] | 2024 | 建立考慮移動方式、時間及個人差異的旅行時間資料集 | 不適用；使用路網計算與 `r5py` | Helsinki 路網、交通方式與步行速度 | Helsinki 地區旅行時間矩陣及相關交通資料 | 提供不同情境下的門到門旅行時間，並與 Google Directions API 比較 | 研究區域非臺中；API 比較值並非真實到達時間 |
| [B4] | 2023 | 規劃考慮使用者舒適度的步行路線 | 不適用；GIS 路網與步行舒適度計算 | 人行道、路口、溫度、陰影及使用者偏好 | 西班牙馬德里空間與環境資料 | 提出人行道路網及依條件產生步行路線的方法 | 重點為舒適度；部分樹木遮蔭與穿越資訊不足，非專門驗證垃圾收運點步行時間 |
| [B5] | 2023 | 讓語言模型學習使用外部 API | 自我監督資料產生、篩選與 GPT-J 微調 | 計算、搜尋、問答等一般工具使用 | CCNet 子集；評估含 LAMA、算術、問答、MLQA 等任務 | 工具使用改善多項零樣本任務，但非所有任務皆優於比較模型 | 未針對垃圾清運驗證；原方法不支援串接工具與互動式工具使用 |
| [B6] | 2023 | 結合語言模型推理與環境行動 | ReAct 提示方法 | 知識檢索、問答及互動決策 | HotpotQA、FEVER、ALFWorld、WebShop | 作者展示交替推理與行動在多項任務中的效果 | 可能出現推理錯誤、重複行動或搜尋資訊不足；未針對本專案驗證 |
| [B7] | 2025 | 依自然語言偏好規劃多目標路線 | LLM-as-Parser 擷取需求與偏好，搭配 MSGS 圖搜尋 | POI、營業時間、時間限制與任務先後關係 | 14 國 27 城市共 1,000 筆路線請求 | 作者報告優於 LLM-as-Agent 方法；LLM 推估數值型偏好權重較不精確 | 一般 POI 行程，非垃圾清運；POI 類型增加時運算量顯著上升 |
| [B8] | 2026 | 預測公車到站時間並減少車輛串連 | 路線嵌入 LSTM 搭配多代理模擬 | 公車路線、站點、GPS 輪詢缺口與班距 | 紐約市 MTA SIRI 公車 GPS，20 條路線 | 作者報告 MAE 約 2.02 分鐘，較歷史平均 Baseline 改善約 28.5% | 公車情境；只適用已訓練路線；資料切分描述不完全明確 |

## 參考文獻

[B1] C.-H. Chen, F.-J. Hwang, and H.-Y. Kung, “Travel Time Prediction System Based on Data Clustering for Waste Collection Vehicles,” *IEICE Transactions on Information and Systems*, vol. E102.D, no. 7, pp. 1374–1383, 2019. [https://doi.org/10.1587/transinf.2018EDP7299](https://doi.org/10.1587/transinf.2018EDP7299).

[B2] B. Zhang, L. Tang, D. Zhou, K. Liu, and Y. Xue, “Bus Arrival Time Prediction Based on the Optimized Long Short-Term Memory Neural Network Model With the Improved Whale Algorithm,” *Journal of Advanced Transportation*, vol. 2024, Art. no. 6997338, 2024. [https://doi.org/10.1155/2024/6997338](https://doi.org/10.1155/2024/6997338).

[B3] C. Fink, E. Willberg, R. Klein, V. Heikinheimo, and T. Toivonen, “A travel time matrix data set for the Helsinki region 2023 that is sensitive to time, mode and interpersonal differences, and uses open data and novel open-source software,” *Scientific Data*, vol. 11, Art. no. 858, 2024. [https://doi.org/10.1038/s41597-024-03689-z](https://doi.org/10.1038/s41597-024-03689-z).

[B4] T. Al Shammas, P. Gullón, O. Klein, and F. Escobar, “Development of a GIS-based walking route planner with integrated comfort walkability parameters,” *Computers, Environment and Urban Systems*, vol. 103, Art. no. 101981, 2023. [https://doi.org/10.1016/j.compenvurbsys.2023.101981](https://doi.org/10.1016/j.compenvurbsys.2023.101981).

[B5] T. Schick et al., “Toolformer: Language Models Can Teach Themselves to Use Tools,” in *Advances in Neural Information Processing Systems*, vol. 36, 2023. [NeurIPS 論文頁面](https://proceedings.neurips.cc/paper/2023/hash/d842425e4bf79ba039352da0f658a906-Abstract-Conference.html).

[B6] S. Yao et al., “ReAct: Synergizing Reasoning and Acting in Language Models,” in *International Conference on Learning Representations*, 2023. [論文原文](https://arxiv.org/abs/2210.03629).

[B7] L. Yuan, D.-J. Han, C. G. Brinton, and S. Brunswicker, “LLMAP: LLM-Assisted Multi-Objective Route Planning with User Preferences,” in *Findings of the Association for Computational Linguistics: EMNLP 2025*, 2025, pp. 7866–7894. [https://doi.org/10.18653/v1/2025.findings-emnlp.416](https://doi.org/10.18653/v1/2025.findings-emnlp.416).

[B8] S. Rawat, A. Abaidullina, D. Alimbayeva, D. Kumar, and P. Kumar, “Real-time bus arrival prediction and bus bunching prevention using a multi-agent LSTM approach,” *Frontiers in Built Environment*, vol. 12, 2026. [https://doi.org/10.3389/fbuil.2026.1894212](https://doi.org/10.3389/fbuil.2026.1894212).

## 附錄：原文核對紀錄（供組內審閱）

核對日期：2026-11-06。[B1]–[B6] 來源為組員提供的六份本機 PDF；[B7] 為 ACL Anthology 公開 PDF，[B8] 為 Frontiers 網站全文頁；並以出版頁面與 Crossref 輔助核對書目；下表頁碼為 PDF 從第一頁起算的頁序。核對可確認本章轉述是否有原文支持，不能取代原研究實驗重現或組員親自閱讀。本章未重製原文圖表與原始資料；若後續使用圖片或重新散布資料，需另確認各自授權。

| Ref. | 主要核對位置 | 轉述範圍及使用限制 |
|---|---|---|
| [B1] | PDF 第 1、6–9 頁；§3.2、§4.1、§4.2 | 分群後線性迴歸、新竹實驗、App；原文為 IEICE 版權，未將 PDF 可取得解讀為可任意重製 |
| [B2] | PDF 第 1、5–9、13–14 頁；§2.3 Step 3、§3.3.5、§4、Conclusion | 單日公車 GPS、天氣特徵、超參數及 test set 調參文字；第 1 頁標示 CC BY，實驗資料第 14 頁註明需向通訊作者申請 |
| [B3] | PDF 第 1–5、10 頁；Methods、Technical Validation、授權段落 | 步行速度、時段差異及 API 比較；論文標示 CC BY-NC-ND 4.0，輸入資料另有各自使用條件 |
| [B4] | PDF 第 1、9–10 頁；Abstract、Discussion、Conclusion | 舒適度路線及樹木／穿越資料限制；第 1 頁標示 CC BY-NC-ND 4.0 |
| [B5] | PDF 第 1–5、7、9–10 頁；§2–4、§6 | 自我監督工具學習、評估與串接限制；本章未另確認圖表／全文重製授權 |
| [B6] | PDF 第 1、3、5–6 頁；§2、§3.3 | 交替推理與行動、任務與失敗分析；本章未另確認圖表／全文重製授權 |
| [B7] | PDF 第 1–2、8–10 頁（論文頁碼 7866–7867、7873–7875）；Abstract、§1、§4.4、§4.5、§5、Limitations | LLM-as-Parser 與 MSGS 分工、評估規模、數值偏好估計誤差及運算量限制；本章未另確認圖表／全文重製授權 |
| [B8] | Frontiers 全文頁；Abstract、§3.2、§3.10、§4.1、文末限制與未來工作段落 | 紐約公車 GPS、LSTM、歷史平均 Baseline、MAE 及資料切分文字；頁面標示 CC BY，資料可用性聲明表示其他詢問需洽通訊作者 |

本章只承擔 B 的技術文獻部分。整份 Related Work 是否達到約一半 AI Technology、約一半 Domain Know-how，以及完整的 Existing Research → Limitations → Research Gap → Our Project，需待合併 C 的章節後再驗收。老師對 2025–2026 證據的優先建議位於研究動機部分；本章 [B7]、[B8] 雖為 2025–2026 年文獻，但屬技術參考，同樣不取代 Introduction 所需的近期證據。
