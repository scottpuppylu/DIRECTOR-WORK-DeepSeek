# 05 模型與思考程度（effort）

本檔是 dsh-DIRECTOR-WORKER（簡稱 dshdw；舊名 DIRECTOR-WORK DeepSeek 版（DW-DS））的版本。平台只有一個模型，差別在思考程度（reasoning effort）。Claude 版原文見 upstream（`repo/docs/05_models_effort.md`）。

## 可用的模型與 effort

| 項目 | 值 |
|---|---|
| 模型 | `deepseek-flash`（DeepSeek-V4.1-Flash），DSH 目前唯一可選 |
| 思考程度 | `off` / `low` / `high` / `max` |
| 總監自己的模型與 effort | 由 PO 在 DSH 設定（模型與思考程度）決定，總監不能自己改 |
| worker 的模型與 effort | 總監開子代理時指定，開完**不能中途改** |

effort 的意思：`off` 關閉思考，只適合純機械工作；`low` 例行、反應快；`high` 一般預設；`max` 最難、品質優先。平台與模型會更新，實際名稱以 DSH 設定為準。

## 規則

### 判斷原則：重要程度 × 難度

- **重要且困難 → max**；**重要或困難其一 → high**；**其餘 → high 或 low**。
- worker 最低 `low`。只有「只收發指令、不需要判斷」的線（例如清理員只照清單做、格式轉換）才用 `off`。
- **max 只臨時用**：worker 照停止規則在同一根因 1 輪沒進展就停下回報（ds.2，`docs/02`）；總監判斷要做最後一次深度根因分析時，才開 max 的接班人；寫進 `DIRECTOR_LOG.md`，解決後換人或關線。
- 只在工作線換到重要度或難度明顯不同的階段時才調整；調整方式是開接班人（子代理）並在 `ACTIVE_WORKSTREAMS.md` 記下新 effort，不是對同一個子代理改設定。
- 開工時把 `MODEL: deepseek-flash` 和 `EFFORT: <off|low|high|max>` 寫進工單和 `DIRECTOR_LOG` 的 DISPATCH 行；接班、重派都照同一規則記。

### 派工難度表（2.5.0-ds.6，上游 2.5.0）

每次派工都在 DISPATCH 行寫難度類別、開子代理時給的思考程度和模型：`| class=<類別> effort=<off|low|high|max> model=deepseek-flash`。`tools/dispatch_check.py --log DIRECTOR_LOG.md` 檢查，只提醒。

| 類別 | 例子 | effort |
|---|---|---|
| `mechanical` | 只收發指令、照清單搬檔、格式轉換 | off 或 low |
| `routine` | 照清單做、整理、一般小改 | low 或 high |
| `dev`、`ui` | 一般開發、介面 | high |
| `root_cause`、`fix_after_fail`、`realism`、`core_engine` | 根因研究、修失敗之後的那一輪、真實度關鍵、核心引擎 | high 或 max |
| `repeated_failure` | 同一問題重複失敗之後 | max（只臨時用，解決後換人或關線） |

和上游的差別：DSH 只能設 `off / low / high / max`（開子代理時的 `reasoning_effort`，開完不能改），沒有 Claude Code 的 `medium`、`xhigh`；表裡寫 `xhigh` 的類別在這裡是 high 或 max，照上面「判斷原則」選。`--table <表.json>` 可換成專案自己的表。

### 依角色

| 角色 | 建議 effort | 說明 |
|---|---|---|
| 總監（根 session） | high（難專案 max，由 PO 設定） | 以分派、裁決為主；大量閱讀和看圖交給子代理 |
| 總管（排程） | high | routine 排程；規則判斷交總監 |
| 清理員 | low | 照清單盤點與比對；刪除前的保護檢查要寫清楚 |
| Worker：關鍵路徑、架構決策、困難除錯 | max | 例如核心演算法、資料格式、品質最落後的領域 |
| Worker：重要但做法已知 | high | |
| Worker：一般實作、截圖、參數實驗 | high 或 low | 卡在根因時個別調高；要換 effort 就開接班人 |
| 盲審 reviewer（子代理） | high | 品質判斷不省；指示只准讀（DSH 子代理預設拿到完整工具，限制靠指示＋總監事後用 `dsh_audit.py` 核對） |
| 機械性子代理（搜尋、彙整 log、格式轉換） | off 或 low | 只回傳結論 |

### 選用角色（同 Claude 版，改成子代理）

