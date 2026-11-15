# 02 工單、Gate、報告與測試

## 規則

### 治理模式（依風險選）

- **Direct**：純查詢、文件、沒有風險。
- **Standard**：一般開發，可以回退。
- **Strict**：核心邏輯、資料格式、存檔、對外介面、跨分支整合、發布。
- 流程：`Baseline → Plan → Isolated Change → Build/Test → 成品檢查 → Evidence → Gate → Checkpoint`。

### 安全閘門（ds.2 起；2.2.5-ds.5 拿掉 OpenSpec；Standard／Strict）

完整流程和開關見 `docs/13_safety_gates.md`。下面每條都是 `director_work.json` 的 `"safety"` 開關，預設全開。

- **OpenSpec 已移除（2.2.5-ds.5）**：`SPEC_CHANGE`、`openspec validate`、`openspec_bin`、`require_spec_*` 不再使用。理由：WO-DS-008 r2 的隱藏測試，開 SDD 85/107、關 SDD 101/107，OpenSpec 本身沒有量到正確性效益。需求改寫在工單 ACCEPTANCE 和 `templates/WORK_ORDER.md` E 節的邊界與壓力清單。舊設定檔的 `"sdd"` 區塊照讀，安全開關印「請搬到 safety」，OpenSpec 的鍵印「此鍵被忽略」。
- **規格審查**：Standard 也必做（Claude 版只有 Strict）；`--match` 查 `SPEC_REVIEW <WO>` 那一行（`spec_review_for_standard`）。
- **測試先寫**：驗收測試在派工前寫好、commit 到 BASE_REF，用 `tools/safety_gate.py --lock-tests` 把雜湊寫進工單的 `TESTS_LOCKED:`，跑法寫進 `CHECKS:`。worker 不得改測試，改了 gate 判不過（`tests_first`）。
- **工單大小**：一張工單最後結果最多 3 個檔、約 200 行（新增＋刪除）；超過就拆。`scope_check.py` 印 `OVERSIZE` 並判越界（頂層 `order_limits`）。
- **計畫閘門**：worker 第一步只交 `<WORK_DIR>/<WO>/PLAN.md`（`- [ ] 1.1 …`），總監核准後在 `DIRECTOR_LOG` 寫 `PLAN_APPROVED <WO> sha=<64>`（`safety_gate.py --plan-hash` 印），worker 才可以寫程式；交件時 PLAN.md 只准比核准版多打勾，而且要全部勾完（`plan_gate`）。
- **停止規則**：同一根因 **1 輪**沒進展就停並回報（`stop_after_rounds`；Claude 版 2 輪）。
- **不得自行關閉**：lead 要對 Standard／Strict 關掉上面任一開關，或把 `stop_after_rounds` 調高到超過 1，先在 PO_PENDING 寫一項等 PO 回答；沒有 PO 的答覆，`gate_check.py --order` 判不過（`docs/13`「誰能關」）。`prefer_auto` 只是提示，關掉只印 note。
- **驗收**：優先寫可自動判定的 AUTO 條件；REVIEW／PO 只留給真的要人看的。

### 工單

- 一律落檔：`DIRECTOR/orders/WO-<編號>-<短名>.md`，格式見 `templates/WORK_ORDER.md`。`send_message` 只附路徑、一句摘要和必要的決定。
- 必填：`PRIMARY_WORKER / MODEL / EFFORT / FALLBACK / GOVERNANCE / BASE_REF / SCOPE / FORBIDDEN / ACCEPTANCE / DELIVERABLES / STOP_RULES`。
- BASE_REF 寫 `origin/main @ <commit>`，派工前先 `git fetch`，填 fetch 後遠端分支的最新 commit（2.2.2-ds.3）。`gate_check.py --order --repo <專案>` 會自己 fetch 再比：commit 不存在或落後遠端時印 `~ WARN BASE_REF`，加 `--strict-base` 判不過；fetch 失敗會印「not compared with the remote」，不會當作通過。故意從舊版開工就在工單寫明理由。開關在 `director_work.json` 的 `"base_ref"`（`check`、`fetch`、`strict`，預設 true／true／false）。
- 模型與 effort：`MODEL` 一律 `deepseek-flash`；`EFFORT` 只能寫 `off / low / high / max`（`docs/05`）。effort 在總監用 `subagent` 開 worker 時指定，開完不能中途改；要換就開接班子代理，並在工單 H 節記錄。
- 內容分段：A 背景、B 目標（MUST / OPTIONAL / OUT OF SCOPE，加上 SCOPE / FORBIDDEN 路徑清單）、C 執行前檢查、D 實作要求、E 驗收條件、F 安全與版控、G 完成定義。
- 驗收條件每項有：ID、類型、要求、驗證方法、預期。結果（實際、證據、狀態）寫在 TASK REPORT 的 ACCEPTANCE 表，不寫回工單。Mock 和單元測試不能當成真實環境的驗收。
- 類型 `AUTO / REVIEW / PO`：
  - AUTO：有指令可以重跑，總監重跑後判定。核准的指令寫在工單的 `CHECKS:`（`templates/WORK_ORDER.md` E 節），派工雜湊一起鎖住。
  - REVIEW：要有人看成品，獨立審查後由總監判定。開工前寫明誰看、從哪個角度看、看多大範圍、看哪些常識閘門項目（`docs/07`）。reviewer 是總監用 `subagent` 開的子代理；DSH 子代理預設拿到完整工具集，不能只給讀取工具，限制靠指示＋總監事後核對（`docs/07`）。
  - PO：只有 PO 能判。
  - worker 能填的狀態以 `tools/vocabulary.json` 為準：REVIEW 最多填 `READY_FOR_REVIEW`，PO 只填 `PENDING_PO`。
