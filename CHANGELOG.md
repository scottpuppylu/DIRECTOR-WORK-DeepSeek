# CHANGELOG — DeepSeek Harness 版

本 repo 是 [DIRECTOR-WORK](https://github.com/scottpuppylu/DIRECTOR-WORK) v2.2.1（Claude Code／Claude Desktop 版，MIT）的移植。
上游的完整變更歷史保留在 [`CHANGELOG-upstream.md`](CHANGELOG-upstream.md)；本檔只記 DeepSeek 版自己的變更。

## 2.2.1-ds.1（2026-11-14）

對應上游 2.2.1（`CHANGELOG-upstream.md` 已加上游 2.2.1 全文；上游 dw-221 commit 7a6091e）。上游 2.2.1 只改工具，沒有改規則文件；本版搬三項工具變更，另修 2.2.0-ds.1 的幾處說明錯誤。流程核心不變。

### 工具（對應上游 2.2.1）
- `report_vs_audit.py`：換成上游 2.2.1 版。被截在 500 字的紀錄行照 JSON 字串解回 `\"`、`\\`，長的 Windows／UNC／含引號指令對得上；沒被截的指令不再當成截斷（較長的主張不會靠前綴通過）；單字比對至少要 2 個不是 `...`／`<名稱>` 的字（只寫 `python -I -X utf8` 不再假通過）。DSH 的部分保留：`pwsh` 算 shell 工具、說明寫 PTC 包殼。讀到 `kind=rebuild` 的紀錄時印 `~ note: a log was rebuilt after the fact (dsh_audit.py) ...`（上游的字樣寫 transcript，DSH 改寫成重建來源）。
- `dsh_setup_check.py`：加上游 2.2.1 setup_check 的 shadow 檢查，印 `~ shadow: ...`，`--strict` 才算失敗：PO_PENDING 的 ID 重複（OD/ACT 以外的 `ID:` 行與缺 CREATED 只是提示）；RESUME_STATE 標頭四行有值、UPDATED 有日期（用 `gate_check.check_resume`，四行順序仍照舊算失敗）；director_work.json 的 `schema_version` 1、`mode`、三個 `*_pattern` 是合法正規式、`po_pending_files` 是字串清單；Claude 專用鍵（window、plugins_off、hooks……）和不認得的鍵只提示。DSH 原本就有的欄位、STATUS、答案、順序檢查不變。
- `dsh_setup_check.py` bug：OD/ACT 以外的 `ID:` 行（例如範例設定允許的 `CH-xx`）後面的欄位，原本會算到上一筆，誤報「STATUS 出現 2 次」。現在那一行之後不再算進上一筆。
- `dsh_audit.py`（build 版本 1 → 2）：建出的紀錄第 1 行是 `kind=rebuild`，`source` 記 `by: dsh_audit.py`、版本、讀了哪些 session 檔（檔名、sha256、大小）、行數、警告與略過數，和上游 `transcript_audit.py` 的第 1 行同格式；工具呼叫從 seq 2 起，`head_seq` 含這一行。串鏈抽成 `chain_lines()` 好測。
- 上游新工具 `transcript_audit.py` 不搬：它讀 Claude Code transcript，DSH 沒有這種檔；DSH 的事後重建本來就是 `dsh_audit.py`（記於 `DEEPSEEK-PORT.md` 第 7 節）。

### 說明更正（2.2.0-ds.1 寫了但沒做）
- `pause_ctl.py`：2.2.0-ds.1 的 CHANGELOG 與 `DEEPSEEK-PORT.md` 說「移除 hook 自動檢查假設」，實際檔案和上游一模一樣，說明仍寫 `hook_guard.py --pause-flag` 會擋每個工具呼叫。本版才改：DSH 沒有 hook，旗標要 worker 自己讀（`pause_ctl.py status` 或 `dsh_guard.py --pause-flag`），總監審查時核對；不看的 worker 照樣能動作。
- `status_gen.py`：說明與 `~ PENDING_METHOD_MISSING` 提示原本寫「worker 用 ask_user_question 問 PO」，和平台事實相反（子代理呼叫會被拒，DELEGATED_CALLER）。改成：總監（根 session）用 `ask_user_question`，worker 經「總監」。
- `dsh_session.py`：「REWRITE-GUIDE section 0」是本 repo 沒有的文件，改指 `docs/01_roles_authority.md`、`docs/11_dsh_operations.md`。
- `BOOTSTRAP.md`、`README.md`：上游版本改寫 v2.2.1。

### 遷移
- `dsh_audit.py` 新建的紀錄多一行第 1 行，seq 往後移 1；舊檔不受影響，舊的 AUDIT_RANGE／錨點照舊對舊檔。要比對新舊 build 時注意這一行。
- `dsh_setup_check.py` 新檢查是 shadow，exit code 不變；用 `--strict` 前，範本的範例條目（`ID: OD-01（要 PO 決定）或 ACT-01……`）與佔位會被提示。

### 驗證
- `selftest_ds.py`：11 項 → 14 項（新增 `matching_221`：21 個比對案例＋2 個 CLI＋6 個突變都被抓到；`setup_shadow`：7 種錯誤 shadow 不失敗、`--strict` 失敗，乾淨資料夾 `--strict` 通過，5 種提示；`audit_rebuild`：第 1 行、verify、改過的行被拒、report 的 note）。`dsh_audit_and_report` 改成檢查第 1 行是 rebuild，session_id 從後面的行取。紀錄：`D:/DIRECTOR-WORK-HANDOFF/v221/selftest_ds_221.log`。
- 沒測到的（已知限制）：`dsh_audit build` 只在本機現有的 DSH session 紀錄上跑過（selftest 的 `dsh_audit_and_report`），沒在 DSH 裡實際跑一輪派工；比較報告 D 節列的沙箱、`git clone` 啟動流程仍未實測。

對齊初衷：
1. 幫到誰：DSH 版的總監（核對報告不再誤判或假通過、建置檢查多看三個檔案）、讀文件的人（暫停旗標與 PO 管道的說明和平台事實一致）。依據：DeepSeek 版與 2.2.0 的比較報告 A 節、A3。
2. 平台：全是本機命令列工具；DSH 沒有 hook，所以暫停與紀錄都寫明是自己讀、事後重建。
3. 服務：初衷 5（成品要真的對）：核對不假通過；初衷 7（零成本）：只用標準庫。
4. 核心：每輪必讀不變；新檢查先 shadow。
5. 舊檔案：照樣能讀；`report_vs_audit` 原本判錯的那幾類結果會變。

## 2.2.0-ds.1（2026-11-12）

第一個 DeepSeek Harness 版，對應上游 2.2.0。流程核心（角色、工單、gate、證據、續航、初衷卡）不變，平台層重寫。

### 文件
- `README.md`：啟動提示詞、流程說明、FAQ、檔案地圖改成 DeepSeek Harness 版；新增「Claude 版和 DeepSeek 版有什麼不同」與防護對照。
- `BOOTSTRAP.md`：0～14 步改寫。待決頁改成本機 `PO_PENDING.md`＋`ask_user_question`；壓縮門檻與 context_probe 改成 DSH 設定、子代理名額、指示載入確認與 `dsh_usage.py` 基準；開 worker 改成 `subagent`；外掛清單步驟改成「不移植、只列給 PO」。
- `docs/04_quota_efficiency.md`：改成 token 計價、1,048,576 上下文、KV cache、自動壓縮與 `dsh_usage.py` 量測。
- `docs/05_models_effort.md`：只有 `deepseek-flash`，effort 改成 `off/low/high/max`；子代理開工時選 effort、不能中途改。
- `docs/09_memory.md`：改成 AGENTS.md 指示鏈（每條 64 KiB）與 DIRECTOR 檔案，沒有 MEMORY.md。
- `docs/11_dsh_operations.md`（取代 `11_claude_desktop.md`）：能力→DSH 工具對照、開 worker 流程、限制清單。
- `docs/12_chat_to_product.md`：選擇頁改成聊天附圖＋`ask_user_question`，移除 Artifact 與 choice 帳本機制。
- 其餘 docs（01、02、03、06、06b、07、08、10）做平台名詞與工具替換；不自稱 DSH 沒有的能力。檔名對齊內容：`01_roles_authority.md`、`06_resume_lossless.md`、`06b_on_demand_procedures.md`、`08_safety_rules.md`；每輪必讀四份實測 10,947 bytes（上限 11,000，記於 `DEEPSEEK-PORT.md`）。
- `PURPOSE.md`：原文保留（只有 PO 能改）；其中「Claude Code／Claude Desktop」字樣屬歷史敘述，PO 可視需要自行更新。

### 範本
- `templates/AGENTS_PROJECT_SECTION.md`（取代 `CLAUDE_PROJECT_SECTION.md`）。
- `templates/PO_PENDING.md` 改成待決帳（`ask_user_question`＋本機帳）。
- `templates/RESUME_STATE.md` 的 session 欄位改子代理名稱。
- 移除 `templates/choice_page.html`、`templates/settings.runtime-guard.json`、`templates/guard_sessions.json`。
- 其餘工單／報告／裁決／測試申請／初衷卡／DIRECTOR 骨架照原版小幅替換。

### 工具
- 保留（平台中立）：`gate_check.py`、`scope_check.py`、`evidence_record.py`、`report_vs_audit.py`、`trace_report.py`、`round_check.py`、`status_gen.py`、`metrics_report.py`、`memory_size_check.py`、`secret_mask.py`、`pause_ctl.py`、`audit_log.py`（verify／head／cite／recover）、`vocabulary.json`；其中 `report_vs_audit.py`（DSH 包殼比對）、`status_gen.py`（吃 po_pending）、`memory_size_check.py`（預設 AGENTS.md）、`pause_ctl.py`（無 hook 自動檢查；更正：本版實際沒改，2.2.1-ds.1 才改）、`audit_log.py`（append 不用）做了小幅適配。
- 新增：`dsh_session.py`（共用庫：找 Node、解 session zstd、列 session、agent 名稱映射）、`dsh_usage.py`（token 用量與上下文）、`dsh_audit.py`（從 session 紀錄重建動作）、`dsh_doctor.py`（環境檢查）、`dsh_setup_check.py`（DIRECTOR 建置檢查）、`dsh_guard.py`（選用的風險指令自我提醒）、`selftest_ds.py`（冒煙測試）。
- 移除：`hook_guard.py`、`setup_project_settings.py`、`context_probe.py`、`usage_report.py`、`usage_mix.py`、`doctor.py`、`setup_check.py`、`choice_reconcile.py`、`browser_check.py`、`poll_hint.py`、`selftest.py`、`container/`。
- `director_work.example.json`：移除 Claude 專用欄位（window、plugins_off、hooks、protect_director、director_worktree）。

### 沒做（NOT_PORTED）
- PreToolUse hooks 與命令層自動阻擋（DSH 沒有 hook 機制）。
- Artifact 私人頁面、置頂、留言叫醒、choice 資料庫與收條。
- 容器 worker、WSL 隔離、網路出口管制。
- 專案級外掛開關、記憶索引 MEMORY.md、Monitor、notify_when_idle、session 封存、interrupt_agent、讀取他人 context 的工具。
- 輸出：`tools/selftest_ds.py` 只冒煙測試 DeepSeek 版工具，不重寫上游 527 KB 的 selftest。

### 驗證
- 端到端 demo：`_work/demo-project` 用 WO-001（加 multiply）派給子代理 w1，交件 HEAD `d675820dfc9a27638951cb00ebc22729a37d2fdb`；總監親跑 gate_check（--order/--hash/--match/--verdict）、scope_check、evidence_record verify --rerun、dsh_audit build+verify（141 筆）、report_vs_audit（8/8 PASS）全綠；裁決 PASS → ACCEPT_AND_CLOSE（NO MERGE / NO PUSH）。
- 工具鏈：`selftest_ds.py` PASS 11/11；`dsh_doctor.py` PASS 12/12；`dsh_setup_check.py` 對 demo DIRECTOR PASS；`dsh_usage.py --session w1` 讀到 effort/context%（10.8%）。
- 子代理平台：AGENTS.md 自動載入、可 send_message 回總監、可續談；worker 不能 ask_user_question（DELEGATED_CALLER）。
- 文件：必讀四份 10,947 bytes（上限 11,000）；`RAN` 截斷規則與 `--project-dir`/`--session` 語意已按實測修正。
- 完整實測指令與輸出見 `DEEPSEEK-PORT.md` 第 8 節。

### 升級
- 上游有新版時，先看 `CHANGELOG-upstream.md` 的該版變更，只把「規則與工單格式」的變更搬過來；平台層（docs/04、05、11、12、BOOTSTRAP 的 DSH 段落）以本版為準。