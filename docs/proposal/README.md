# GarbageGo Proposal 分工說明

> **Status:** Active
> **Last Updated:** 2026-11-03
> **組員章節截止:** 2026-11-07
> **最終繳交:** 2026-11-11

本文件說明 Proposal 階段剩下的工作、分工方式、協作規則，以及使用 AI 時要遵守的規範。

開工前請先讀：

1. `AGENTS.md`：專案共用規範。
2. `DESIGN.md`：目前的系統設計。
3. `docs/proposal-rule.txt`：老師的 Proposal 規範（評分依據）。
4. 本文件。

---

## 1. 目前進度

| 繳交項目 | 狀態 |
|---|---|
| Proposal Document | ❌ 未開始 |
| Proposal PPT | ❌ 未開始 |
| GitHub Repository | ✅ 完成 |
| DESIGN.md | ✅ v0.1 草稿 |

**最大缺口：** Introduction、Related Work、Deep Research 三塊合計佔 **60%** 分數，目前都還沒寫。

---

## 2. 分工

| 成員 | 姓名 | 主責 | 負責檔案 |
|---|---|---|---|
| **A** 組長／整合 | 文賢 | Proposed Scheme、Abstract、最後整合、**製作整份 PPT** | `05-proposed-scheme.md`、`01-abstract.md`、`06-references.md`、`DESIGN.md` |
| **B** AI 技術 | 易軒 | Related Work（AI 技術） | `03a-related-work-ai.md` |
| **C** 領域＋資料 | 安爵 | Related Work（領域知識）、Research Gap、OpenData API 實測 | `03b-related-work-domain.md`、`03c-research-gap.md`、`docs/research/opendata-api-check.md` |
| **D** 深度研究 | 勇嘉 | Deep Research、Introduction | `04-deep-research.md`、`02-introduction.md` |

> PPT 由 A 依各章內容統一製作，B、C、D 只需交文字章節。

### 2.1 各自要寫什麼

**A — Proposed Scheme**
- 架構圖：每個主要模組用 ①②③… 編號，正文逐一說明。
- Flowchart：Input → Processing → AI/Analytics → Decision → Output，包含判斷、迴圈、例外分支。
- Pseudocode：有行號，可沿用 `DESIGN.md` §5.2 再修整。
- 技術可行性：引用 C 的 API 實測結果。
- 最後寫 Abstract（A–F 六段），並把各章合併、統一引用編號、轉成 PDF。
- 製作整份 PPT：研究動機、文獻、Research Gap、Agent Design、Architecture、Flowchart、Pseudocode。

**B — Related Work（AI）** 約 5 篇
- 車輛／公車 ETA 預測。
- LLM Agent、Tool Calling。
- GIS 路徑與步行時間估計。

**C — Related Work（領域）** 約 5 篇 ＋ Research Gap ＋ API 實測
- 垃圾清運作業與「定時定點」制度。
- 既有垃圾車查詢 App 與服務。
- 政府 OpenData 的品質與限制。
- API 實測：欄位、座標系統、更新頻率、缺漏情況，記錄在 `docs/research/opendata-api-check.md`。
- Research Gap：Existing Research → Limitations → Research Gap → Our Project。C 依自己的研究先寫初稿，A 統整時再調整。

**D — Deep Research ＋ Introduction**
- Q1：五個核心思維模式（意義、證據、對系統設計的影響）。
- Q2：三個專業爭論（觀點 A ↔ 觀點 B → Evidence → Consensus → Unresolved Problems）。
- Q3：十個深度理解問題（Why、What-if、Trade-off、Failure Case 等）。
- Introduction：A–F 結構，用 2025–2026 的公開數據、報告或案例開頭。

---

## 3. 檔案結構

```text
docs/proposal/
├── README.md                    # 本文件
├── 01-abstract.md               # A
├── 02-introduction.md           # D
├── 03a-related-work-ai.md       # B
├── 03b-related-work-domain.md   # C
├── 03c-research-gap.md          # C
├── 04-deep-research.md          # D
├── 05-proposed-scheme.md        # A
├── 06-references.md             # A（整合時產生）
└── figures/                     # 圖片
```

**一人一檔，不要改別人的檔案。** 發現別人的章節有問題，在 PR 或群組裡講。

---

## 4. 時程

| 期限 | 內容 | 誰 |
|---|---|---|
| **2026-11-07** | 完成負責章節，並送出 PR | B、C、D |
| **2026-11-11** | 統整全文、轉 PDF、製作 PPT，最終繳交 | A |

