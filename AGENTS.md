# AGENTS.md

> GarbageGo — Claude / Codex 共用開發規範。
>
> 本文件為專案共用規範的 Single Source of Truth。
> 所有 AI Agent 均應遵循本文件，但不得覆蓋系統層級指示或使用者明確要求。

## 1. Language

- 使用繁體中文回答、解釋與撰寫專案文件。
- 技術名詞、API、Class、Function、Variable 保留英文。
- 程式碼命名優先使用英文。
- Commit Message 使用英文，格式保持一致。

## 2. Development Workflow

本專案使用 **Superpowers** 管理開發流程。

### 2.1 Initialization

開始任務前：

1. 讀取 `AGENTS.md`，確認專案共用規範。
2. 讀取 `DESIGN.md`，理解目前系統架構、模組責任與設計決策。
3. 依任務需要，讀取 `docs/specs/`、`docs/plans/` 與相關程式碼。
4. 確認目前可使用的 Superpowers Skills。
5. 確認任務目標、修改範圍、驗收條件與可能影響。

若 `DESIGN.md` 或相關文件尚未建立，應說明現況，不得假設文件內容已存在。

### 2.2 Standard Workflow

新功能與重大架構變更依下列流程執行：

1. **Understand**：理解需求、目標、限制與驗收條件。
2. **Brainstorming**：使用 Superpowers `brainstorming` 探討方案及技術取捨。
3. **Design Approval**：向使用者確認設計，未確認前不得進入重大功能實作。
4. **Specification**：更新 `docs/specs/` 與 `DESIGN.md`，記錄已確認的設計。
5. **Planning**：使用 `writing-plans` 拆分任務，將計畫存放於 `docs/plans/`。
6. **Implementation**：依計畫實作，對可測試的核心邏輯遵循 TDD。
7. **Verification**：執行測試，確認結果符合驗收條件。
8. **Review**：檢查程式品質、安全性、相容性與需求符合程度。
9. **Documentation**：同步更新相關文件及實作狀態。
10. **Completion**：回報完成內容、驗證證據、已知限制與後續事項。

### 2.3 Workflow Rules

- 新功能及重大架構變更，必須先確認設計。
- 未經使用者確認，不得直接實作尚未定案的重大功能。
- 使用者要求「只設計、不實作」時，不得自行進入 Implementation。
- Bug Fix 優先使用 `systematic-debugging`。
- 可測試的核心邏輯遵循 **Red → Green → Refactor**。
- 實作中發現重大設計衝突，應先說明並重新確認。
- 不得擅自擴大修改範圍。
- 不得宣稱測試成功，除非已實際執行並確認結果。
- Superpowers 的具體操作以目前可用 Skill 的正式指示為準。

### 2.4 Lightweight Tasks

以下任務可使用簡化流程：

- 文件錯字、格式與排版修正。
- 不影響功能的註解調整。
- 已有明確設計的小型修改。
- 不涉及架構變更的簡單設定調整。

簡化流程仍須確認修改範圍、遵守適用的 Skills，並執行必要驗證。

## 3. Project Rules

- 不得任意刪除、破壞或改變既有功能。
- 優先維持簡單、模組化、可測試且可維護的架構。
- 修改 API 時同步更新相關文件及測試。
- 未經確認，不得引入大型框架或重大依賴。
- 避免不必要的重構與超出需求範圍的修改。
- 不得在程式碼中硬編碼 API Key、Token、Password。
- 敏感資訊使用環境變數或安全的設定管理機制。
- 不得將 `.env`、憑證、密鑰及敏感資料提交至 Git。
- 重大技術選型應提出替代方案、優缺點及建議。
- 未經確認，不得修改既有系統的重要對外介面或資料格式。
- 外部 API 必須考慮 Timeout、Error Handling、Rate Limit 與資料不可用情況。

## 4. Documentation

專案文件依下列位置管理：

