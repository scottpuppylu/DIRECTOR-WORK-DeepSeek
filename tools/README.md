# tools — DIRECTOR-WORK DeepSeek（DSH）版

Python 3.9 以上，只用標準函式庫。一律用 bundled Python 執行：`python -I -X utf8 <tool>.py ...`
（`-I` 不從目前資料夾載入模組；執行檔路徑見 `docs/11`）。每支都有 `--help`，沒有寫死的本機路徑。
完整 CLI 契約、與上游的差異、已知限制看 [`DSH-TOOLS.md`](DSH-TOOLS.md)。

DSH 沒有 hooks、沒有 PO 頁、沒有 Claude 額度查詢；所以**沒有東西會自動跑**：用量、動作紀錄、環境檢查都是事後由總監或 worker 手動執行，`dsh_guard.py` 只是自律檢查，不是攔截器。

## DSH 新增

| 工具 | 做什麼 | 寫檔 |
|---|---|---|
| `dsh_session.py` | 共用庫：找 Node、解 session `*.jsonl.zstd` 的 zstd frames、列 session、從父 catalog 對 agent 名稱、讀投影快取。2.2.4-ds.4 唯一的 CLI：`--temp-env <WORK_DIR>` 建 `WORK_DIR/tmp`，印出把 TEMP／TMP／TMPDIR 指過去的 PowerShell 與 bash 設定行 | `--temp-env` 只建 `WORK_DIR/tmp` |
| `dsh_usage.py` | 每 session 的 input/output/cacheRead/cacheWrite、最後 prompt tokens、context 使用率、effort/model、每日彙總。2.2.4-ds.4：`NO_DATA` 時 `--out` 也寫檔（`status`、`reason`、`hints`；exit 仍是 2，之前不寫檔）；`--project-dir` 指到啟動資料夾底下時印 `HINT` 指出上層的啟動資料夾；`--effort-check <工單>` 印 `EFFORT_ACTUAL` 行，session effort 和工單不同印 shadow WARN | `--out` 才寫 |
| `dsh_audit.py` | 從 session 事件重建有雜湊鏈的動作紀錄，給 `report_vs_audit.py`／gate 審查用；`verify` 檢查鏈與錨點，`cite` 印報告要引的區段。2.2.1-ds.1 起第 1 行是 `kind=rebuild`（記來源 session 檔名、sha256、大小），工具呼叫從 seq 2 起 | `build` 寫一份 JSONL，不覆蓋舊的 |
| `dsh_doctor.py` | 12 項環境檢查：Python、Node、DSH home、session log、投影快取、profile 模型/effort、沙箱/核准、git、工具/文件/範本齊不齊 | 不寫 |
| `dsh_setup_check.py` | 建置完成的檢查：BOOTSTRAP 產出的 DIRECTOR 資料夾（必要檔案、PENDING_METHOD、PO_PENDING、RESUME_STATE 標頭、director_work.json）；2.2.1-ds.1 起另有 shadow 檢查（ID 重複、RESUME 標頭有值與 UPDATED 日期、director_work.json 欄位型別與 regex），印 `~ shadow:`，`--strict` 才算失敗；2.2.2-ds.3 加 RESUME_STATE 大小（RESUME_SIZE）和 `resume`／`base_ref`／`release` 區塊的型別檢查 | 不寫 |
| `dsh_guard.py` | 動手前的自律檢查：force push、push、刪除、送出/發布、付款、改設定、秘密、永遠禁止的 git/程序模式、PAUSE 旗標；預設只提醒 | 不寫 |
| `safety_gate.py` | 安全閘門（ds.2 `sdd_gate.py` 改名，2.2.5-ds.5 拿掉 OpenSpec，docs/13）：`--lock-tests` 印工單的 `TESTS_LOCKED:`、`--plan-hash` 印 `PLAN_APPROVED` 行；`gate_check.py` 用它查鎖定測試、PLAN.md、SPEC_REVIEW、輪數、安全開關不得自行關閉；也讀 `order_limits`／`protected_tests` 給 `scope_check.py`。舊的 `sdd` 區塊照讀：安全開關印「請搬到 safety」，OpenSpec 的鍵印「此鍵被忽略」 | 不寫 |
| `bootstrap_repo.py` | 2.2.3-ds.3 BOOTSTRAP 10.5 的機械步驟：把 `.memsearch/` 加進 `<REPO>/.git/info/exclude`。做過的跳過，`--check` 只報告。2.2.5-ds.5：`--config` 只讀，舊設定的 `sdd` 區塊只印 WARN，不找、不裝、不寫任何 CLI（L-061） | 只寫 exclude |
| `release.py` | 2.2.2-ds.3 發版一次到位：fetch → 比對 origin/main（落後／分岔／領先；分岔加 `--merge` 開 `release/<版本>` 合併，有衝突就停並列檔名）→ 工作樹有沒 commit 的 tracked 檔就停 → VERSION 與 CHANGELOG（都從 HEAD 讀）最上段一致、tag 排序高於遠端所有 tag（2.2.3-ds.3 起比「(上游版本, ds 序號)」整組，ds 序號不單獨比） → selftest → 公開掃描（金鑰、私人 email、使用者路徑、DIRECTOR/、_work/、session 檔）→ push → tag → `gh release create`，每步用 ls-remote／`gh release view` 驗。預設 dry run，`--execute` 才動遠端 | 只有 `--execute` 動遠端；`--merge --execute` 開本機分支 |
| `verify_dsh_run.py` | 2.2.2-ds.3 DSH 試跑驗證器（由 ds.2 的 WO-101 `verify_run.py` 通用化）：R01–R21 看 repo（候選 commit、各階段改了哪些檔、鎖定測試雜湊、總監重跑測試與隱藏 oracle、gate_check、evidence 重跑、DIRECTOR_LOG），D01–D14 看 DSH session 紀錄（模型、寫入範圍、禁止動作、偷看隱藏測試、閘門、測試先寫、report_vs_audit）。工單專屬的檔名、代理名、oracle 寫在設定檔（`templates/VERIFY_DSH_RUN.json`）；單元測試 `test_verify_dsh_run.py` | 只寫 `--out` 資料夾 |
| `selftest_ds.py` | 離線冒煙測試整組工具（help、usage、audit+report、setup fixture、status 產生、doctor、guard、gate hash、evidence、報告比對、worktree、--final 用量檢查） | 只寫暫存資料夾 |