- `TRACES_TO` 寫這張工單服務的需求或決定編號，沿用專案已有的編號；格式寫在 `director_work.json` 的 `trace_id_pattern`。
- 初衷卡改了以後（2.1，shadow：只加 `~` 提示，不改 exit code；舊工單照樣通過）：
  - 工單可以選填 `BRIEF_REVISION` 和 `BRIEF_FINGERPRINTS_V1`，值照抄 `gate_check.py --brief BRIEF.md` 印的兩行。每條 B 的指紋是 `brief-row-v1\n` 加上 [ID, 類別, 內容, 怎麼算做到] 精簡 JSON 的 sha256。
  - `--order / --match / --preflight` 加 `--brief BRIEF.md`：工單記的那條 B 被改掉，印 `~ BRIEF_STALE <WO> <B> <受影響的 AC>`（舊條件驗過，新條件待重驗）；被刪掉是「需求已取消，待調整範圍」。同一編號出現兩次、欄數不對，或工單沒記指紋，印 `~ BRIEF_UNCONFIRMED`（依據未確認）。
  - 初衷卡定版時跑 `gate_check.py --brief BRIEF.md --snapshot brief-history`：只收狀態 LOCKED、有版次的卡，原子寫入快照，印一行 `BRIEF_LOCKED rev=<n> sha=<雜湊> snapshot=<路徑>`，原樣寫進 `DIRECTOR_LOG`。之後加 `--dispatch-log` 時，以最新一行 BRIEF_LOCKED 為依據；定版後的草稿不算。
  - 派工時用 `--hash 工單 --snapshot order-history` 留下工單原檔。工單改版、用 `EVIDENCE_EQUIVALENT` 沿用舊證據時，`--match ... --order-history order-history` 拿舊工單記的指紋比對；條件變了就印 `BRIEF_STALE`，找不到舊工單就印 `BRIEF_UNCONFIRMED`。
- Worker 不改工單的驗收條件和規格。發現條件做不到、互相矛盾或有錯，回報 `BLOCKED` 並寫明原因，由總監裁決後改工單。
- 總監改工單時 `REVISION` 加 1，在 H 節記一列（誰改、原因、影響的 AC），**同一步同步 `BRIEF.md`、`WORK_DIR/tasks.md`、`WORK_DIR/RESUME_STATE.md`**（WO-DS-004：工單改到 rev2，tasks.md 還留著舊的期望值）；`gate_check.py --order` 對 REVISION ≥2 的工單提示要同步，WORK_DIR 裡比工單舊的 tasks.md／RESUME_STATE.md 印 `~ shadow: REVISION_SYNC`（2.2.3-ds.3，不影響結果）。派工時用 `gate_check.py --hash` 印出工單雜湊，把它印的 `DISPATCH <WO-ID> rev=<n> sha=<雜湊>` 那行原樣寫進 `DIRECTOR_LOG`（同一工單以最新一行為準）；worker 在報告填 `ORDER_SHA256`。審查時 `--match ... --dispatch-log DIRECTOR_LOG.md` 拿派工紀錄比對：工單被改過再重算雜湊也會被查出；DISPATCH 必須獨占一行，引用、縮排或圍欄裡的不算；沒有紀錄時各模式都失敗。這是事後查出，不是事前防止：誰都還是改得動工單。
- 發工單前想清楚需求、現有結構、相依、邊界條件、測試方法，一次給完整。
- 先用 DW 現有的工具（2.3.0）：要檢查、計數、比對、等待、整理狀態之前，先查 `tools/README.md` 有沒有現成的；有就用，沒有才自己寫，並在報告寫為什麼現有工具不夠。工單的 D 節列出這次要用的 DW 工具。
- 製作類工單的第一步固定是「既有資產盤點」：未合併的分支（`git log --all -- <路徑>`）、需求方提供過的檔案、舊報告。盤點結果寫進 gate 報告。
- 規格審查：Strict 和 Standard 工單派工前必做（ds.2 起 Standard 也要，開關 `safety.spec_review_for_standard`；在 DSH 上的做法見 `docs/11_dsh_operations.md`），Direct 不做。總監開一個短上下文的子代理（`subagent`，新 context；depth 1 可以），照 `templates/SPEC_REVIEW.md` 審工單；reviewer 只准讀，限制靠指示＋總監事後檢查（`docs/07`）。結果只給總監參考，不增加 PO 的工作。每次在 `DIRECTOR_LOG` 記下花費（用 `tools/dsh_usage.py` 看該子代理 session 的 token，分不出來或讀不到就記 UNKNOWN）、抓到的問題和審查子代理的 `session=`（2.2.5）；2.2.5 起 Standard 必做，不再依花費降回選用，要改由 PO 決定。

