# DIRECTOR-WORK → DeepSeek Harness 版：移植報告

本檔說明這次移植：動了什麼、為什麼、哪些搬不過去、怎麼驗證、以後怎麼跟上上游。

## 1. 移植原則

1. **流程核心不動。** 權責分層、工單與 gate、證據優先、RESUME_STATE 續航、初衷卡、Single Writer、依風險選流程——這些是 `PURPOSE.md` 的九項核心，原樣保留。
2. **平台層重寫。** 凡是「Claude Code／Claude Desktop 提供的能力」，換成 DeepSeek Harness（DSH）的等價做法或誠實的替代；做不到的標 NOT_PORTED，不假裝。
3. **能少改就少改。** 文件只改平台耦合處；工具只移植平台中立的部分；新增的 DSH 工具集中在新檔，不散落各處。
4. **可驗證。** 每個新工具都用真實 session 紀錄跑過；每份文件不自稱平台沒有的能力；驗證結果寫在第 8 節。

## 2. 平台事實（移植時依據）

| 事實 | 值 | 來源 |
|---|---|---|
| 平台 | DeepSeek Harness 桌面版 0.2.2-rc.2（DSH） | `~/.dsh/profiles/desktop/cordis.patch.yml`、app asar |
| 模型 | `deepseek-flash`（DeepSeek-V4.1-Flash），目前唯一 | 模型選擇器、request/header 紀錄 |
| 思考程度 | `off / low / high / max`；`off` 關閉思考 | `dsh-llm-deepseek` 套件文件 |
| 上下文視窗 | 1,048,576 tokens（官方模型清單） | session 紀錄的 request/context、`dsh-llm-deepseek` README |
| 單次輸出上限 | 預設 256,000 tokens | request/header config |
| 自動壓縮 | 有（dsh-compaction-basic） | DSH 套件文件 |
| 專案指示 | `AGENTS.md`（也讀 `CLAUDE.md`）、`AGENTS.local.md`；專案鏈每條 64 KiB | `dsh-agent-instructions` README |
| 使用者層指示 | `~/.dsh/AGENTS.md`、`~/.agents/AGENTS.md` | 同上 |
| worker | `subagent` 開的具名子代理，可續談、可傳訊息、有完成通知 | `dsh-tool-subagent` README |
| 子代理上限 | 每棵樹作用中預設 8；委派深度預設 1 | `dsh-subagent` README、GUI 設定 |
| 檔案沙箱 | `read-only / workspace-write / danger-full-access` | `dsh-sandbox-policy` README、session 紀錄 |
| 核准政策 | session 設定（本環境可設 never ask） | `dsh-user-approval` 套件、session 紀錄 |
| Hooks | **沒有** PreToolUse 等 hook 機制 | asar 套件清單無 hook 套件 |
| 待決問答 | `ask_user_question`（選項＋自訂答案，可多題）；**對 delegated 子代理會被拒絕**（DELEGATED_CALLER），只有總監能問 PO | 工具 schema、`dsh-tool-ask-user` README |
| 成品展示 | `present`（上限 8 個檔；子代理做的檔要由總監自己呼叫） | 工具 schema、`dsh-tool-present` README |
| 用量資料 | 另有純 JSON 的投影快取 `%USERPROFILE%\.dsh\storages\session_projcache\sessions\<id>.json`（`tokenUsage`、`contextPressure`、`sessionStats`、`sandboxMode`、`approvalState`…） | 實際檔案（version 7） |
| worktree | 這個 profile **沒有** worktree 工具；所有子代理共享同一個 checkout | asar 套件清單、team:policy |
| 成品展示 | `present`（成品檔）、聊天 markdown 圖 | 工具 schema |
| 排程 | `schedule_create/list/view/edit`；只有 PO 明確要求可建；子代理不能用 | `dsh-tool-schedule` README |
| 共享工作板 | Team 模式下的 `team_task_*`（本版不用作真相來源） | `dsh-tool-agent-team` README |
| 用量與動作 | session 紀錄：`%USERPROFILE%\.dsh\sessions\--<cwd>--\session-<id>\session.v4.jsonl.zstd` | 實際檔案 |
| 遠端/封存/中止 | **沒有** session 封存、interrupt_agent（本 profile 未掛載） | 工具清單、`dsh-tool-subagent-control` 文件 |

## 3. 能力對照表