## 上游保留（跨平台，已適配 DSH）

- `gate_check.py`：檢查 RESUME_STATE／工單／TASK REPORT／裁決的欄位與用詞；`--match` 逐條對報告與工單 AC、`--evidence-dir` 核證據、`--hash` 印派工雜湊、`--verdict` 驗裁決。ds.2 起 Standard／Strict 工單另查安全閘門（`safety_gate.py`；`--repo <專案>`、`--config director_work.json`）。2.2.5-ds.5：拿掉 OpenSpec 檢查；`--final <DIRECTOR>` 找不到 `usage.json` 印 `~ WARN USAGE`；`--report-skeleton` 的 `WORKTREE:` 行由 `git worktree list` 產生。2.2.2-ds.3：`--order` 先 `git fetch` 再比 BASE_REF 與遠端分支，落後或不存在印 `~ WARN BASE_REF`，`--strict-base` 判不過，fetch 失敗會明說沒比對；`base_ref` 開關型別錯會印 note 並用預設（同上游 2.2.2）。`--resume` 檔案超過 `resume.max_bytes`／`resume.max_line_bytes`（預設 20480／4096）印 `~ shadow: RESUME_SIZE`，`--strict` 判不過。`--report-skeleton 工單 [--repo] [--out]` 印出照工單填好欄位、雜湊和每條 AC 一列的 TASK REPORT 骨架，以及錄證據、scope_check、`--match` 的完整指令（DSH worker 不用讀原始碼學格式；docs/13「省 token」）。2.2.4-ds.4：`--order` 的 CHECKS 反斜線路徑指出第幾行並建議改正斜線；`--match` 的 Standard／Strict 沒有 SPEC_REVIEW 一律判不過（沒給 `--dispatch-log` 就找 DIRECTOR_LOG.md 和 `reviews/`），報告 `PROTECTED_CHANGED` 對 diff，`--dispatch-log` 的 `EFFORT_ACTUAL` 和工單 effort 不同印 shadow WARN；骨架對有 WORK_DIR 的工單印 TEMP 設定行。2.2.4-ds.4（上游 2.2.4）：`--after-verdict <裁決.md>... --repo <專案> [--orders <工單資料夾>] [--strict]` 解出每份裁決的 `CANDIDATE_HEAD:`，取其他候選都在它之前的那份當最後一份；從它到 HEAD 的 commit 改到該工單 SCOPE 外、又不是文件（`DIRECTOR/` 底下、`.md`／`.rst`／`.txt`）的檔，印 `~ WARN LATE_COMMIT <sha> <標題>: <檔案>`（shadow，exit 不變），`--strict` 判 FAIL；工單依序在 `--orders`、裁決所在資料夾、`../orders` 找，找不到就把每個非文件的檔都算進去；候選解不出或 HEAD 不含候選印 `NOT_CHECKED`，不當作通過。只讀 git。
- `scope_check.py`：比對實際改動與工單 SCOPE／FORBIDDEN。ds.2：Standard／Strict 工單另查大小上限（`OVERSIZE`）。2.2.4-ds.4：上限讀頂層 `order_limits`（舊 `sdd.max_*` 照讀並印 shadow WARN「請搬到 order_limits」），測試檔行數另算 `max_test_lines_per_order`；共用 checkout（`--shared` 或工單 WORKTREE 寫「共用」）只算 commit 訊息有工單編號的 commit 和 SCOPE 內未 commit 的檔，別人的檔印 `OTHER`；受保護的測試（TESTS_LOCKED、`protected_tests`）只准新增或在檔尾加，改到原有內容印 `PROTECTED`，並印 `PROTECTED_CHANGED:` 給報告照抄。
- `evidence_record.py`：跑驗收指令，留下 exit code、輸出尾段、產物 SHA-256；`verify --rerun` 可重跑。2.2.3-ds.3（上游 2.2.3，原樣搬）：`CHECKS:` 的程式只寫 `git` 也可以，但只限唯讀子指令（diff、show、log、status、rev-parse、ls-files、cat-file），子指令前的選項、其他子指令、會寫檔或執行程式的選項（`--output`、`--ext-diff`、`--textconv`、`--filters`、`--no-index`，縮寫也算）一律 `NOT_RUN`、exit 2；git 檢查在 `--repo` 頂層跑，關掉 replace 物件、fsmonitor、pager、optional locks、外部 diff 和 textconv，跑完照樣重讀 repo（docs/02「AC 用 git」）。
- `report_vs_audit.py`：拿 RAN 與 TESTS／EVIDENCE／DONE 的指令對動作紀錄（DSH 包殼指令會先剝殼再比；比對不到就 FAIL，不會亂放行）。2.2.1：被截在 500 字的行會照 JSON 字串解回引號與反斜線，長的 Windows 路徑指令也對得上；單字比對至少要 2 個不是 `...`／`<名稱>` 的字；讀到 `kind=rebuild` 的紀錄會印一行 note。2.2.3-ds.3（上游 2.2.3）：換行、`;`、`&&`、`||` 切段，多段主張對得到多行腳本（順序要一樣），`RAN:` 下面用 ``` 包的一段算一個主張；`at=13:17（備註）` 只取時間、主張裡的全形（備註）不比；`AC-1/AC-2`、`AC-1/2`、`AC-1..AC-3` 每個編號都要有一筆，缺的會點名；有省略的主張（`...`、`427fcef...`、「同上」）可跳過紀錄裡的選項、對到開頭相同的詞，`wo-003` 對到以它開頭再接 `-`／`_`／`.` 的檔名；被截的紀錄行，3 個詞一路對到行尾也算；比到幾筆時顯示最接近 `at=` 的那筆；exit 對不上但那筆後面還跑了別的指令，印「not checkable」算 OK。兩種 shadow WARN（exit code 不變）：`RAN:` 有一行沒有 `` `指令` ``；報告寫 `SCOPE_CHECK: PASS`，但做事的 agent 最後一次 commit 之後沒有再成功跑過 `scope_check.py`。WO-DS-004 的 DSH 報告：舊版 FAIL 6 條、新版 PASS 11/11。2.2.4-ds.4（上游 2.2.4，原樣搬）：變數會展開（`$X`、`${X}`、`$env:X`、`%X%`、PowerShell 的 `a + b`、here-string；同一 agent 前面設的延用到後面的呼叫）；`git -C DIR x` 當成 `cd DIR` 再 `git x`；字中的 `...`／`…` 代表任意字；短 hex 對長 sha 的開頭；主張的絕對路徑對紀錄的相對路徑；`at=HH:MM:SS` 和 `at=HH:MM–HH:MM` 區間；`AC-1 .. AC-6`；選項順序不同也對得上（完整主張要列齊每個選項）；全形 `；` 斷句、CJK 字之間的詞當備註；多段主張分在幾次呼叫跑也算（順序要一樣）；``` 從 RAN: 外開的區塊在那裡就結束；主張在任何呼叫都找不到、但可能在另一條主張對到的截斷呼叫被截掉的那段時，印 `UNVERIFIED`（in log cut part）：獨立狀態，不算 OK、也不算 FAIL，最後一行另計 `unverified=n`（放在最後），exit code 不變，審查的人要自己看這幾條；在截斷呼叫留下來的那段就對得到的主張仍是 OK；PowerShell 這類從不回報 error 的工具，exit 對不上印 not checkable。沒人跑過的指令照樣 FAIL。WO-DS-006 三組報告：FAIL 64 → 0（其中 18 條 UNVERIFIED）。
- `trace_report.py`：產生需求 → 工單 → AC → 證據 → 裁決的追溯表。
- `round_check.py`：修正輪數檢查（第 4 輪起要根因研究）。
- `status_gen.py`：產生一條工作線的 `status.py`；總監版加待決帳計數、未結案工單、近 1 小時動作紀錄（已改吃 `po_pending`、無 pending_sends／processes）。2.2.4-ds.4（上游 2.2.4，L-059）：一行超過 `width` 時頭尾都留，行內最長路徑（路徑太短就整行）的中段換成 `…`，行尾的狀態字（OK、LOW、計數）不再被切掉；已產生的 `status.py` 要用 `--force` 重新產生。
- `metrics_report.py`：從 DIRECTOR 檔案數成效數字。
- `memory_size_check.py`：指示鏈大小（預設找最近的 `AGENTS.md`，`--max-bytes 65536`）。2.2.2-ds.3（上游 2.2.2）：`--kind resume` 量 RESUME_STATE（整份 20480、單行 4096 bytes，`--config` 讀 `resume.*`），可給多個 `--file`、`--glob "<根>/**/RESUME_STATE*.md"` 或 `--workstreams ACTIVE_WORKSTREAMS.md`；一檔一行（OK／OVER、bytes、~token、最長行、可搬 bytes），最後 `SIZE: PASS|OVER|MISSING files=n over=n`，超過或找不到 exit 1，只讀。
- `resume_archive.py`：2.2.2-ds.3（上游 2.2.2，原樣搬）把 RESUME_STATE 的舊段落原文搬到同資料夾 `RESUME_HISTORY_<YYYYMMDD>.md`，原處留索引。預設 dry-run；`--execute` 先寫 `.bak`，搬完驗證 (a) 歷史檔逐字含搬走的內容 (b) 留下的部分 sha256 不變、表頭仍四行 (c) 搬走＋留下＝原檔，任何一項不過就還原並 exit 1。近期只用筆數算（`resume.keep_recent`，預設 10，沒有 keep_days）；表頭、現況、保護標題、沒日期的段落不動（docs/06b「RESUME_STATE 瘦身」）。
- `secret_mask.py`：把私鑰、token、API key、JWT、`password=` 這類值遮成 `[MASKED:種類]`。
- `pause_ctl.py`：暫停開關（寫／移除 `<DIRECTOR>/PAUSE` 並記 LOG 一行）。
- `audit_log.py`：動作紀錄格式的來源；DSH 只用它的 `verify`／`head`／`cite`／`recover`（`append` 是 Claude hook 用的，DSH 不呼叫）。
- `vocabulary.json`、`guard_rules.json`：固定用詞與 `dsh_guard.py` 的規則檔。