### Gate 與回報

- Worker 在 gate 完成、卡住、需要裁決、要偏離工單時回報（用 `send_message` 通知總監），一個 gate 只送**一則完整**的 TASK REPORT（`templates/TASK_REPORT.md`）。
- 暫存檔位置（2.2.3，L-053）：harness 給的 scratchpad 和系統暫存資料夾（`%TEMP%`、`/tmp`）算工作區外：不在工單範圍內，總監看不到也重跑不到，session 結束可能就沒了。自寫的腳本、暫存輸出一律放工單的 `WORK_DIR`，RAN 寫的也是 WORK_DIR 裡的路徑。2.2.4-ds.4：開工第一步就把 `TEMP`／`TMP`／`TMPDIR` 設成 `WORK_DIR/tmp`（`python -I -X utf8 <WS>/DIRECTOR/tools/dsh_session.py --temp-env <WORK_DIR>` 建好資料夾並印出 PowerShell 與 bash 的設定行），工具和測試自己開的暫存檔也就留在 WORK_DIR。2.2.5（上游 DW 2.2.5 B9）：Git Bash 自己匯出 TMPDIR（指向系統暫存資料夾），Python 的 tempfile 先讀 TMPDIR 才讀 TEMP，所以 bash 一定要連 TMPDIR 一起設，而且每次呼叫是新的 shell，要在同一個呼叫裡設；設了環境變數 `WORK_DIR` 時，`ran_line.py`、`evidence_record.py`、`release.py` 自己把暫存檔放到 `WORK_DIR/tmp`；`gate_check.py --report-skeleton` 對有 WORK_DIR 的工單也印同一行。
- 工單大小與測試檔（2.2.4-ds.4）：Standard／Strict 的上限寫在 director_work.json 頂層 `order_limits`（`max_files_per_order` 3、`max_lines_per_order` 200、`max_test_lines_per_order` 400）。測試檔（`test_*.py`、`*_test.py`、`tests/` 下）算檔數，行數另算，不吃掉 200 行。
- 受保護的測試（2.2.4-ds.4）：TESTS_LOCKED 的檔和 `protected_tests` 列的檔只准新增或在檔尾加測試，`scope_check.py` 對到改動原有內容就判 `PROTECTED`。報告的 `PROTECTED_CHANGED:` 逐檔列出改到的受保護檔，沒有寫 NONE；`gate_check.py --match --repo` 拿它對 diff，寫「無」卻有改就判不過（WO-DS-006：PO 報告寫「兩支原測試沒改一行」，實際有改）。
- effort 一致（2.2.4-ds.4）：工單 `MODEL / EFFORT` 寫的 effort 就是派工時 `subagent` 的 `reasoning_effort`。派工後跑 `dsh_usage.py --effort-check <工單> --project-dir <WS>`，把印出的 `EFFORT_ACTUAL <WO> agent=… effort=… order=…` 行原樣寫進 DIRECTOR_LOG；不一致印 shadow WARN，`gate_check.py --match --dispatch-log` 也會提示（WO-DS-006：工單寫 high，session 全是 max）。
- 交件前 worker 跑三支工具，把結論行貼進 TASK REPORT：`tools/scope_check.py`（改動有沒有超出工單）、`tools/gate_check.py`（欄位和用詞）、`tools/evidence_record.py`（驗收指令留下重跑指令和產物雜湊）。AUTO 條件在最後一次 commit 之後記錄，ACCEPTANCE 表的證據欄寫紀錄的 `.json` 檔名；總監用 `gate_check.py --match 報告 工單 --evidence-dir 證據資料夾` 核對紀錄真的 exit 0、HEAD 相同。2.2.2-ds.3 起 worker 開工先跑 `gate_check.py --report-skeleton 工單 --repo <專案> --out <報告路徑>`：報告骨架照工單先填好，並印出這三支工具的完整指令，不用讀工具原始碼或 `--help`（省 token 的其他規則見 docs/13「省 token」）。
- 總監審查時自己重跑 `scope_check.py`、`evidence_record.py verify 紀錄 --rerun --order 工單 --dispatch-log DIRECTOR_LOG.md --repo <有候選 commit 的 repo 路徑> --candidate <40 位>` 和 `gate_check.py --match 報告 工單 --dispatch-log DIRECTOR_LOG.md`，不只看報告怎麼寫。`--rerun` 跑的是工單 `CHECKS:` 裡核准的指令，不是 worker 寫在紀錄裡的；紀錄的指令不同或不是在候選 commit 記的，都算不符。它在候選 commit 的 tree 複製出來的暫存資料夾裡跑，仍會執行候選 commit 的測試碼，不是沙箱（DSH 的檔案沙箱只管檔案效果，danger-full-access 等於不擋；這段隔離是 `evidence_record.py` 自己複製資料夾做的）；`--repo` 給任一有候選 commit 的 repo 就好（工具用 commit 的 tree 複製出乾淨資料夾來跑，不是用工作樹現況）。worker 記證據時加 `--order 工單`，紀錄就綁住工單版次；工單改版後要沿用舊證據，總監在 DIRECTOR_LOG 寫整行 `EVIDENCE_EQUIVALENT <WO-ID> rev=<舊> sha=<舊雜湊> to rev=<新>`，否則 Strict 失敗。Strict 工單再加 `--evidence-dir 證據資料夾 --candidate <git rev-parse worker 分支>`，少一個就失敗：報告、證據紀錄和裁決的 `CANDIDATE_HEAD` 都要指向同一個 commit。只有 `verify --rerun` 才算重跑驗證；`--match --evidence-dir` 和不加 `--rerun` 的 `verify` 只是讀 worker 自己寫的紀錄，`--rerun-recorded` 跑的也是紀錄裡寫的指令。`--match` 檢查每條驗收條件都有結果、狀態符合類型、PASS 附證據、工單雜湊和派工紀錄相符；不給 `--dispatch-log` 就只能和工單現在的樣子比。工具通過只代表格式、範圍和檔案對得上，不代表做對了；下面四階段照做。
- AC 用 git（2.2.3，L-055）：`CHECKS:` 的程式寫裸名稱會被 `--rerun` 擋下（PATH 會選到哪支程式說不準），git 是例外，只限唯讀子指令 `diff`、`show`、`log`、`status`、`rev-parse`、`ls-files`、`cat-file`，例如 `["git", "diff", "--exit-code", "<BASE_REF commit>", "--", "tests/"]`。子指令前不能有選項（`-c`、`-C`），其他子指令（push、commit、reset、checkout…）和會寫檔或執行程式的選項（`--output`、`--ext-diff`、`--textconv`、`--filters`、`--no-index`）都擋。git 檢查要用歷史，所以在 `--repo` 裡跑（不是複製出來的資料夾），跑完照樣重讀 repo，有變就不符。只要確認鎖定的測試檔沒被改，也可以不用 git：工單寫 `TESTS_LOCKED: <路徑> sha256=<64 位>`，CHECKS 用 python 算雜湊比對，不需要歷史。
- 總監審查四階段：
  1. 對照原始需求逐項核對，不接受 worker 自行縮減的驗收條件。REVIEW 條件交給獨立審查（`docs/07`），PO 條件列進待決帳，用 `ask_user_question` 問。
  2. 審證據：修改範圍、意外修改、build、測試是否足夠、回歸、未驗證項。沒有親自取得的證據要寫「依 worker 報告」。
  3. 判定：`PASS / PASS_WITH_WARNINGS / CONDITIONAL_PASS / PARTIAL / HOLD / BLOCKED / FAIL / NOT_RUN`。
  4. 下一步只選一個：`ACCEPT_AND_CLOSE / CONTINUE_SAME_WORKER / SWITCH_TO_OTHER_WORKER / REQUEST_INDEPENDENT_REVIEW / REQUEST_OWNER_AUTHORIZATION / STOP_AND_REPORT_BLOCKER`。