| DIRECTOR-WORK 需要的能力 | Claude 版做法 | DeepSeek 版做法 | 狀態 |
|---|---|---|---|
| 開一條 worker 工作線 | `start_session` | `subagent({name, cwd, prompt, reasoning_effort})` | 移植 |
| 傳訊息給 worker | `SendMessage` | `send_message({agent, message})` | 移植 |
| 看 worker 狀態 | `list_sessions`／`get_session` | `list_agents()`＋讀 `RESUME_STATE.md` | 移植（細節較少） |
| worker 回報總監 | 訊息／完成通知 | `send_message`／DSH 完成通知 | 移植（已實測） |
| 調 worker 模型/effort | `set_session_model`／`set_session_effort`（可中途） | 開工時指定 `reasoning_effort`；要改開接班人 | 部分移植 |
| 額度／上下文用量 | `get_usage` | `tools/dsh_usage.py`＋GUI token meter | 替代 |
| 專案指示 | `CLAUDE.md` | `AGENTS.md`（也認 CLAUDE.md） | 移植 |
| 使用者層規則 | `~/.claude/CLAUDE.md` | `~/.dsh/AGENTS.md`、`~/.agents/AGENTS.md` | 移植 |
| 待決頁 | Artifact 私人頁面＋置頂＋留言叫醒 | `ask_user_question`＋本機 `PO_PENDING.md` | 替代（無置頂／網頁） |
| 選擇題 | choice_page 網頁＋資料庫＋收條 | 聊天附圖＋`ask_user_question` | 替代（較簡） |
| 成品給 PO 看 | Artifact 截圖＋頁面 | `present`＋聊天 markdown 圖 | 替代 |
| 叫醒／排程 | 背景計時器／排程任務 | `schedule_create`（PO 明確要求時） | 移植（有條件） |
| 工具前自動阻擋 | PreToolUse hook（hook_guard.py） | 無；沙箱模式＋核准政策＋規則＋事後 audit | NOT_PORTED |
| 動作紀錄 | hook 寫 hash chain log | `dsh_audit.py` 從 session 紀錄重建（需 Node 解 zstd） | 替代（事後） |
| 用量 | `get_usage`、Claude transcript | `dsh_usage.py` 讀 projcache JSON（純 Python） | 替代 |
| worktree 隔離 | 每條線獨立 worktree | 共享 checkout；手動 git worktree 可行，但不是 DSH 機制 | 部分移植 |
| 容器 worker／網路管制 | container/run_worker.sh | 無 | NOT_PORTED |
| 外掛清單與關閉 | `claude plugin list`／`plugins_off` | 使用者層設定，本版不改 | NOT_PORTED |
| 記憶索引 | `~/.claude/projects/.../MEMORY.md` | AGENTS.md 指示鏈＋DIRECTOR 檔案 | NOT_PORTED（無索引檔） |
| 壓縮門檻 250000 | `.claude/settings.local.json` | 模型視窗 1,048,576＋DSH 自動壓縮 | NOT_PORTED（不需要） |
| 額度重置喚醒 | 5 小時／週視窗 | 無對應；改成中斷恢復程序 | NOT_PORTED |
| 盲審 reviewer 限工具 | subagent 只給 Read/Glob/Grep | 子代理預設全工具；指示＋事後 audit | 部分移植 |

## 4. 文件改寫清單