### 上游 DW 2.2.5 移植（2.2.5-ds.5，WO-DS-009 B7）

- `ran_line.py`（新，上游原樣搬）：`--to 報告 -- 指令` 代跑並寫一行 RAN（exit code 照傳）；`--exit N --cmd "指令"` 剛跑完補記；`--stamp [--to 檔 --text ...]` 印或加一行 `YYYY-MM-DD HH:MM`。時間取時鐘，不手打。設了 `WORK_DIR` 時暫存檔放 `WORK_DIR/tmp`。
- `gate_check.py`：`--sequence 工單… --dispatch-log DIRECTOR_LOG.md --repo <checkout>`（PLAN_APPROVED 早於 worker 第一個 commit、每張工單有自己的 SPEC_REVIEW、審查與裁決來自別的 session）；`--after-verdict` 預設 FAIL（裁決後改到程式碼，SCOPE 內也算；只改文件放行；`--warn` 回到 WARN）；`--final <DIRECTOR>`：`evidence/E2E/` 沒有非空檔 FAIL，缺 `ENTRY_POINT:`、DD 沒「驗收案例」印 WARN，再加 DS 的 usage.json 行（`~ WARN USAGE`）；git 的 `Filename too long` 印一行寫明路徑和超過多少；BASE_REF 括號裡的字當註解。
- `scope_check.py`：印 `WORKTREE:` 行（`git worktree list`；`dsh_session.py --worktree-status`、`--report-skeleton` 用同一個函式）；BASE_REF 括號當註解；長路徑一行訊息；任何錯誤 `SCOPE_CHECK: NOT_RUN`，不印 Traceback。`--shared` 是 ds.4 B2，上游 2.2.5 搬回去的就是這一份。
- `report_vs_audit.py`：H1 誤報修正（全形 `～` 區間、只設 TEMP／TMP／TMPDIR／PYTHONIOENCODING／PYTHONUTF8 的句子不比、相對路徑照該次呼叫的資料夾解開、`/d/x` 等於 `d:/x`、shell 函式展開、可少寫無害選項）；每條 FAIL 標類別（沒跑／時間不符／結束碼不符／格式），最後一行多 `time_mismatch=n not_run=n`；`--tolerance-min` 預設 10；`--lead 檔` 查 lead 自己寫的裁決、DIRECTOR_LOG 時間；最上層攔例外，exit 2 一行。
- `dsh_audit.py`（對應上游 `transcript_audit.py` 2.2.5）：`build` 預設整條 input 都記，不再截 500 字；`--input-limit N` 截過的行標 `input_cut`。`audit_log.summary(input, limit)` 跟著上游。
- `evidence_record.py`、`release.py`：設了 `WORK_DIR` 時，`tempfile` 和子行程的 TMPDIR／TEMP／TMP 指到 `WORK_DIR/tmp`（上游原樣搬）。
- 範本：`templates/weird_inputs.py`（怪檔案產生器）、`templates/HANDOFF.md`（worker 到輪數上限的交接）。
- 沒搬：`browser_check.py`（DS 本來就沒有）、上游 `selftest.py`（案例改寫進 `selftest_ds.py`）。

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