- 裁決格式（`templates/GATE_VERDICT.md`）：A 判定 → B 已證實成果 → C 問題 P0/P1/P2 → D 取捨 → E 下一張工單（落檔）→ F 停止狀態（預設 NO MERGE / NO PUSH / NO FINAL ACCEPTANCE）。
- 證據等級：`VERIFIED_LOCAL / VERIFIED_REMOTE / REPORTED / SUPPORTED / ESTIMATED / ASSUMPTION / UNKNOWN / NOT_TESTED / INVALID`。
- 狀態分開寫：工程、功能、成品、效能、穩定性、整合、PO 驗收，不用一個 PASS 蓋過其他。
- 跳過的測試不算 PASS；既有失敗維持原樣寫 `NO_NEW_REGRESSION`，不是 ALL PASS。
- 裁決的「自己查證的證據」（2.3.0）：A 節至少一行裁決者自己跑的 `- `<指令>` exit=<n> at=<HH:MM>`（`ran_line.py` 印），沒有就不能判 PASS 類；`gate_check.py --verdict` 檢查，嚴重度看 `director_work.json` 的 `verdict_self_check`（`warn` 預設 / `fail`；`docs/07` 第 6 節）。
- 交接時用 `RESUME_STATE.md`（`docs/06`）；原 worker 先停在安全狀態，接手者先核對 repo 和交接資料一致，不重做已通過的工作。
- 時間不得手填（2.2.5-ds.5）：報告、裁決、`DIRECTOR_LOG` 的時間一律由工具產生（`tools/ran_line.py`：`--stamp` 印時間，`--to 報告 -- 指令` 代跑並寫 RAN 行，`--exit N --cmd "指令"` 剛跑完補記；上游 DW 2.2.5 B1）。WO-DS-008 r2：8 份驗收報告寫 01:32，實際是 01:17。報告的 `WORKTREE:` 行也由工具產生（`gate_check.py --report-skeleton` 、`scope_check.py` 或 `dsh_session.py --worktree-status`，同一個函式）。共用 checkout 裡用 `scope_check.py --shared` 只算這張工單自己的 commit。
- TASK REPORT 可以加 `AGENT_NAME:` 和 `RAN:`（一行一個實際跑過的指令，寫 exit 和時間）。總監用 `tools/report_vs_audit.py --report 報告 --log <動作紀錄>` 核對：報告說跑過的 selftest、Unity、Blender、雜湊檢查，動作紀錄裡有沒有、結果和時間對不對得上。動作紀錄由 `python -I -X utf8 <WS>/DIRECTOR/tools/dsh_audit.py build --session <agent> --out <WS>/DIRECTOR/research/audit-<日期>.jsonl` 從 session 紀錄事後重建，不是 hook 即時寫的（`--session` 換 `--project-dir <WS>` 可抓整個工作區；<WS>＝工作區根＝總監 session 啟動資料夾，子代理 session 記在這裡，不在 worker 的 repo）。沒有紀錄時記 UNKNOWN，不當成通過或失敗。它只核對有沒有跑，不代表跑的內容對。`RAN` 要能和動作紀錄對上：2.2.5-ds.5 起 dsh_audit 整條指令都記（經 secret_mask，不再截 500 字，同上游 transcript_audit 2.2.5）；`--input-limit N` 截過的行標 `input_cut`，report_vs_audit 只比前段。
- 閘門順序（2.2.5，Standard / Strict）：先 DISPATCH、SPEC_REVIEW，再 PLAN_APPROVED，然後 worker 才開工（格式見 `templates/DIRECTOR_FILES.md` 的 DIRECTOR_LOG；計畫閘門的 `PLAN_APPROVED` 見 `docs/13`）。`gate_check.py --sequence 工單 --dispatch-log DIRECTOR_LOG.md --repo <repo>`：核准晚於 worker 的第一個 commit、沒有核准、沒有規格審查、審查和作者同一個 session，都 FAIL；缺 session id 是 WARN。
  - `--match` 的規格審查只查「有沒有」：`SPEC_REVIEW <WO>` 整行或 `reviews/` 的審查檔；沒給 `--dispatch-log` 也會找工單所在 DIRECTOR 的 DIRECTOR_LOG.md；交件時跑，受安全開關 `spec_review_for_standard` 管（docs/13）。
  - `--sequence` 的規格審查一定要給 `--dispatch-log`，除了有沒有，還查時間先後（核准早於 worker 第一個 commit）和 session（審查不是作者的 session）；不看安全開關。兩者用同一個函式（`safety_gate.review_fields_lacking`）查 tokens／issues／adopted 三欄。