| 檔案 | 改寫幅度 | 內容 |
|---|---|---|
| `README.md` | 大 | 啟動提示詞、流程、FAQ、檔案地圖改 DSH；新增「Claude 版和 DeepSeek 版有什麼不同」、防護對照、限制 |
| `PURPOSE.md` | 無 | 原文保留（只有 PO 能改）；平台字樣屬歷史，PO 可自行更新 |
| `BOOTSTRAP.md` | 大 | 0～14 步重寫：待決帳、DSH 設定、子代理名額、指示載入驗證、`dsh_usage.py` 基準、開子代理、第一份回報 |
| `docs/01` | 小 | 角色改根 session／子代理；子代理上限與深度；reviewer 限制說明 |
| `docs/02` | 中 | MODEL/EFFORT 改 deepseek-flash／effort；規格審查改子代理；報告核對改 `dsh_audit.py`；移除 hook 敘述 |
| `docs/03` | 小 | 跨代理訊息、send_message、無 notify_when_idle；待決頁改 ask_user_question＋PO_PENDING |
| `docs/04` | 大 | token 計價、1M 上下文、KV cache、自動壓縮、`dsh_usage.py` 量測；移除方案額度與停工線 |
| `docs/05` | 大 | 只有 deepseek-flash；effort off/low/high/max；不可中途改；接班流程 |
| `docs/06` | 小 | 自動壓縮；子代理續談；RESUME_STATE 不變 |
| `docs/06b` | 中 | 恢復程序改用 `list_agents`＋子代理續談；機制重建用 `schedule_create`；移除容器與額度重置 |
| `docs/07` | 小 | 盲審 reviewer 改子代理（無法限工具）；成品用 `present`／聊天圖 |
| `docs/08` | 小 | 保留核准清單；新增「DSH 能擋到什麼」；移除權限模式與 hook 敘述 |
| `docs/09` | 中 | AGENTS.md 指示鏈大小（64 KiB）＋DIRECTOR 檔案；沒有 MEMORY.md |
| `docs/10` | 輕 | 保留教訓；開頭說明哪些是 Claude 版機制、DSH 版不適用 |
| `docs/11_dsh_operations.md` | 新 | 取代 `11_claude_desktop.md`：能力→工具對照、開 worker 流程、限制清單 |
| `docs/12` | 大 | 選擇頁改聊天附圖＋ask_user_question；移除 Artifact／choice 帳本；初衷卡與追溯保留 |
| `templates/` | 中 | AGENTS_PROJECT_SECTION（新）、PO_PENDING（待決帳）、RESUME_STATE（子代理名稱）、DIRECTOR_FILES、BRIEF、WORK_ORDER、TASK_REPORT 等改 DSH；移除 choice_page.html、settings.runtime-guard.json、guard_sessions.json |

## 5. 工具移植

**保留（平台中立；其中 5 個有小幅 DSH 適配）**

| 工具 | 用途 |
|---|---|
| `gate_check.py` | 工單／報告／裁決／測試申請格式與互相對照、雜湊、派工紀錄 |
| `scope_check.py` | 比對實際改動與工單 SCOPE／FORBIDDEN |
| `evidence_record.py` | 驗收指令的證據紀錄與重跑 |
| `report_vs_audit.py` | 報告聲明 vs 動作紀錄；**適配**：先剝 DSH 的 PowerShell 包殼、絕對路徑 python、`...` 萬用字元再比 |
| `trace_report.py` | 需求→工單→AC→證據→裁決追溯 |
| `round_check.py` | 修正輪數上限 |
| `status_gen.py` | 狀態頁／狀態檔產生；**適配**：吃 `po_pending`、移除 pending_sends／processes／PO 頁 |
| `metrics_report.py` | PURPOSE 五個數字 |
| `memory_size_check.py` | 指示檔大小；**適配**：預設找最近的 `AGENTS.md`（不再寫死 `~/.claude`） |
| `secret_mask.py` | 機密遮罩 |
| `pause_ctl.py` | 暫停旗標與程序檢查（重資源排程用）；**適配**（2.2.1-ds.1 才真的改；2.2.0-ds.1 寫了但檔案沒動）：說明改成 DSH 沒有 hook、旗標要 worker 自己讀（`pause_ctl.py status` 或 `dsh_guard.py --pause-flag`）、總監審查時核對 |
| `audit_log.py` | hash chain 的 verify／head／cite／recover��append 是 hook 用，DSH 不用） |
| `vocabulary.json` | worker 可填的狀態用詞 |

**新增（DeepSeek Harness 版）**

| 工具 | 用途 |
|---|---|
| `dsh_usage.py` | 讀 session 紀錄：每日／每 session 的 input/output/cache tokens、最後 prompt 大小、上下文百分比、effort |
| `dsh_audit.py` | 從 session 紀錄重建動作 audit（相容 `report_vs_audit.py` 與 `audit_log.py` 的 hash chain）；2.2.1-ds.1 起第 1 行 `kind=rebuild`，同上游 `transcript_audit.py` |
| `dsh_doctor.py` | 環境自檢：Python、Node、session 目錄、模型設定、沙箱、git、工具齊全 |
| `dsh_setup_check.py` | DIRECTOR 建置檢查（取代舊 setup_check 的 PO_PAGE_URL 檢查）；2.2.1-ds.1 加上游 2.2.1 的 shadow 檢查與 `--strict` |
| `dsh_guard.py` | 風險指令的**自我提醒**（沒有 hook，不是自動阻擋） |
| `selftest_ds.py` | 這版工具的冒煙測試（不重寫上游 selftest） |

**移除（Claude 專用）**

