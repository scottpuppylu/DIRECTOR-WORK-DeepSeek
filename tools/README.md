# tools — DIRECTOR-WORK DeepSeek（DSH）版

Python 3.9 以上，只用標準函式庫。一律用 bundled Python 執行：`python -I -X utf8 <tool>.py ...`
（`-I` 不從目前資料夾載入模組；執行檔路徑見 `docs/11`）。每支都有 `--help`，沒有寫死的本機路徑。
完整 CLI 契約、與上游的差異、已知限制看 [`DSH-TOOLS.md`](DSH-TOOLS.md)。

DSH 沒有 hooks、沒有 PO 頁、沒有 Claude 額度查詢；所以**沒有東西會自動跑**：用量、動作紀錄、環境檢查都是事後由總監或 worker 手動執行，`dsh_guard.py` 只是自律檢查，不是攔截器。

## DSH 新增

| 工具 | 做什麼 | 寫檔 |
|---|---|---|
| `dsh_session.py` | 共用庫（無 CLI）：找 Node、解 session `*.jsonl.zstd` 的 zstd frames、列 session、從父 catalog 對 agent 名稱、讀投影快取 | 不寫 |
| `dsh_usage.py` | 每 session 的 input/output/cacheRead/cacheWrite、最後 prompt tokens、context 使用率、effort/model、每日彙總 | `--out` 才寫 |
| `dsh_audit.py` | 從 session 事件重建有雜湊鏈的動作紀錄，給 `report_vs_audit.py`／gate 審查用；`verify` 檢查鏈與錨點，`cite` 印報告要引的區段。2.2.1-ds.1 起第 1 行是 `kind=rebuild`（記來源 session 檔名、sha256、大小），工具呼叫從 seq 2 起 | `build` 寫一份 JSONL，不覆蓋舊的 |
| `dsh_doctor.py` | 12 項環境檢查：Python、Node、DSH home、session log、投影快取、profile 模型/effort、沙箱/核准、git、工具/文件/範本齊不齊 | 不寫 |
| `dsh_setup_check.py` | 建置完成的檢查：BOOTSTRAP 產出的 DIRECTOR 資料夾（必要檔案、PENDING_METHOD、PO_PENDING、RESUME_STATE 標頭、director_work.json）；2.2.1-ds.1 起另有 shadow 檢查（ID 重複、RESUME 標頭有值與 UPDATED 日期、director_work.json 欄位型別與 regex），印 `~ shadow:`，`--strict` 才算失敗 | 不寫 |
| `dsh_guard.py` | 動手前的自律檢查：force push、push、刪除、送出/發布、付款、改設定、秘密、永遠禁止的 git/程序模式、PAUSE 旗標；預設只提醒 | 不寫 |
| `sdd_gate.py` | ds.2 規格先行的膠水（OpenSpec 沒有的部分）：`gate_check.py`／`scope_check.py` 載入它來查 `SPEC_CHANGE`＋`openspec validate --strict --json`、`TESTS_LOCKED` 雜湊、`SPEC_REVIEW`／`PLAN_APPROVED` 紀錄、工單大小、STOP_RULES 輪數；CLI：`--lock-tests`、`--plan-hash`、`--which`（`docs/13`） | 不寫 |
| `selftest_ds.py` | 離線冒煙測試整組工具（help、usage、audit+report、setup fixture、status 產生、doctor、guard、gate hash、evidence、報告比對、SDD gate 正反案例） | 只寫暫存資料夾 |

## 上游保留（跨平台，已適配 DSH）