| 文件 | 用途 |
|---|---|
| `README.md` | 專案介紹、安裝、執行方式與 Demo |
| `DESIGN.md` | 系統架構、模組責任、資料流程、技術決策及實作狀態 |
| `docs/specs/` | 需求規格、功能定義與驗收條件 |
| `docs/plans/` | Superpowers 開發計畫 |
| `docs/architecture/` | 詳細架構、Flowchart、Pseudocode |
| `docs/research/` | 論文、資料來源與研究紀錄 |
| `docs/proposal/` | 期末專題 Proposal |

### 4.1 Documentation Rules

- 文件內容必須與實際程式行為一致。
- 需求變更時同步更新相關 Specification。
- 架構、模組責任或資料流程變更時，必須更新 `DESIGN.md`。
- API 變更時同步更新 API 文件及相關測試。
- 研究資料應記錄來源、日期、授權與限制。
- 不得虛構論文、資料集、實驗結果或引用來源。
- 尚未實作的功能必須標示為 `Planned`。
- 已實作但尚未驗證的功能應標示為 `Implemented / Unverified`。
- 只有完成相關驗證後，才能標示為 `Verified`。
- `DESIGN.md` 負責整體設計，詳細內容可連結至 `docs/architecture/`，避免重複維護。

### 4.2 Documentation Synchronization

開始開發前：

1. 確認 `DESIGN.md` 與相關 Specification。
2. 檢查是否已有對應的開發計畫。
3. 確認本次修改會影響哪些文件。

完成開發後：

1. 更新 `DESIGN.md` 的相關模組與實作狀態。
2. 更新受影響的 Specification、README 或 API 文件。
3. 確認文件與實際程式行為一致。

不要求每次小型修改都更新所有文件，只更新受到影響的部分。

## 5. Skills

### 5.1 General Rules

- 優先使用目前 Agent 環境已安裝的 Superpowers。
- 執行任務前，確認是否有適用的 Skill。
- 依 Skill 的觸發條件與工作流程執行。
- 不得假設 Skill 已成功安裝或可使用。
- 若 Skill 不可用，應說明情況並採用合理替代流程。
- 不得因為存在 Skill 目錄，就假設該 Skill 已被 Agent 正確載入。
- 專案共用規範以 `AGENTS.md` 為準；具體 Skill 執行方式以各 Agent 的安裝環境為準。

### 5.2 Codex

- 使用 `.agents/skills/` 中已安裝的 Superpowers Skills。
- 優先閱讀 `.agents/skills/using-superpowers/SKILL.md`。
- 依任務類型選用 `brainstorming`、`writing-plans`、`test-driven-development`、`systematic-debugging`、`verification-before-completion` 等技能。
- 若 Skill 文件不存在，應先回報，不得假設其內容。

### 5.3 Claude

- 優先使用 Claude Code 環境中已安裝的 Superpowers Plugin。
- 透過 `CLAUDE.md` 引用本文件。
- 依目前 Claude Code 環境的技能載入方式執行。
- 若 Plugin 未安裝或無法使用，應先告知使用者。
- 不得假設 Claude 與 Codex 的 Skill 路徑相同。

## 6. Code Principles

遵守以下原則：

- **KISS**：Keep It Simple, Stupid。
- **DRY**：Don't Repeat Yourself。
- **SOLID**：物件導向設計原則，在適用情況下採用。
- **YAGNI**：You Aren't Gonna Need It。

優先順序：

1. Correctness（正確性）
2. Readability（可讀性）
3. Maintainability（可維護性）
4. Testability（可測試性）
5. Performance（效能）

避免為了套用 Design Pattern 而增加不必要的複雜度。

## 7. Testing & Verification