`hook_guard.py`、`setup_project_settings.py`、`context_probe.py`、`usage_report.py`、`usage_mix.py`、`doctor.py`、`setup_check.py`、`choice_reconcile.py`、`browser_check.py`、`poll_hint.py`、`selftest.py`、`container/`。

## 6. 範本變更

- 新增 `templates/AGENTS_PROJECT_SECTION.md`（原 `CLAUDE_PROJECT_SECTION.md` 的 AGENTS.md 版）。
- `PO_PENDING.md` 改成「待決帳」：保留 ID／STATUS／QUESTION／OPTIONS／RECOMMENDED／IMAGES／SOURCE／ANSWER／RESOLUTION，移除網頁欄位，加註「用 `ask_user_question` 問」。
- `RESUME_STATE.md` 的 `SESSION_ID` 改 `AGENT_NAME`（子代理名稱）。
- `DIRECTOR_FILES.md`：`DIRECTOR_STATE` 去掉 `PO_PAGE_URL`／`PO_PAGE_PINNED`，加 `PENDING_METHOD`；`ACTIVE_WORKSTREAMS` 用子代理名稱；`BASELINE_METRICS` 用 `dsh_usage.py` 欄位；`GUARDS` 列 DSH 機制。
- `BRIEF.md`：開工說明改成開子代理，成本改成 DeepSeek Harness 帳號用量。
- `WORK_ORDER.md`／`TASK_REPORT.md`：MODEL/EFFORT 改新型別，`SESSION_ID` 改 `AGENT_NAME`。
- 移除 `choice_page.html`、`settings.runtime-guard.json`、`guard_sessions.json`。

## 7. 不移植（NOT_PORTED）與替代

| 沒搬過來的東西 | 為什麼 | 替代做法 | 風險 |
|---|---|---|---|
| PreToolUse hooks（hook_guard.py） | DSH 沒有 hook 機制 | 沙箱模式、核准政策、工單 SCOPE、`scope_check`、`dsh_audit`；`dsh_guard.py` 只提醒 | 命令層自動阻擋沒有；只能靠規則與事後檢查 |
| Artifact 私人頁面、置頂、留言叫醒 | DSH 沒有 Artifact | `ask_user_question`＋`PO_PENDING.md`＋聊天附圖 | 沒有常駐待決頁；PO 要在對話中被問 |
| choice 資料庫／收條／冪等 | 依附 Artifact | 本機帳的 open/answered/closed；同一題不重問 | 沒有自動去重與逾時標記 |
| 容器 worker／網路出口管制 | 平台不提供、Claude 版用 claude CLI | 無 | 沒有 OS 級隔離；不要當安全邊界 |
| 專案級外掛開關／plugin token 清單 | DSH 外掛是使用者層 | 只列清單給 PO；不改 | 無法為單一專案關外掛 |
| MEMORY.md 記憶索引 | DSH 沒有 | AGENTS.md 指示鏈＋DIRECTOR 檔案 | 記憶容量受 64 KiB 鏈限制 |
| 壓縮門檻 250000／context_probe | DSH 自動壓縮、視窗 1,048,576 | 用 `dsh_usage.py` 監看上下文 | 沒有專案級壓縮時機控制 |
| 額度重置喚醒 | DeepSeek 帳號沒有 Claude 的 5h／週視窗 | 中斷後恢復程序（docs/06b） | 沒有「額度快用完自動停」機制 |
| interrupt_agent／session 封存 | 本 profile 未掛載 | `send_message` 請 worker 停在安全狀態 | 失控時要 PO 在 GUI 中止 |
| 子代理中途改 effort | DSH 限制 | 開接班子代理 | 多一次交接成本 |
| reviewer 只給讀取工具 | 子代理預設全工具；preset 屬使用者層 | 指示只准讀＋`dsh_audit.py` 核對 | 靠信任與事後檢查 |
| 上游 selftest.py（527 KB） | 大量 Claude 專用測試 | 新寫 `selftest_ds.py` 冒煙測試 | 覆蓋率比上游低 |
| 上游 `transcript_audit.py`（2.2.1） | 它讀 Claude Code 的 transcript（`~/.claude/projects`），DSH 沒有這種檔 | `dsh_audit.py` 本來就從 DSH session 紀錄事後重建；2.2.1-ds.1 起寫同樣的 `kind=rebuild` 第 1 行 | 無新增風險；兩者的 result 雜湊都不能和 hook 紀錄比 |

## 8. 驗證結果