- `gate_check.py`：檢查 RESUME_STATE／工單／TASK REPORT／裁決的欄位與用詞；`--match` 逐條對報告與工單 AC、`--evidence-dir` 核證據、`--hash` 印派工雜湊、`--verdict` 驗裁決。ds.2：Standard／Strict 工單另查 SDD 規則（`--repo <專案>`、`--config director_work.json`）。
- `scope_check.py`：比對實際改動與工單 SCOPE／FORBIDDEN。ds.2：Standard／Strict 工單另查大小上限（`OVERSIZE`）。
- `evidence_record.py`：跑驗收指令，留下 exit code、輸出尾段、產物 SHA-256；`verify --rerun` 可重跑。
- `report_vs_audit.py`：拿 RAN 與 TESTS／EVIDENCE／DONE 的指令對動作紀錄（DSH 包殼指令會先剝殼再比；比對不到就 FAIL，不會亂放行）。2.2.1：被截在 500 字的行會照 JSON 字串解回引號與反斜線，長的 Windows 路徑指令也對得上；單字比對至少要 2 個不是 `...`／`<名稱>` 的字；讀到 `kind=rebuild` 的紀錄會印一行 note。
- `trace_report.py`：產生需求 → 工單 → AC → 證據 → 裁決的追溯表。
- `round_check.py`：修正輪數檢查（第 4 輪起要根因研究）。
- `status_gen.py`：產生一條工作線的 `status.py`；總監版加待決帳計數、未結案工單、近 1 小時動作紀錄（已改吃 `po_pending`、無 pending_sends／processes）。
- `metrics_report.py`：從 DIRECTOR 檔案數成效數字。
- `memory_size_check.py`：指示鏈大小（預設找最近的 `AGENTS.md`，`--max-bytes 65536`）。
- `secret_mask.py`：把私鑰、token、API key、JWT、`password=` 這類值遮成 `[MASKED:種類]`。
- `pause_ctl.py`：暫停開關（寫／移除 `<DIRECTOR>/PAUSE` 並記 LOG 一行）。
- `audit_log.py`：動作紀錄格式的來源；DSH 只用它的 `verify`／`head`／`cite`／`recover`（`append` 是 Claude hook 用的，DSH 不呼叫）。
- `vocabulary.json`、`guard_rules.json`：固定用詞與 `dsh_guard.py` 的規則檔。

## 已移除（Claude 專屬）

`hook_guard.py`（規則留在 `guard_rules.json`）、`setup_project_settings.py`（改 `.claude/settings.local.json`）、
`context_probe.py`、`usage_report.py`、`usage_mix.py`、`doctor.py`、`setup_check.py`、
`choice_reconcile.py`、`browser_check.py`、`poll_hint.py`、`selftest.py`、`container/`。
理由：DSH 沒有 hooks、Artifact 私人待決頁、Claude 方案額度或容器 worker；對應能力改用 `ask_user_question`＋`PO_PENDING.md`、`dsh_usage.py`、子代理共享 checkout。

## 常用指令

```text
# 總監：重建 worker 的動作紀錄、核對報告
python -I -X utf8 tools/dsh_audit.py build --session w1 --out DIRECTOR/research/audit-2026-11-12.jsonl
python -I -X utf8 tools/report_vs_audit.py --report _work/demo-worker/TASK_REPORT.md --log DIRECTOR/research/audit-2026-11-12.jsonl --utc-offset +08:00

# 總監：環境與建置檢查
python -I -X utf8 tools/dsh_doctor.py
python -I -X utf8 tools/dsh_setup_check.py DIRECTOR

# 總監：用量（--project-dir 比對 session 啟動資料夾；單線用 --session <agent>）
python -I -X utf8 tools/dsh_usage.py --project-dir <WS>
python -I -X utf8 tools/dsh_usage.py --session w1 --json

# worker／總監：動手前自律檢查
python -I -X utf8 tools/dsh_guard.py --command "git push origin main" --profile worker

# 總監：規格先行（ds.2，docs/13）
python -I -X utf8 tools/sdd_gate.py --which --config DIRECTOR/director_work.json
python -I -X utf8 tools/sdd_gate.py --lock-tests tests/test_parser.py --repo <專案>
python -I -X utf8 tools/gate_check.py --order DIRECTOR/orders/WO-002.md --repo <專案>
python -I -X utf8 tools/sdd_gate.py --plan-hash <專案>/openspec/changes/<名稱>/tasks.md --order DIRECTOR/orders/WO-002.md

# 全組冒煙測試（OPENSPEC_BIN 指到真的 openspec 時，sdd_real_openspec 才會跑，不然 SKIP）
python -I -X utf8 tools/selftest_ds.py
```

## 限制

- `dsh_audit.py` 的 input 經 `secret_mask` 後最多記 500 字，長指令尾端會被截斷；TASK REPORT 的 `RAN` 在截斷處用 `...` 表示，否則對不上。
- 子代理 session 記在總監 session 的啟動資料夾下，`--project-dir <worker 的 repo>` 抓不到；用 `--session <agent>`。
- `dsh_usage.py` 讀投影快取（寫入可能落後幾百筆事件或幾秒），`--from-jsonl` 可強制讀原始 log。
- `dsh_audit.py` 需要 Node 22+（zstd）；`dsh_doctor.py` 會確認。
- `dsh_guard.py` 只檢查指令文字，不是攔截器；真正擋檔案的是 DSH 沙箱，核准政策是 session 設定。