- 裁決之後鎖程式碼（2.2.5）：`gate_check.py --after-verdict` 預設 FAIL。裁決之後的 commit 只改文件（`DIRECTOR/`、`docs/`、`.md` / `.rst` / `.txt`）照樣放行；改到程式碼（SCOPE 內也算）要再審、寫指向新 commit 的裁決；裁決的 commit 已不在分支上（歷史被改寫）也 FAIL。導入舊專案時加 `--warn`。
- 最終驗收（2.2.5）：最終裁決前，lead 照規格的情境，從交付物唯一的公開入口（CLI 或可呼叫的函式）實際跑一次，證據放 `evidence/E2E/`，每份紀錄寫 `ENTRY_POINT:`。`gate_check.py --final <DIRECTOR 資料夾>` 找不到證據就 FAIL；DECISION_REGISTER 的 DD 沒有「驗收案例」印 WARN。清單在 `templates/GATE_VERDICT.md` G 節。
- worker 輪數上限與交接（2.2.5）：worker 預設到 80 輪或 context 60% 就停（工單 `WORKER_LIMIT` 可改），寫 `HANDOFF.md`（`templates/HANDOFF.md`）用 `send_message` 回報 lead；lead 開新的子代理接續，不讓原 worker 繼續長下去。lead 只讀 TASK REPORT 的摘要段（首行到 RESULT）和 HANDOFF.md，不讀 worker 的完整過程。
- 要看「哪個需求做到哪裡」時，用 `tools/trace_report.py` 從工單、報告和裁決產生追溯表（需求 → 工單 → AC → 證據 → 裁決），不另外人工維護。
  - 加 `--brief BRIEF.md` 時，每條 B 多一列三欄：有人負責／這版有驗證紀錄／你看過這個成品嗎。
  - `--director-log` 讀 PO 看過哪個成品，`--acceptance PO_ACCEPTANCE.json` 讀 PO 的驗收紀錄。
  - 2.2 起「這版有驗證紀錄」拆成四欄：worker 自述、證據有效、綁鎖定依據、總監重跑。四欄都齊才寫「有」；只有 worker 自述的寫「部分」，不會再顯示成已驗證。總監重跑過 `evidence_record.py verify --rerun` 後，把它印的 `LOG_LINE: EVIDENCE_RERUN …` 整行貼進 DIRECTOR_LOG。
  - 只給 `--decisions BRIEF.md` 時，初衷卡裡用清單列出的 DD 編號也算找得到；PO 編號再加 `--decisions DECISION_REGISTER.md`。