驗證環境（2026-11-12）：DSH 0.2.2-rc.2、模型 deepseek-flash（effort max，子代理 high）、bundled Python 3.12.14、Node 24.21.0、git 2.55.0、sandbox danger-full-access、approval never、Asia/Taipei。

**8.1 端到端 demo（真的派工、交件、裁決，不是只跑工具）**

- 示範專案 `_work/demo-project`（git，master@91d4765843，add/subtract calculator）＋總監檔 `_work/demo-director/DIRECTOR`。
- 工單 `WO-001-add-multiply` rev2（SCOPE 3 檔、AC-1 AUTO、AC-2 REVIEW、Standard 級、CHECKS `python -X utf8 -m unittest -v test_calculator`）：`gate_check --order` OK，`ORDER_SHA256=2650e5b62c1892cf67bba3bda67f9d94aae3ea4016f04b0b37b979d2177a2fa5`。
- 用 `subagent` 開 worker `w1`（cwd=demo-project、effort high），全程只給工單路徑＋RESUME_STATE 路徑＋限制。w1 交件：分支 `demo/w1-multiply`、HEAD `d675820dfc9a27638951cb00ebc22729a37d2fdb`、evidence `20261112T232016-AC-1.json`、TASK REPORT/RESUME_STATE 齊全，並用 `send_message` 回報。
- 總監獨立複核（每項親跑，不採信宣稱）：
  - `gate_check --order` → OK；`--hash` → 2650e5b6…（與 DISPATCH 一致）；`--match`（+evidence-dir+dispatch-log+candidate）→ OK；`--verdict` → OK。
  - `scope_check --order --repo --candidate` → `SCOPE_CHECK: PASS base=91d4765843 changed=3 forbidden=0 outside=0`。
  - `evidence_record verify --rerun` → `EVIDENCE_VERIFY: OK integrity=same test=passed artifacts=2 missing=0 rerun=yes`，並取得 `EVIDENCE_RERUN WO-001 AC-1 candidate=d675820… result=ok record=20261112T232016-AC-1.json`。
  - `dsh_audit build --session w1` → 141 筆 hash-chain 動作紀錄；`dsh_audit verify` → `AUDIT_VERIFY … entries=141 head_seq=141 OK`。
  - `report_vs_audit --report … --log …` → `REPORT_VS_AUDIT: PASS claims=8 ok=8 failed=0`（第一輪 5/8 失敗，暴露工具在 DSH 包殼下的比對缺口，修好後重跑；報告的 RAN 行也依工具限制補正）。
  - 裁決 `reviews/GATE_VERDICT-WO-001.md`：PASS → ACCEPT_AND_CLOSE，DD-03 登記；分支保留、**NO MERGE / NO PUSH / NO FINAL ACCEPTANCE**。
- 這次 demo 同時驗證：待決帳＋`ask_user_question`、DIRECTOR 建置、工單 gate、子代理派工、TASK REPORT/RESUME_STATE、證據重跑、動作紀錄對報告、裁決、決策登記、`dsh_setup_check`。

**8.2 工具鏈**

- `selftest_ds.py` → `SELFTEST_DS: PASS tests=11 pass=11 fail=0 skip=0`（工具 `--help` 全掃、18 個真實 session、最新 log 的 audit build+verify、DSH 包殼／絕對路徑／截斷 claim 的 report 比對、setup fixture、status.py 產生、doctor、guard、gate hash、evidence run+verify）。
- `dsh_doctor.py` → `DSH_DOCTOR: PASS checks=12 ok=12 warn=0 fail=0`（Python、Node、DSH home、session、投影快取、profile 模型/effort、沙箱/核准、git、工具/文件/範本）。
- `dsh_usage.py --session w1` → TURNS 2、INPUT 122.7k、OUTPUT 37.5k、CACHE_R 2.69M、TOTAL 2.85M、LAST 113.4k、CTX% 10.8、EFFORT high、MODEL deepseek-flash；`--project-dir <WS>` 列出 18 個 session（含各研究子代理）。
- `dsh_setup_check.py` 對 demo DIRECTOR → `DSH_SETUP_CHECK: PASS problems=0`。
- `dsh_guard.py --command "git push origin main"` → `REMIND … G02 push …` exit 1；安全指令 exit 0。

**8.3 子代理平台**

- probe：子代理 session 會載入 cwd 的 AGENTS.md；可用 `pwsh`/`read`/`write` 等；子代理可 `send_message` 給總監（實測收到 `PROBE1_TO_LEAD_OK`）；同一 session 可續談（w1 補正 RAN 就是續談）。
- 限制實測：子代理不能 `ask_user_question`（DELEGATED_CALLER）、不能開 schedule；reviewer 無法 per-child 限工具（改用指示＋audit 事後核對）。

