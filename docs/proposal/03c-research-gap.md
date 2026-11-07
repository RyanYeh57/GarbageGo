# Research Gap

> **負責人：** 李安爵（C）
> **狀態：** 初稿 v2。依 `03a-related-work-ai.md`、`03b-related-work-domain.md` 與 `docs/research/opendata-api-check.md`（以下簡稱「API 實測」）撰寫；全員討論後定稿。
> **結構：** Existing Research → Limitations → Research Gap → Our Project

本組檢視的研究與服務已能告訴居民「垃圾車在哪裡」，部分系統也能預估垃圾車幾點到 [B1]；但在已檢視資料中，尚未找到整合步行時間與垃圾車 ETA，直接回答「我現在出發，走到哪個收運點來得及」的方案。GarbageGo 擬處理這個缺口；此結論不代表已窮盡所有研究與服務。

## 1. Existing Research

| 研究方向 | 文獻 | 已經做到什麼 |
|---|---|---|
| 收運作業規劃 | [C1][C2] | [C1] 以 GIS 最佳化收運路線，3 條路線的行駛距離都縮短；[C2] 統合 11 篇研究，IoT 路徑最佳化平均減少 21.51% 收運距離，使用實際營運資料的研究只減少 12.37% |
| 臺中收運方式 | [C7] | 平日沿街收運；國定假日改為定時定點，每個定點公告 10–30 分鐘的停留時段 |
| 影響到點時間的因素 | [C3][B1] | [C3] 曼谷垃圾量隨星期與區域類型變化，其中一群的週一垃圾量比平均高 31.5%；[B1] 發現新竹停收日（週三、週日）後的週四、週一行駛時間較長 |
| 居民端垃圾車資訊 | [C4][C5] | 即時位置、附近收運點查詢、接近時通知；[C5] 讓知道收運時間的居民由 30% 增至 95% |
| 垃圾車與公車 ETA 預測 | [B1][B2][B8] | [B1] 用新竹垃圾車的歷史站間行程，分群後以線性迴歸預測，App 可查附近收運點的預估到達時間；[B8] 的 LSTM MAE 約 2.02 分鐘，較歷史平均 Baseline 改善約 28.5% |
| GIS 步行路線與時間 | [B3][B4] | 以路網與不同步行速度計算門到門旅行時間；依人行道、路口與舒適度規劃步行路線 |
| LLM Agent 與 Tool Calling | [B5][B6][B7] | 讓 LLM 調用外部工具；[B7] 由 LLM 解析需求、演算法計算路線，表現優於直接讓 LLM 規劃 |
| 開放資料品質 | [C6] | 巴西 215 位資料管理人員中，71% 的平臺有標示更新頻率，但只有 54% 確實依標示更新；詮釋資料與資料同步更新的只有 48% |

## 2. Limitations

| # | 限制 | 依據 |
|---|---|---|
| L1 | 收運研究多為營運端設計，目標是路線長度與成本，不是居民能否趕上 | [C1][C2] |
| L2 | 居民端服務停在「位置」「接近通知」與「預估到點時間」，公開文件都沒有把居民走到收運點的時間納入判斷 | [C4][C5][B1] |
| L3 | ETA 研究難以直接套用：臺中 App [C4] 提到可預測抵達時間，但未公開方法與準確度；[B1] 使用新竹車載設備的歷史行程；[B2]、[B8] 為公車情境，分別有單日單一路線、只適用已訓練路線的限制 | [C4][B1][B2][B8] |
| L4 | 公開資料的粒度與時效有限：本組推定公開 API 約每 5 分鐘產生快照，官方資料集頁面標示每 10 分鐘，內部車機回報間隔為每 20 秒；2026-11-03 19:42 單次快照中 663 台車有 118 台（約 18%）位置超過 30 分鐘未更新；API 回應不提供歷史資料 | [C4][C6]、API 實測 §6–7 |
| L5 | 公開資料之間難以直接串接：動態資料的 `location` 不是收運點編號；20,090 個收運點只有文字地址，沒有座標 | API 實測 §4、§9 |
| L6 | 到點時間的影響因素缺少可取得的臺中本地量測：[C3] 只分析垃圾量與距離，交通採靜態假設，也沒有量測停留時間；[B1] 的星期效應來自新竹；臺中環保局內部雖統計停駐時間與準點率，但沒有公開 | [C3][B1][C4] |
| L7 | 步行時間研究不針對收運點：[B3] 為 Helsinki 的旅行時間矩陣，[B4] 以步行舒適度為目標，兩者都沒有與車輛 ETA 結合 | [B3][B4] |
| L8 | LLM Agent 研究未驗證垃圾清運情境，且 LLM 從文字推估數值並不精確 | [B5][B6][B7] |

這些限制分成三類：