- PO 看過成品要留下看的是哪一版（2.1，shadow）：
  - 總監在 `DIRECTOR_LOG` 寫整行 `PO_PRODUCT_REVIEW <WO-ID> candidate=<commit> outcome=seen|changes|accepted ref=<訊息> [manifest=<64 位>] [brief=B-2:<指紋>]`。
  - 要正式綁定時，寫 `PO_ACCEPTANCE.json`（schema `po-acceptance-v1`：candidate_id、commit、entry、manifest_sha256、offered_message_ref；有回覆時再加 reply_ref 和 outcome）。用 `gate_check.py --po-acceptance 檔 [--candidate <40 位>]` 檢查，少綁一項就印 `~ UNBOUND_PO_REPLY`。
  - 2.2 起還要能核對成品本身：再寫 `entry_sha256` 和 `manifest`（manifest 檔的路徑），檔案放在驗收紀錄檔旁邊（或用 `--artifact-root` 指定）。檔不見、內容變了、一則回覆用在兩份成品，都算綁不到；沒寫這兩欄的舊紀錄顯示「成品待核對」。同一 commit 有多份成品時，報告寫 `CANDIDATE_ID:` 指定是哪一份。
  - 裁決可以選填 `ORDER_SHA256:` 和 `REPORT_SHA256:`。之後檔案被改，`--match` 會印 `~ VERDICT_RECORD`。

### 發版（2.2.2-ds.3，同上游 2.2.2）

- 用 `python -I -X utf8 tools/release.py`：先 dry run，乾淨再加 `--execute`。它從 HEAD 讀 VERSION 和 CHANGELOG，工作樹有沒 commit 的改動就停並印下一步；遠端主線比本機新就停（落後），分岔要 `--merge` 另開 `release/<版本>`；「(上游版本, ds 序號)」整組要比遠端所有 tag 新、tag 還不存在（2.2.3-ds.3 起；`DEEPSEEK-PORT.md` 第 10 節）；selftest 和公開掃描（金鑰、私人 email、使用者路徑、DIRECTOR/、_work/、session 檔）過了才 push、打 annotated tag、建 GitHub Release（Latest），每步用 ls-remote／`gh release view` 驗。細節見 `tools/README.md`。
- 有 PR 和 CI 時照順序：PR → CI 全綠 → merge → 在 merge 後的主線 commit 跑 `release.py`，這時 push 是 SKIP，只打 tag 和建 Release。CI 沒全綠不發版。
- push、tag、Release 都要 PO 核准（`docs/08`）；release.py 不代替核准。