**8.4 文件**

- 每輪必讀四份（docs/01+03+06+08）實測 10,947 bytes，預算 11,000。
- demo 實際使用 `templates/WORK_ORDER.md`、`TASK_REPORT.md`、`GATE_VERDICT.md`；`gate_check --verdict` 驗過裁決格式。
- `docs/11`、`BOOTSTRAP`、`docs/04` 的 `dsh_usage`／`dsh_audit` 指令照文件跑得通；實測後修正了 `--project-dir` 的語意（子代理 session 記在總監啟動資料夾，不在 worker repo）與 `RAN` 截斷規則。

## 9. 已知限制

- **每輪必讀預算調高**：上游 docs/01+03+06+08 合計 9,549 bytes（上限 9,550）；DeepSeek 版改寫後實測 **10,947 bytes**（01_roles_authority 2,295＋03_communication 3,281＋06_resume_lossless 1,981＋08_safety_rules 3,390），上限定為 11,000 bytes。這是平台名詞與限制的必要說明，不是新增規則；DSH 版沒有上游 selftest 檢查這個上限，改大時要說明理由並把細節搬去 docs/11。
- 移植版本對應上游 2.2.1（2.2.1-ds.1 起，現為 2.2.1-ds.3；上游 2.2.1 只改工具，沒有改規則文件）；上游之後的規則變更要手動跟（見第 10 節）。
- 用量與動作紀錄依賴 DSH session 檔格式（`session.v4.jsonl.zstd`）；DSH 升版改格式時要更新 `dsh_usage.py`／`dsh_audit.py`。
- 模型只有 deepseek-flash；沒有任何「換更強模型」的選項，只能用 effort 與拆工。
- 章節與範例中的歷史數字（原專案量到的）沿用，換平台後要自己重量。
- `dsh_audit.py` 的 input 經 `secret_mask` 後最多記 500 字，長指令尾端會截斷；TASK REPORT 的 `RAN` 要在截斷處用 `...`，否則 `report_vs_audit` 對不上（這條已寫進 docs/02 與範本）。
- 子代理的 session log 記在總監 session 的啟動資料夾下（`--project-dir <worker repo>` 抓不到）；要抓單一工作線用 `dsh_audit/dsh_usage --session <agent>`（已寫進 docs/11）。
- `dsh_audit.py` 需要 Node 22+（zstd 解壓）；bundled Node 24.21.0 實測可用。

## 10. 跟上游同步

1. 看 `CHANGELOG-upstream.md` 的該版變更，只搬「規則、工單格式、gate、證據、續航、初衷卡」這類平台中立的變更。
2. 平台層（docs/04、05、11、12、BOOTSTRAP 的 DSH 段落、tools/dsh_*.py）以本版為準，不要直接覆蓋。
3. 每次搬完跑 `tools/selftest_ds.py`，並在 `CHANGELOG.md` 記一筆。
4. 發版用 `python -I -X utf8 tools/release.py`（2.2.1-ds.3）：預設只演練（dry run），檢查和 origin/main 的落後／分岔、VERSION 和 CHANGELOG 最上面一段相同且比遠端所有 tag 新、selftest、公開掃描（金鑰、私人 email、私人路徑、DIRECTOR/、_work/、session 檔）；加 `--execute` 才 push、打 tag、建 GitHub Release，每步用 `ls-remote`／`gh release view` 確認。發版仍要 PO 核准。

## 11. ds.2 起 DeepSeek 版自己加嚴的規則（上游沒有）

- 規格先行（SDD）：Standard／Strict 工單要有 OpenSpec 變更、鎖定的驗收測試、Standard 也做規格審查、計畫閘門、≤3 檔約 200 行、停止規則 1 輪（`docs/13`）。
- 理由：上游的品質靠 Opus 的判斷力與 Claude Desktop 機制；DSH 版的 worker 是 `deepseek-flash`，DSH 沒有 hook、子代理不能中途改 effort，所以把判斷前移到派工前。
- 跟上游同步時，`docs/02` 的「規格先行」一節、`templates/WORK_ORDER.md` 的 `SPEC_CHANGE`／`TESTS_LOCKED`／計畫閘門、`tools/sdd_gate.py` 和 `gate_check.py`／`scope_check.py` 的 ds.2 呼叫點以本版為準；上游改到同一段時手動合併。
