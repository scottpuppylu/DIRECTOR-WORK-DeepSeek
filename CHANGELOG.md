# CHANGELOG — DeepSeek Harness 版

本 repo 是 [DIRECTOR-WORK](https://github.com/scottpuppylu/DIRECTOR-WORK) v2.2.0（Claude Code／Claude Desktop 版，MIT）的移植。
上游的完整變更歷史保留在 [`CHANGELOG-upstream.md`](CHANGELOG-upstream.md)；本檔只記 DeepSeek 版自己的變更。

## 2.2.0-ds.2（2026-11-14）

規格先行（SDD）：DSH 上的 worker（deepseek-flash）判斷力較弱，所以規格、驗收測試和計畫在寫程式前寫死並鎖住。規格層採用現成的 OpenSpec（Fission-AI/OpenSpec，MIT，鎖 1.16.0），DW-DS 只寫膠水。完整說明見 `docs/13_sdd_openspec.md`。

### 規則（`director_work.json` 的 `"sdd"` 開關，預設全開）
- Standard／Strict 工單必填 `SPEC_CHANGE = openspec/changes/<名稱>`；`gate_check.py --order / --match` 會實際跑 `openspec validate <名稱> --strict --json`，找不到 CLI 判不過（不會靜默通過）。Strict 的變更不能 `skip_specs: true`。
- 規格審查從「只有 Strict」改成 Standard 也必做（`--match --dispatch-log` 查 `SPEC_REVIEW <WO>` 行）。
- 測試先寫：`TESTS_LOCKED:` 記驗收測試的 sha256（`sdd_gate.py --lock-tests` 產生）；被改就判不過。
- 計畫閘門：worker 先交 OpenSpec 的 `tasks.md`，總監核准後記 `PLAN_APPROVED <WO> sha=<64>`；交件時 tasks.md 只准比核准版多打勾，而且要全部勾完（勾選規則照 OpenSpec）。
- 工單大小：最後結果 ≤3 個檔、≤200 行（`openspec/` 不算），`scope_check.py` 超過印 `OVERSIZE`。
- STOP_RULES：同一根因 1 輪沒進展就停（原 2 輪）。
- 沒有 AUTO 驗收時提示（優先 AUTO）。

### 工具
- 新增 `tools/sdd_gate.py`：上述檢查的共用模組（`gate_check.py`、`scope_check.py` 載入），CLI `--lock-tests`、`--plan-hash`、`--which`。每段註明 OpenSpec 為什麼沒有這個功能。
- `gate_check.py`：`--order / --match` 接 SDD 檢查；`--repo` 可用在 `--order / --match`（專案 checkout）；新增 `--config`。
- `scope_check.py`：Standard／Strict 工單的大小上限（`SIZE:`／`OVERSIZE`）；新增 `--config`。
- `selftest_ds.py`：新增 8 個 `sdd_*` 測試（含「NONE 但 Standard」「validate 失敗」「找不到 CLI」三個負面案例，及改測試、停止規則、計畫被改、大小超過）；`sdd_real_openspec` 用真的 CLI（找不到就 SKIP）。

### 文件與範本
- 新增 `docs/13_sdd_openspec.md`（流程、開關、原生 vs 膠水、安裝、OpenSpec vs Spec Kit 選型、已知限制）。
- 更新 `docs/02`（規格先行一節、規格審查）、`docs/05`（SDD 時怎麼分 effort）、`docs/11`（OpenSpec 在 DSH 上的操作）、`BOOTSTRAP.md`（10.5 規格先行工具）、`README.md`、`DEEPSEEK-PORT.md` 第 11 節、`tools/README.md`。
- `templates/WORK_ORDER.md`：`SPEC_CHANGE`、`TESTS_LOCKED`、大小上限、計畫閘門、STOP_RULES 1 輪；`templates/SPEC_REVIEW.md`：Standard 必做、加審 OpenSpec 變更三題。
- 新增 `templates/openspec_config.yaml`（OpenSpec 原生 `rules:`／`operations:`）；`"sdd"` 開關的完整寫法放在 `docs/13`（`director_work.example.json` 不在本次工單範圍，沒改）。

### 升級注意
- 預設全開：舊的 Standard／Strict 工單沒有 `SPEC_CHANGE`／`TESTS_LOCKED`、STOP_RULES 寫 2 輪，`gate_check.py --order` 會判不過。舊工單用 `--warn`／`--since`，或在專案 `director_work.json` 把對應開關設成 `false`。
- 沒裝 OpenSpec 的專案：關掉 `require_spec_for_standard`／`require_spec_for_strict`（BOOTSTRAP 10.5 第 5 點）。

### 驗證
- `selftest_ds.py`：基準 11/11 → 19/19 PASS（`OPENSPEC_BIN` 指到實機 OpenSpec 1.16.0）；不設時 18 PASS、1 SKIP（`sdd_real_openspec`）。
- 試跑找到並已修進來：`validate --strict` 要求 Requirement 含英文 SHALL／MUST（改用原生 `init --language zh-TW`）；archive 後主規格 Purpose 要 ≥50 字元；`python -I -m unittest <模組>` 找不到 cwd 的測試（CHECKS 改 `discover -s .`）；交件時未勾的任務原本不查。
- 試跑：`_work/demo-project` 一張 Standard 工單走完 propose → 審查 → tasks 核准 → apply → 交件檢查 → archive，見 `_work/ds2-openspec/TRIAL.md`（Claude 模擬 worker；DSH 實機 deepseek-flash 尚未跑，列為 PO 步驟）。

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
- 保留（平台中立）：`gate_check.py`、`scope_check.py`、`evidence_record.py`、`report_vs_audit.py`、`trace_report.py`、`round_check.py`、`status_gen.py`、`metrics_report.py`、`memory_size_check.py`、`secret_mask.py`、`pause_ctl.py`、`audit_log.py`（verify／head／cite／recover）、`vocabulary.json`；其中 `report_vs_audit.py`（DSH 包殼比對）、`status_gen.py`（吃 po_pending）、`memory_size_check.py`（預設 AGENTS.md）、`pause_ctl.py`（無 hook 自動檢查）、`audit_log.py`（append 不用）做了小幅適配。
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