---

## 5. 協作規則

### 5.1 Git

| 規則 | 說明 |
|---|---|
| 開自己的 branch | 名稱：`proposal/<章節>`，例如 `proposal/related-work-ai` |
| 用 PR 合併 | 不要直接 push 到 `main`，由 A 審核後合併 |
| Commit Message 用英文 | 例如 `docs(proposal): add ETA prediction related work` |
| 不要提交 `.env`、API Key | 見 `AGENTS.md` §3 |
| 原始資料不要直接放 repo | API 實測只放摘要與少量範例 |

### 5.2 引用

- 每一篇文獻都要附 **DOI 或可點開的 URL**。
- 每一篇都要**自己打開原文確認過**。
- 各自檔案底部列出自己的參考文獻，暫時用自己的代號：B 用 `[B1]`、`[B2]`…，C 用 `[C1]`…，D 用 `[D1]`…。
- A 整合時統一改成 IEEE 格式的 `[1]`、`[2]`…。

### 5.3 文獻摘要表

每個人在自己的檔案裡放自己那幾篇，欄位固定：

| Ref. | Year | Problem | AI Method | Domain Knowledge | Dataset | Findings | Limitation |
|---|---|---|---|---|---|---|---|

A 整合時合併成一張表。

---

## 6. AI 使用規範

老師允許使用 AI，但**你必須能解釋內容、說明為什麼這樣寫、說明怎麼驗證**。老師會口頭抽問。

### 6.1 一定要遵守

| 規則 | 原因 |
|---|---|
| **不得虛構論文、作者、年份、數據** | AI 很常編出不存在的論文，被抓到會很嚴重 |
| 每篇文獻都要自己打開原文確認 | 確認論文存在，且內容跟 AI 的摘要一致 |
| 不寫實驗結果，只寫 Expected Outcomes | 規範要求 |
| 不改專案題目與範圍 | 題目固定為「臺中市垃圾收運點到點可行性推薦」 |
| 不自行提出新架構 | 架構以 `DESIGN.md` 為準，有想法提出來討論 |
| 只改自己負責的檔案 | 避免衝突，也避免 AI 順手亂改 |

### 6.2 開場 Prompt（每次開新對話先貼）

把 `< >` 換成自己的內容。可以在 repo 裡讀檔的 AI（Claude Code、Codex 等）會自己讀檔；網頁版 AI 讀不到 repo，要把 `docs/proposal-rule.txt` 對應段落和 `DESIGN.md` 第 1、3 節一起貼上。

```text
你是 GarbageGo 期末專題 Proposal 的寫作助理。

開始前先讀：
- AGENTS.md
- DESIGN.md
- docs/proposal/README.md
- docs/proposal-rule.txt

我是成員 <A/B/C/D>。
我負責的檔案：<檔名>
本章必備內容：<貼上本文件 2.1 節中屬於你的部分>

規則：
1. 只能修改上面列出的檔案。其他檔案有問題，用文字告訴我，不要改。
2. 不寫程式，不修改 AGENTS.md、DESIGN.md、README.md。
3. 每個引用都要附 DOI 或 URL。找不到可驗證的原文就不要寫，不得虛構論文、作者、年份或數據。
4. 不寫實驗結果，只寫 Expected Outcomes。
5. 不更改專案題目與範圍，不提出新的系統架構，架構以 DESIGN.md 為準。
6. 使用繁體中文，專有名詞保留英文。
7. 不確定的地方先問我，不要自己假設。

完成時回報：
- 寫了哪些段落
- 用了哪些來源（附連結）
- 還缺什麼、哪些內容需要我確認
```

> **例外：** A 整合時需要修改 `DESIGN.md`，A 的 Prompt 可以拿掉第 2 條中的 `DESIGN.md`。

---

## 7. 交 PR 前的檢查清單

- [ ] 只改了自己負責的檔案。
- [ ] 規範要求的小標題都有寫到（對照 `docs/proposal-rule.txt`）。
- [ ] 每篇文獻都有 DOI／URL，而且我自己打開看過。
- [ ] 沒有虛構的數據或實驗結果。
- [ ] 內容和 `DESIGN.md` 的架構一致。
- [ ] 我能口頭解釋每一段在寫什麼。

審核人（A）至少**隨機點開 2 個引用連結**確認。