| 角色 | 是誰 | 做什麼 | 不做什麼 |
|---|---|---|---|
| 總管（排程） | 一個子代理 | 排程共用重資源（GPU、長 build、量測時段），寫排程看板 | 不決定優先序（照總監給的）；不改程式 |
| 清理員 | 一個子代理 | 磁碟盤點、備份、經擁有者同意後刪除 | 不刪有依賴或受保護的資料 |
| 盲審 reviewer | 總監開的子代理，指示只准讀 | 只看審查包的盲審層，列出缺陷與證據（`docs/07`） | 不看答案、不看分數、不寫檔 |

專案沒有共用重資源，就不要總管；磁碟不吃緊，就不要清理員。每多一個子代理，就多一份用量與管理成本（同一棵樹最多 8 個作用中子代理）。

### 派工規劃

總監的職責範圍不變（`docs/01`）。每次派工前先想清楚怎麼分給工人，不把實作都攬進總監自己的 session。

- **規劃要回答**：要不要開 worker、開幾個；依檔案歸屬怎麼切（同一個檔案只給一個人，Single Writer）；平行還是先後（後一個要用前一個的結果，就排先後）；每個 worker 的 effort（照本檔「判斷原則」）；誰整合、誰驗收（不是寫的人自己）。
- **寫在哪裡**：寫進工單，或 `DIRECTOR_LOG.md` 的 DISPATCH 那一筆；恢復時看得到當初怎麼分。
- **總監自己做的**：讀、規劃、寫工單、審證據、裁決、管續航（`docs/01` 的職責）。改檔、跑測試這類實作交給 worker，驗收才是中立的。
- 一件事只有一個人做最快、拆開反而要多整合時，就只開一個 worker，並在規劃裡寫一句為什麼。
- **平行線切多大**（2.2.4-ds.4，上游 2.2.4）：整合前每條線至少是一段完整功能加它的測試；切得比這更細，整合花的比平行省的多。
- **能同時就同時派**：兩條長線互不依賴就一起派，不要等一條做完才派下一條。
- **派工前查重複**（2.5.0-ds.6，上游 2.5.0）：`tools/dispatch_check.py --dup "<標題和範圍>" --resume "<各線>/**/RESUME_STATE*.md" --repo <repo>`，有 `~ WARN DUP` 先看那條線或那個 commit 是不是已經在做。可能誤報，看過再決定。
- **派工前估時間**：每條線估一個時間寫進規劃；兩條線同時在跑的時間不到較長那條的一半，就合併成一條或重切。
- 同一棵樹最多 8 個作用中子代理（可在 DSH「設定 → 子代理」調整上限）、委派深度 1（worker 不能再開子代理）；開線前確認名額。

### 安全閘門下怎麼分 effort（ds.2；2.2.5-ds.5 拿掉 OpenSpec）

`deepseek-flash` 判斷力較弱，所以判斷集中在派工前（`docs/13`）：

| 工作 | 誰做 | 建議 effort | 說明 |
|---|---|---|---|
| 寫工單 ACCEPTANCE 與驗收測試 | 總監，或總監開的測試子代理 | high；核心邏輯、資料格式用 max | 這一步錯了，後面全部照錯的做；不省 |
| 規格審查（`templates/SPEC_REVIEW.md`） | 審查子代理 | high | Standard 也做 |
| 寫 PLAN.md（計畫閘門） | worker | 與實作同一個 effort | worker 開完不能改 effort，計畫和實作是同一條線 |
| 照 PLAN.md 實作一張小工單（≤3 檔、約 200 行） | worker | high；純機械改動 low | 工單夠小、測試先寫，就不需要 max |
| 1 輪沒進展後的接班人 | 新 worker | 比原本高一級 | 交接靠 `RESUME_STATE.md`，不讓原 worker 重試同一招 |

### 不要為省用量犧牲品質的界線

下面這些**不降** effort：P0 阻擋的根因分析、gate 裁決、正式候選的盲審、安全與資料完整性相關的修改、要給 PO 看的成品檢查。
要省，先從上下文長度省（`docs/04`），不是從思考省。

## 為什麼

- 一律 max 很浪費；一律 off 會做錯、返工，返工更貴。用「重要 × 難度」分配，簡單又可解釋。
- DeepSeek Harness 只有一個模型，所以 effort 是唯一的成本旋鈕；但 effort 的效果因任務而異，要用 `tools/dsh_usage.py` 的實際用量和返工次數驗證，不要憑感覺。
- 子代理的 effort 在開工時固定，不能像 Claude 版那樣中途用工具調。與其假裝能調，不如把「為什麼選這個 effort」寫進派工紀錄，要變就開接班人（交接靠 `RESUME_STATE.md`）。
- 盲審和裁決是品質的最後一道防線，省在這裡會讓整條線的努力白費。
- 總監自己做實作，上下文變長、平行變排隊，也沒有中立的驗收（`docs/10` L-057）。