# 總監：安全閘門（docs/13）
python -I -X utf8 tools/safety_gate.py --lock-tests tests/test_x.py --repo <專案>
python -I -X utf8 tools/safety_gate.py --plan-hash <WORK_DIR>/WO-002/PLAN.md --order DIRECTOR/orders/WO-002.md

# 總監：工單閘門
python -I -X utf8 tools/gate_check.py --order DIRECTOR/orders/WO-002.md --repo <專案>
python -I -X utf8 tools/gate_check.py --after-verdict DIRECTOR/gates/WO-002-GATE.md --repo <專案>   # 2.2.4：裁決之後的未審 commit

# 總監：每個 worker 一個 worktree（2.2.5-ds.5）
python -I -X utf8 tools/dsh_session.py --worker-worktree <專案> --order WO-002 --branch wo-002 --base <BASE_REF 的 commit>
python -I -X utf8 tools/dsh_session.py --worktree-status <checkout>

# 收尾（2.2.5-ds.5）：最後一步寫用量，再跑 --final
python -I -X utf8 tools/dsh_usage.py --project-dir <WS> --out DIRECTOR/usage.json
python -I -X utf8 tools/gate_check.py --final DIRECTOR

# 全組冒煙測試
python -I -X utf8 tools/selftest_ds.py
```

## 限制

- `dsh_audit.py` 的 input 經 `secret_mask` 後最多記 500 字，長指令尾端會被截斷；TASK REPORT 的 `RAN` 在截斷處用 `...` 表示，否則對不上。
- 子代理 session 記在總監 session 的啟動資料夾下，`--project-dir <worker 的 repo>` 抓不到；用 `--session <agent>`。
- `dsh_usage.py` 讀投影快取（寫入可能落後幾百筆事件或幾秒），`--from-jsonl` 可強制讀原始 log。
- `dsh_audit.py` 需要 Node 22+（zstd）；`dsh_doctor.py` 會確認。
- `dsh_guard.py` 只檢查指令文字，不是攔截器；真正擋檔案的是 DSH 沙箱，核准政策是 session 設定。
- `report_vs_audit.py` 的 `UNVERIFIED` 要人看：工具只能說「可能在截斷處」，不能判斷有沒有跑。

### 已知限制（2.2.4-ds.4，Windows 長路徑，同上游 2.2.4）

- 路徑超過 260 字時 git 會報 `Filename too long`。工具不替你改設定，要自己跑一次 `git config --global core.longpaths true`。`selftest_ds.py` 開頭給整個 process 設 `GIT_CONFIG_COUNT`／`GIT_CONFIG_KEY_n=core.longpaths`／`GIT_CONFIG_VALUE_n=true`（原本有 `GIT_CONFIG_COUNT` 就接在後面），它叫起來的工具裡的 git 也吃得到；只在 selftest 裡設，tools 不變。
- GIT_DIR（`.git` 資料夾，或子模組在 `.git/modules/` 下的資料夾）超過約 220 字時，git 本身就停止（`'$GIT_DIR' too big`），`core.longpaths` 也沒用；只能把 repo 放在短一點的路徑。selftest_ds 沒有建子模組的測試，所以沒有這種 SKIP。
- 本機路徑當 remote（push、clone、fetch 到同一台電腦的另一個 repo）時，對方那一側的 git 不會繼承 `GIT_CONFIG_COUNT`／`GIT_CONFIG_PARAMETERS`（`git -c` 也一樣），要在對方 repo 裡設 `core.longpaths`，或用 `--global`；selftest_ds 建的 bare origin 就是這樣設。