### 重資源排程（有總管時）

- 用到共用重資源的工作，先送 `TEST REQUEST`（`templates/TEST_REQUEST.md`），等 `GO`，結束送 `DONE <內容> <實際分鐘>`；超時 10 分鐘以上要說明原因和新 ETA。
- **GO 寫在排程看板檔，不用訊息發。** 看板只有總管能寫，一行一筆：`GO <完整名稱> <內容> <開始> <上限分鐘>`、`QUIET <時段> <原因>`、`HOLD <名稱> <原因>`。
- Worker 送出申請的**同一輪**，就自己等看板（不花 token）：讀看板檔，或開一個背景 job 等 GO 出現（job 結束會有通知），或結束回合讓總監在 GO 後用 `send_message` 叫醒。看到自己的 GO 才開始，並寫一行 ACK。DSH 沒有 Monitor、沒有 `notify_when_idle`，也不要反覆叫醒自己輪詢。收尾框不能取代等 GO（L-029）。看板讀寫用固定的小工具，名稱一律寫完整名稱，短名稱由工具換成全名。
- GO 後 N 分鐘內沒有 ACK，總管回報總監，由總監用 `send_message` 找 worker 並告警；派工工具成功不等於對方確認。N 建議 3–5 分鐘；不准空等整段獨佔時段。
- 文件、git、打包、輕量 CPU 工作不用申請。
- 和某個狀態有關的限制，寫成事件條件（「QUIET-END 後」），不寫固定時間。宣告 QUIET-END 的人，同時掃過所有寫成時間的限制，通知受影響的工作線（L-024）。
- 會用到 GPU 或引擎的執行腳本不能有預設設定檔，沒給參數就拒跑；清 HOLD 的指令裡不放任何執行腳本（L-025）。
- 停機（QUIET、叫停）的對象是整條程序樹：由上往下，先停批次腳本（父 shell），再停子程序。DSH 的 job 用 `job_kill` 停（只停自己的 job），其他程序照 PID 停。停完依 CPU 用量列出所有程序，量一段時間內的 CPU 增量，確認沒有殘留，並回報已停的 PID；不能只比對程序名。下令的一方也獨立確認一次。
- 長批次腳本每一步開跑前檢查暫停旗標（看板的 QUIET）；有暫停就自己停下。
- 收尾範本（2.3.0）：`templates/run_closing.py`。`run` 模式第一行就寫 ACK，跑完不論成敗在 `finally` 自己寫 DONE（含 exit code），不靠人記得；`go` 模式寫 GO 後等 5 分鐘，沒 ACK 先看有沒有 DONE / RESULT 檔（已經跑完就不吵），沒有才補通知一次，再沒有就印 `NO_ACK`。接到專案只改 `signal()` 和 `seen()` 兩個函式（寫看板、送訊息的方式）。
- 豁免要有期限和觸發條件（2.3.0）：`tools/waiver.py`。`add` 寫 `--until`（解除它的事件）和 `--watch`（那個事件會改到的檔，記內容雜湊），存在 WAIVERS.json，重開也讀得回來；檔案內容變了或 snooze 時間到才 `WAKE`，沒變就不吵醒人。沒寫 until 印 WARN。`block` 記錄卡在整合的分支，超過 N 小時（預設 8）印 `INTEGRATION_BLOCKED`，建議改成「在預設關閉的開關後面先合進去」，不要一直等。閒置監看每次跑 `waiver.py check --wake-only`。
- 工具：`tools/pause_ctl.py on|off|status` 管暫停旗標，`pause_ctl.py procs` 依 CPU 增量確認沒有殘留（見 `tools/README.md`）。DSH 沒有 hook 那種「工具呼叫前自動檢查旗標」的機制，旗標要由 worker 自己讀（工單寫明）＋總監在審查時核對。

### 測試預算