- 新增或修改核心邏輯時，應補充對應測試。
- Bug Fix 優先建立可重現問題的測試。
- 修改後執行相關 Unit Tests。
- 涉及模組整合時，執行 Integration Tests。
- 外部 API 使用 Mock 或測試資料驗證異常情況。
- 必須考慮正常、邊界及異常情境。
- 無法執行測試時，必須說明原因及未驗證範圍。
- 完成任務前，檢查是否符合驗收條件。
- 不得將 Mock 測試結果描述為真實 API 整合測試結果。
- 不得將預期結果描述為已完成的實驗結果。

## 8. Git Workflow

- 新功能與重大修改優先使用獨立 Branch。
- Commit 前檢查修改範圍與敏感資訊。
- Commit Message 使用清楚、一致的英文描述。
- 不得未經使用者授權執行 Force Push、Reset Hard 或其他可能破壞資料的 Git 操作。
- 不得擅自刪除其他開發者或 Agent 的未提交變更。
- 除非使用者明確要求，不得自動 Push 至遠端 Repository。
- 多個 Agent 同時開發時，優先使用獨立 Git Worktree，避免相互覆蓋修改。
- 不得擅自覆蓋其他 Agent 尚未完成的工作。

## 9. GarbageGo Domain Rules

本專案為結合 LLM、GIS、ETA Prediction 與垃圾清運領域知識的 Domain AI Agent。

### 9.1 Architecture

- **LLM Agent**：負責需求理解、任務規劃、工具調用及結果解釋。
- **GIS Engine**：負責空間查詢、收運點搜尋、距離及路線分析。
- **ETA Engine**：負責垃圾車到指定收運點的時間估計。
- **Recommendation Engine**：負責候選收運點可行性評估與排序。
- **RAG**：負責檢索清運規則及相關領域知識。
- **Data Acquisition**：負責取得、驗證及整理外部資料。

各模組應保持明確職責，避免將 GIS 計算、ETA 預測或推薦排序直接交由 LLM 自行猜測。

### 9.2 Data & AI

- 優先使用可驗證的政府 OpenData 與官方資料。
- 外部資料應記錄來源、更新時間、授權與使用限制。
- 不得將預定清運時間視為實際抵達時間。
- 不得將過期 GPS 資料描述為即時位置。
- ETA 預測應保留資料更新時間與不確定性。
- 不得讓 LLM 自行虛構 GPS、ETA、距離、清運點或預測結果。
- LLM 應依據 GIS、ETA 與其他工具的實際結果生成建議。
- 若資料不足，應明確告知使用者，不得提供沒有依據的精確時間。
- 訓練資料、測試資料應適當分離，避免 Data Leakage。
- 模型結果必須透過客觀指標驗證，不得虛構模型效能。

### 9.3 Recommendation Rules

- 不得只依照直線距離推薦最近的收運點。
- 應考慮使用者步行時間、垃圾車 ETA、清運時間及候選點可行性。
- 應考慮 ETA 不確定性，避免推薦高風險方案。
- 若最佳候選點不可行，應搜尋其他可行方案。
- 無法確認可行性時，應標示風險與資料限制。
- 推薦結果應提供可解釋的依據。

### 9.4 Privacy & Location

- 使用者定位應取得適當授權。
- 只蒐集完成任務所需的定位資訊。
- 不得在 Log 中記錄不必要的精確位置或敏感資訊。
- 若需要儲存歷史定位資料，必須先確認用途、保存方式與保留期限。

## 10. Completion Criteria

任務完成前，確認：

- [ ] 符合需求與驗收條件。
- [ ] 沒有破壞既有功能。
- [ ] 已執行適用的測試與驗證。
- [ ] 已更新受影響的文件。
- [ ] 沒有洩漏敏感資訊。
- [ ] 清楚說明完成內容、測試結果及已知限制。

### Completion Report

完成開發任務後，應簡要回報：

1. **Changes**：本次完成的修改。
2. **Tests**：實際執行的測試與結果。
3. **Documentation**：更新的文件。
4. **Limitations**：尚未解決的問題或未驗證部分。
5. **Next Steps**：建議的下一步。

只有完成實際驗證後，才能宣稱相關功能已通過測試。