- **問題面（L1–L2）**：本組檢視的研究與服務尚未提供從居民角度判斷「來不來得及」的完整方案。
- **資料與方法面（L3–L6）**：要回答這個問題，必須處理低頻、不完整且彼此分散的公開資料，並用本地資料估計停留與卸載造成的延誤。
- **整合面（L7–L8）**：ETA、步行時間、LLM 工具調用各自都有研究；在本組檢視的範圍內，尚未找到整合這些技術判斷收運點可行性的方案。

## 3. Research Gap

> 在本組檢視的文獻與服務中，尚未找到以居民為中心的系統，能在低頻、不完整的公開資料下，同時考慮垃圾車到點時間、居民步行時間與資料不確定性，判斷「現在出發來不來得及」，並在來不及時提供備案。

| Gap | 說明 | 來自 |
|---|---|---|
| G1 | 把垃圾車 ETA 與居民步行時間合在一起，從「垃圾車幾點到」進一步回答「我趕不趕得上、該去哪個點」 | L1、L2、L7 |
| G2 | 在本組推定約每 5 分鐘產生快照、部分車輛位置可能過期的資料下，探索以本地資料估計到點時間，並揭露不確定性 | L3、L4、L6 |
| G3 | 把垃圾車動態資料與收運點資料串成可以做空間查詢的資料 | L5 |
| G4 | 用自然語言說明推薦依據，但判斷所需的數值不交給 LLM 推估 | L8 |

### 與既有服務比較

| 能力 | 臺中垃圾清運大車隊 [C4] | 新竹垃圾車 ETA 系統 [B1] | 利馬 IoT 系統 [C5] | GarbageGo（Planned） |
|---|---|---|---|---|
| 垃圾車即時位置 | 有 | 有 | 有 | 使用公開 API |
| 附近收運點查詢 | 有 | 有，由使用者自行選點 | 論文未提及 | GIS Engine |
| 接近通知 | 有 | 論文未提及 | 有 | v0.1 不承諾（DESIGN §1.4） |
| 到點時間預測 | 文件提到，未公開方法 | 有，方法公開（分群＋線性迴歸） | 論文未提及（只在接近時通知） | ETA Engine，附不確定性 |
| 居民步行時間 | 文件未提及 | 論文未提及 | 論文未提及 | GIS Engine，以路網估計 |
| 判斷來不來得及、提供備案 | 文件未提及 | 論文未提及 | 論文未提及 | Recommendation Engine |
| 資料時效提示 | 文件未提及 | 論文未提及 | 論文未提及 | 顯示資料時間與風險（FR-10） |

「未提及」表示公開文件或論文中沒有看到，不代表該系統一定沒有這項功能。各欄都已對照原文。

## 4. Our Project

GarbageGo 依 `DESIGN.md` 的設計回應四個 Gap。以下皆為 Planned，尚未實作。

| Gap | GarbageGo 的做法 | 對應 |
|---|---|---|
| G1 | Recommendation Engine 對每個候選收運點計算 `slack(s) = truck_ETA(s) − walking_time(s) − safety_buffer(s)`，不只依距離排序；最佳點不可行時搜尋備案 | DESIGN §5.1、FR-07、FR-08 |
| G1 | GIS Engine 以路網估計步行時間，而不是直線距離 | DESIGN §3.1、FR-06 |
| G2 | ETA Engine 先建立 Schedule、Distance/Speed、Historical 三種 Baseline，再依資料品質選擇進階模型；Schedule Baseline 可直接使用收運點資料的表定時間 | DESIGN §6.1–6.2、API 實測 §8 |
| G2 | 依 GPS 時間戳判斷資料新鮮度，以 `safety_buffer` 吸收資料延遲；資料不足時標示為不確定，不提供沒有依據的精確時間 | DESIGN §2.2、§5.2 第 09–11 行、FR-10 |
| G2 | API 回應僅含最新位置；本組已收集 29 天、約 98 萬筆去重 GPS 點，擬評估其能否供 Historical Baseline 使用，以及是否足以推定實際到點時間作為評估依據 | DESIGN §4.1、API 實測 §3 |
| G3 | Data Acquisition 擬以車牌串接兩份資料：收運點資料的 374 個車牌中，358 個（95.7%）曾出現在 29 天動態資料中；此結果不保證即時或逐站配對。收運點地址也須轉為座標後交給 GIS Engine | DESIGN §4.2 第 3 步、API 實測 §9.4 |
| G4 | LLM Agent 負責理解需求與說明推薦理由，GPS、ETA、步行時間等數值一律來自工具結果；分工方式與 [B7] 的 LLM-as-Parser 相近 | DESIGN §1.4、§3.1 |

**Expected Outcomes：** 預計以趕上率、誤判率比較「最近點策略」與本專題的「時間可行性策略」（DESIGN §8）。實際結果待實驗後填入。

## 5. 待討論事項

- [ ] Research Gap 的主軸是否以 G1「趕不趕得上」為核心。
- [ ] 接近通知是否維持不在 v0.1 範圍。
- [ ] 確認已收集的 GPS 資料能否可靠推定實際到點時間，及其是否適合作為評估基準。

## 參考文獻

完整說明見 `03a-related-work-ai.md`、`03b-related-work-domain.md`。