- 每個 TEST REQUEST 寫三件事：**目的**（回答哪個決定）、**最小範圍**（為什麼不能更小）、**上限分鐘**。缺一項退回。
- 磁碟和時長也要填（`templates/TEST_REQUEST.md`）：build 資料夾、擷取 `組數 × 每組張數 × 單張大小`、Library 和暫存的餘量，總寫入量要涵蓋這三項（L-030）；單位一律 GiB，以總管實測的餘量為準（L-031）；時長 = 組數 × 單組實測時間（含逾時），不用理想值（L-033）。總管用 `tools/gate_check.py --test-request 申請檔` 檢查，沒過就退件、不發 GO。
- 第 0 級的做法寫在 `templates/CPU_REPRO.md`（2.3.0）：明列要編譯的檔、印出實際跑的組件路徑和雜湊（`hash_check.py show`）、用內容雜湊判斷 build 新不新（`hash_check.py fresh`，不看檔案時間）、雜湊比對少一個案例就是 FAIL（`hash_check.py compare`）、開關在第一個 frame 印 `flag X read = 值`（`flag_check.py`，缺行就停、不判定）、模擬和 patch 讀同一個設定且重現上次實測（`sim_check.py`）。
- 送 TR 之前跑 `tools/pre_tr.py --config pre_tr.json --git-diff <base>`（2.3.0，範例 `templates/pre_tr.json`）：依改到的檔案判斷缺陷類別，每個類別的 CPU 檢查都要過；改到的類別沒有檢查也擋下。
- 預設上限：功能測試 30 分鐘、效能量測 20 分鐘；超過 60 分鐘要總監核准。超過上限 10 分鐘就先停下回報。
- 分級：
  - **第 0 級，每次修改後必做，不佔重資源**：離線編譯、CPU 上的單元測試、雜湊、數值檢查、量測腳本。能在這級發現的錯，不准拖到下一級。
  - **第 1 級，批次功能測試，預設**：同一 gate 裡互相獨立的修改累積起來一次驗。每項修改做成**開關**（命令列參數或設定值），同一個 build 跑出每一項的開 / 關對照。
  - **第 2 級，單項測試，例外，要寫理由**：P0 阻擋、PO 正在等、下一步依賴這個結果、修改互相耦合分不開、驗證單一根因假設。
- 不准的測試：程式沒變就重跑已通過的測試；為了「看起來完整」跑整個矩陣；gate 收尾以外的全量回歸；在成品 gate 之前跑效能量測。
- 統計型測試先算樣本數：失敗率約 10–20% 時，用 0/N 證明修好，N≈25–40 就夠（0.88^25 ≈ 5%），同時段跑對照組證明當時確實會重現。
- 一批之中某項失敗，其他項結果照記，不因一項失敗重跑全部。
- 輸出寫到 PO 指定的輸出位置，不寫進 repo；截圖預設 JPG，只有要做像素比對的近景才用 PNG。

## 為什麼

- 工單落檔，任何 session（總監或子代理）中斷後都能重讀；訊息在壓縮後可能消失，也會讓每個收件者多一次完整上下文的成本。
- 四階段審查擋住最常見的問題：worker 偷偷縮小驗收範圍、把「跑過」說成「通過」。驗收條件只有總監能改，worker 改了就等於自己批准自己的交件。
- v0.10 以前，工單的驗收表同時放結果欄：worker 要填結果就得改工單，規格有沒有被動也就查不出來。所以規格留在工單，結果放報告，再用 `--match` 逐條對照。
- 原專案一段展示影片的工程數字全部正確，角色卻朝反方向動作：審查只看了被問到的部位，看的角度也由作者自己挑。所以要用眼睛看的條件，開工前就寫明誰看、怎麼看，實作者不能自己判過。
- 規格審查會花用量，Claude 版只在 Strict 必做。dshdw 的 worker 判斷力較弱，派工前多看一眼比事後返工便宜，所以 ds.2 起 Standard 也做；照樣記下花費和抓到的問題，用數字決定要不要繼續做。
- 測試、計畫先寫死再實作（`docs/13`）：弱模型的錯會變成程式查得到的失敗，而不是「看起來做完了」。
- 狀態分開寫，是因為一個面向 PASS 常被拿來蓋過其他面向沒驗。
- 規則只寫在文件裡，靠模型自律就會漏；能在交件時用程式檢查的就用程式檢查（`scope_check.py`、`gate_check.py`、`dsh_audit.py`），DSH 沒有 hook 在動手前幫你擋。報告裡的「沒超出範圍」「測試通過」是自述，要能重跑、能對上動作紀錄才算證據。
- GO 用檔案發：DSH 樹內 `send_message` 沒有原專案那種「使用者兩次發言之間約 10 則就被暫停」的限制，但每則訊息都會叫醒對方一輪（成本），而且訊息在壓縮後可能消失；看板檔沒有這些問題，背景等待也不花 token。原專案曾因看板寫短名、監看等全名，獨佔時段空轉近半小時。
- 改一個測一個太慢；全部批次又分不出是哪一項造成的。開關讓一次 build 同時得到效率和可歸因的對照。
- 測試本身花時間、花資源、花 token。每個測試都要回答一個問題，否則不跑。

<!-- dshdw：依 DEEPSEEK-PORT.md 改寫 -->