- [B1] C.-H. Chen, F.-J. Hwang, and H.-Y. Kung, "Travel Time Prediction System Based on Data Clustering for Waste Collection Vehicles," *IEICE Transactions on Information and Systems*, vol. E102.D, no. 7, pp. 1374–1383, 2019. https://doi.org/10.1587/transinf.2018EDP7299
- [B2] B. Zhang, L. Tang, D. Zhou, K. Liu, and Y. Xue, "Bus Arrival Time Prediction Based on the Optimized Long Short-Term Memory Neural Network Model With the Improved Whale Algorithm," *Journal of Advanced Transportation*, vol. 2024, Art. no. 6997338, 2024. https://doi.org/10.1155/2024/6997338
- [B3] C. Fink, E. Willberg, R. Klein, V. Heikinheimo, and T. Toivonen, "A travel time matrix data set for the Helsinki region 2023 that is sensitive to time, mode and interpersonal differences, and uses open data and novel open-source software," *Scientific Data*, vol. 11, Art. no. 858, 2024. https://doi.org/10.1038/s41597-024-03689-z
- [B4] T. Al Shammas, P. Gullón, O. Klein, and F. Escobar, "Development of a GIS-based walking route planner with integrated comfort walkability parameters," *Computers, Environment and Urban Systems*, vol. 103, Art. no. 101981, 2023. https://doi.org/10.1016/j.compenvurbsys.2023.101981
- [B5] T. Schick et al., "Toolformer: Language Models Can Teach Themselves to Use Tools," in *Advances in Neural Information Processing Systems*, vol. 36, 2023. https://proceedings.neurips.cc/paper/2023/hash/d842425e4bf79ba039352da0f658a906-Abstract-Conference.html
- [B6] S. Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models," in *International Conference on Learning Representations*, 2023. https://arxiv.org/abs/2210.03629
- [B7] L. Yuan, D.-J. Han, C. G. Brinton, and S. Brunswicker, "LLMAP: LLM-Assisted Multi-Objective Route Planning with User Preferences," in *Findings of the Association for Computational Linguistics: EMNLP 2025*, 2025, pp. 7866–7894. https://doi.org/10.18653/v1/2025.findings-emnlp.416
- [B8] S. Rawat, A. Abaidullina, D. Alimbayeva, D. Kumar, and P. Kumar, "Real-time bus arrival prediction and bus bunching prevention using a multi-agent LSTM approach," *Frontiers in Built Environment*, vol. 12, 2026. https://doi.org/10.3389/fbuil.2026.1894212
- [C1] H. Hassan, T. Ali, and A. Tamimi, "Development of a Smart Waste Management System for Route Optimization and Adaptive Demand Management in Dubai," *The International Archives of the Photogrammetry, Remote Sensing and Spatial Information Sciences*, vol. XLVIII-G-2025, pp. 575–581, 2025. https://doi.org/10.5194/isprs-archives-XLVIII-G-2025-575-2025
- [C2] R. R. Maciel, A. D. de Souza, R. M. A. Almeida, and J. P. R. R. Leite, "The Impact of IoT-Enabled Routing Optimization on Waste Collection Distance: A Systematic Review and Meta-Analysis," *Logistics*, vol. 9, no. 4, Art. no. 161, 2025. https://doi.org/10.3390/logistics9040161
- [C3] C. Hamontree, J. Koiwanit, and A. Sinchai, "Sustainable urban waste collection using a hybrid heuristic–genetic approach: a Bangkok case study," *Frontiers in Sustainability*, vol. 6, Art. no. 1716538, 2026. https://doi.org/10.3389/frsus.2025.1716538
- [C4] 臺中市政府環境保護局，「臺中垃圾清運大車隊即時查詢系統網站及 APP」，臺中市政府廉能透明獎精進發展類申請文件，2021（文件未標日期，引用數據截至 2021 年 5 月）。<https://www.ethics.taichung.gov.tw/media/732603/01_環保局_臺中垃圾清運大車隊即時查詢系統網站及app.pdf>
- [C5] N. Duran Guerrero, Y. Paccini Ventura, J. Mansilla Lopez, and R. Loza, "Improvement of Garbage Collection Management using the Internet of Things," in *Proc. 24th LACCEI International Multi-Conference for Engineering, Education, and Technology*, Santiago, Chile, 2026. https://doi.org/10.18687/LACCEI2026.1.1.1106
- [C6] F. Tejedo-Romero, J. F. F. E. Araujo, and M. J. Gonçalves Ribeiro, "The usability of Brazilian government open data portals: ensuring data quality," *Humanities and Social Sciences Communications*, vol. 12, Art. no. 297, 2025. https://doi.org/10.1057/s41599-025-04404-y
- [C7] 臺中市政府環境保護局北區清潔隊，「115 年國定假日定時定點表」，2026 年度公告，2026 年 11 月 6 日存取。https://www.epb.taichung.gov.tw/media/1354635/03-北區-115年-國定假日定時定點表.pdf
