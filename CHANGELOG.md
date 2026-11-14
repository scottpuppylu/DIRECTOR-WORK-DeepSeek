# CHANGELOG — DeepSeek Harness 版

本 repo 是 [DIRECTOR-WORK](https://github.com/scottpuppylu/DIRECTOR-WORK) v2.2.2（Claude Code／Claude Desktop 版，MIT）的移植。
上游的完整變更歷史保留在 [`CHANGELOG-upstream.md`](CHANGELOG-upstream.md)；本檔只記 DeepSeek 版自己的變更。

## 2.2.4-ds.4（2026-11-14）

對應上游 2.2.4（DW commit 18d8ddb；5428682 之後另有 dad65a2 的 UNVERIFIED 和 18d8ddb 的 status 截寬與長路徑）。這一版處理 WO-DS-006 試驗（DSH 有／沒有 SDD 兩組，對照 Claude）比較表 §10 裡歸 DW-DS 的項目，並移植上游 2.2.4 的通用修正。ds 序號從 3 升到 4（總監待辦「ds 序號可以往下」）。

### 工單大小上限搬出 sdd（#8、S-P1）
- 上限不是 SDD 開關，SDD 關掉的專案也要用，所以搬到 `director_work.json` 頂層的 `order_limits`：`max_files_per_order` 3、`max_lines_per_order` 200、新的 `max_test_lines_per_order` 400。
- 測試檔（`test_*.py`、`*_test.py`、`tests/` 下）照算檔數，但行數另算，不吃掉 200 行（試驗：鎖定測試把 200 行吃掉，sdd 組只好把上限改成 600）。`scope_check.py` 的 `SIZE:` 行印 `files= lines= test_lines= limit=3/200/400`。
- 舊的 `sdd.max_files_per_order`／`sdd.max_lines_per_order` 照讀，`scope_check.py` 印 `NOTE: SHADOW WARN … 請搬到 order_limits`；兩邊都寫時以 `order_limits` 為準。`dsh_setup_check.py` 對舊位置印 shadow，並檢查 `order_limits` 的型別。`docs/13`、`sdd_gate.py` 說明、`director_work.example.json` 同步。

### 共用 checkout 的 scope_check（#2）
- DSH 的工人共用一個 checkout，舊版每張工單都把別人的檔算進來（試驗：`--match` 沒法自動過）。工單 `WORKTREE` 寫「共用」（或加 `--shared`）時，`scope_check.py` 只算 commit 訊息寫了本工單編號的 commit，加上 SCOPE 內還沒 commit 的檔；別人的檔印 `OTHER`，不算越界。本工單 commit 動到 SCOPE 外的檔照樣 `OUTSIDE`。`docs/11` 寫明 commit 訊息要帶工單編號。

### CHECKS 路徑（#3）
- `gate_check.py --order` 派工前就把反斜線路徑擋下，訊息指出第幾行、建議改正斜線。兩種都抓：`\w` 這種不合法的 JSON 跳脫，以及 `\t`、`\n` 這種會悄悄變成控制字元的。其他 CHECKS 錯誤也加上行號。`templates/WORK_ORDER.md` 寫明一律用正斜線。試驗的 WO-004 副本：`CHECKS line 97 (AC-5): backslash path … is not valid JSON; write the path with forward slashes`。

### 每張工單都要 SPEC_REVIEW（#4）
- 原本：只有給 `--dispatch-log` 才查 SPEC_REVIEW，沒給就完全不查，沒審過的工單照樣通過（試驗 WO-005／006）。現在：Standard／Strict 的 `--match` 一律查，沒給 log 就找工單所在 DIRECTOR 的 `DIRECTOR_LOG.md` 和 `reviews/` 下檔名有工單編號與 SPEC_REVIEW 的檔，找不到判不過。行裡缺 `tokens=`／`issues=`／`adopted=` 印 note。

### 受保護的測試只准新增（#7）
- TESTS_LOCKED 的檔和 `director_work.json` 頂層 `protected_tests` 列的檔，只能新增檔案或在檔尾加測試；改到原有內容或刪檔，`scope_check.py` 判 `PROTECTED` 越界（換行符號和檔尾空行不算改）。它也印 `PROTECTED_CHANGED:` 一行。
- `templates/TASK_REPORT.md` 加 `PROTECTED_CHANGED:`（逐檔列出改到的受保護檔，沒有寫 NONE）。`gate_check.py --match --repo` 拿它對 git：寫「無」卻有改、漏列、或改到原有內容都判不過（試驗：nosdd 的 PO 報告寫「兩支原測試沒改一行」，實際有改）。

### SDD 關閉時不提示 CLI（#9）
- `require_spec_for_strict` 和 `require_spec_for_standard` 都是 false 時，`sdd_gate.py --which` 只印一行「SDD 關閉，不檢查 CLI」，不找 CLI、不建議寫入 `openspec_bin`；`dsh_doctor.py` 印 OK 和同一句，`dsh_setup_check.py` 不再印寫入建議。找得到 CLI 時關掉 require_spec 仍要 PO 答覆。

### 範本建議（#10、#13）
- `templates/WORK_ORDER.md` 的邊界與壓力清單、`templates/SPEC_REVIEW.md` 第 7 項、`templates/openspec_config.yaml` 的 specs 規則各補兩行：巢狀深度含 JSON（不透出 RecursionError）；批次輸入有錯時預設輸出就列出是哪幾筆，問題物件用 dict 或中文名稱，不用 `XxxError` 類別名當使用者看到的字。原有清單文字和 DW 2.2.3 相同，只補這兩行。

### effort 一致（#14）
- `dsh_usage.py --effort-check <工單>`：找工單 PRIMARY_WORKER 的 session，印 `EFFORT_ACTUAL <WO> agent= effort= order=`，和工單 `MODEL / EFFORT` 不同印 shadow WARN（exit 0）。試驗資料實測：WO-004 的 w4 是 `effort=max order=high`。lead 把那行貼進 DIRECTOR_LOG；`gate_check.py --match --dispatch-log` 讀到不一致印 shadow WARN，沒有那行印 note。寫回 DIRECTOR_LOG 而不是工單，因為改工單會改掉派工雜湊。`docs/11`、`templates/WORK_ORDER.md` 寫明 `subagent` 的 `reasoning_effort` 一定要填工單的值。

### dsh_usage --out（#16）
- 原因：`--out` 只在有資料時才寫；篩選後沒有 session（`NO_DATA`）就在寫檔前 `return 2`，所以呼叫端看到 rc=2、沒有檔、也不知道為什麼。試驗的常見情況是 `--project-dir` 指到 repo 子資料夾（`…/ws/ledger`），但 session 記在啟動資料夾 `…/ws` 下。另一種 rc=2 是參數寫錯（`-o`、`--output`），那是 argparse 的用法錯誤。
- 修正：`NO_DATA` 時 `--out` 也寫 JSON（`status: NO_DATA`、`reason`、`hints`、`filters`），exit 仍是 2；`--project-dir` 在某個啟動資料夾底下時，印 `HINT` 指出該用的上層資料夾。

### DSH 啟動設 TEMP（對應上游 2.2.4 B3）
- `dsh_session.py` 多一個 CLI：`--temp-env <WORK_DIR>` 建 `WORK_DIR/tmp`，印出把 `TEMP`／`TMP`／`TMPDIR` 指過去的 PowerShell 與 bash 設定行。BOOTSTRAP 第 7 步、`docs/02`、`docs/11`、`templates/WORK_ORDER.md`、`templates/TASK_REPORT.md` 寫明開工先設；`gate_check.py --report-skeleton` 對有 WORK_DIR 的工單也印這一行。

### 上游 2.2.4 移植
- `report_vs_audit.py`（上游原樣搬，DS 只留自己的說明段和 rebuild 註記）：WO-DS-006 三組 20 份報告的誤判 FAIL 64 → 0、其中 18 條是 UNVERIFIED（claude 8 → 0／4、dsh-sdd 32 → 0／11、dsh-nosdd 24 → 0／3；64 條全是誤判，沒有真漏跑）。變數會展開（`$X`、`${X}`、`$env:X`、`%X%`、PowerShell `a + b`、here-string，同一 agent 前面設的延用到後面）；`git -C DIR x` 當 `cd DIR` 再 `git x`；字中 `...`／`…` 代表任意字；短 hex 對長 sha 開頭；主張的絕對路徑對紀錄的相對路徑；`at=HH:MM:SS` 和時間區間；`AC-1 .. AC-6`；選項換順序；全形 `；` 斷句；多段主張分在幾次呼叫跑也算；從 RAN: 外開的 ``` 在那裡結束（WO-01 的 ACCEPTANCE 表格不再當成指令）；主張可能在另一條主張對到的截斷呼叫被截掉的那段時，印新狀態 **UNVERIFIED**（in log cut part）：不算 OK、也不算 FAIL，最後一行另計 `unverified=n`（放在最後，原有欄位位置不變），exit code 不變，審查的人要自己看；在截斷呼叫留下來的那段就對得到的主張仍是 OK；PowerShell 這類從不回報 error 的工具 exit 對不上印 not checkable。沒人跑過的指令照樣 FAIL。
- `gate_check.py --after-verdict <裁決.md>... --repo <專案> [--orders <資料夾>] [--strict]`（shadow）：最後一份裁決的 `CANDIDATE_HEAD` 之後，改到該工單 SCOPE 外、又不是文件（`DIRECTOR/` 底下、`.md`／`.rst`／`.txt`）的 commit 印 `~ WARN LATE_COMMIT`，exit 不變；`--strict` 判 FAIL。候選解不出印 `NOT_CHECKED`。DS 的 `--strict` 原本只配 `--resume`，現在兩者都可以。
- `templates/WORK_ORDER.md` B 節：「不做（OUT OF SCOPE）」不可留空（沒有寫「無」）；新欄「可呼叫的入口」（交付物是函式庫或工具時寫一個測試可直接呼叫的公開函式）。`templates/SPEC_REVIEW.md` 第 12 項審這兩欄（上游是第 9 項，DS 編號不同）。
- `docs/05`「派工規劃」加三行：平行線切多大、能同時就同時派、派工前估時間。
- 暫存檔放 WORK_DIR/tmp：DS 在本版 B10 已做（`dsh_session.py --temp-env`、`docs/02`、BOOTSTRAP 第 7 步）；另照上游在 `docs/11` 開 worker 流程第 3 步的提示加一句。
- `status_gen.py`（上游 2.2.4，L-059，總監驗收時發現）：產生的 `status.py` 每行原本從行尾切到 `width`，TMP 一長，路徑後面的狀態字（OK、LOW、計數）就被切掉。現在一行超過 `width` 時頭尾都留，行內最長路徑（路徑太短就整行）的中段換成 `…`，寬度上限照舊。修前在 152 字的 TMP 下實測：DISK 行尾的 `OK`、LOG 行尾的 `ago)` 都被切掉；修後都留著。DS 原本的 selftest 抓不到（`status_gen_round_trip` 只看 STATUS 標頭），新增 `status_long_path_224`。
- selftest 長路徑（上游 2.2.4 同寫法）：`selftest_ds.py` 開頭給整個 process 設 `GIT_CONFIG_COUNT`／`GIT_CONFIG_KEY_n=core.longpaths`／`GIT_CONFIG_VALUE_n=true`（原本有就接在後面），它叫起來的工具裡的 git 也吃到；release、BASE_REF 測試建的 bare origin 另外在 repo 裡設 `core.longpaths`（本機 remote 那一側不繼承環境變數）。tools 不變。修前用 152 字的 TMP 跑 selftest_ds：49 項 FAIL 5（`release_state`、`release_execute`、`base_ref_fresh`、`release_scan` 的 git push「Filename too long」，`after_verdict_224` 的 commit 寫不進去），都不是 status 造成的。DS 沒有子模組測試，所以沒有上游 `test_submodule_ignore` 的 GIT_DIR SKIP；DS 的摘要行本來就分開算 `skip=n`，格式不變。

### 已知限制
- Windows 長路徑三點寫進 `tools/README.md`「已知限制」：git 超過 260 字要 `core.longpaths`；GIT_DIR 超過約 220 字 git 本身停止；本機 remote 那一側不繼承 `GIT_CONFIG_COUNT`。
- UNVERIFIED 的主張要人看：工具只能說「可能在截斷處」，不能判斷有沒有跑。

### 遷移
- 舊的 `director_work.json` 照樣能用：`sdd.max_files_per_order`／`sdd.max_lines_per_order` 照讀（印 shadow WARN，請搬到頂層 `order_limits`）。
- `report_vs_audit.py` 最後一行多了 `unverified=n`（放在最後，原有欄位位置不變），有程式讀這一行的照樣讀得到。
- 已經產生的 `status.py` 要用 `status_gen.py --force` 重新產生，才會換成頭尾都留的截寬。
- Standard／Strict 工單驗收時一定要有 SPEC_REVIEW 紀錄（DIRECTOR_LOG.md 或 `reviews/`），舊工單沒審過的會判不過。
- 舊工單沒有「不做」「可呼叫的入口」照樣通過 `gate_check`（由規格審查看）。

### 驗證
- `selftest_ds.py` 由 37 項增為 50 項，新增：`order_limits_224`、`scope_shared_224`、`protected_tests_224`、`spec_review_224`、`protected_report_224`、`sdd_which_off_224`、`checks_paths_224`、`dsh_usage_out_224`、`effort_check_224`、`temp_env_224`，以及上游 2.2.4 的 `report_vs_audit_224`（20 個比對案例、15 個 CLI 情境、26 個 mutation，含 UNVERIFIED 兩個情境與 4 個 mutation，案例表與上游逐字相同）、`after_verdict_224`（11 個 CLI 檢查、4 個階段、5 個 mutation）、`status_long_path_224`（150 字以上資料夾，2 個 mutation）。短 TMP 和剛好 140 字的長 TMP 各跑一次，都是 50/50、skip=0。`report_skeleton` 的 fixture 補一行 SPEC_REVIEW（B4 之後沒審過的 Standard 工單會被擋）。新增 `--only <名稱>` 方便單跑（摘要行標 ONLY，不會被當成全套）。
- 每輪必讀（docs/01、03、06、08）：10,964 → 10,964 bytes。

## 2.2.3-ds.3（2026-11-14）

對應上游 2.2.3（DW commit 4f6c9e6）。這一版要讓 OpenSpec 規格層下次一定會被用上，並帶入 WO-DS-004 試驗（DSH 和 Claude 同一需求各跑一次）學到的事。版本號是 PO 指定的：上游段從 2.2.2 升到 2.2.3，ds 序號維持 3；`release.py` 的版本規則因此改成比「(上游版本, ds 序號)」整組（總監裁定，見「工具修正」）。

### OpenSpec CLI 自動偵測（試驗：本機有 CLI，規格層卻被關掉）
- 試驗裡 req-only 專案的 `sdd.openspec_bin` 是 null，本機其實裝好了 openspec 1.16.0，DSH lead 以「無網路、不能裝」自己寫 DD 把 `require_spec_for_*` 關掉，規格層完全沒用上。
- `sdd_gate.py` 依序找 CLI：`OPENSPEC_BIN` → `sdd.openspec_bin`（`%VAR%`／`$VAR`／`~` 會展開）→ `%LOCALAPPDATA%/dw-ds-tools/openspec-*/node_modules/.bin/openspec.cmd`（多版取最新；非 Windows 是 `$XDG_DATA_HOME/dw-ds-tools/…/openspec`）→ PATH。`--which` 印用哪一個、第幾層、版本；設定是 null 時印建議寫入的值（`%LOCALAPPDATA%` 寫法，不寫死使用者路徑）。設了第 1、2 層卻指錯，會判不過，不會偷偷換成後面的層。`gate_check.py` 用同一個函式。
- **找得到 CLI 時，lead 不得關 `require_spec_*`**：`gate_check.py --order` 對 `require_spec_for_<治理>` 為 false 的工單判不過，除非 `PO_PENDING.md` 有寫 require_spec 的項目，而且 PO 已回答。找不到 CLI 時照舊放行（tests-first 保留），另印 note 要寫 PO_PENDING「安裝 openspec」。
- `dsh_setup_check.py` 報告 CLI 狀態（層級、版本）；設定是 null、找不到 CLI 又沒有安裝項目、或有 CLI 卻關了 require_spec 而 PO 沒答，各印一行 shadow（`--strict` 判不過）。`dsh_doctor.py` 多一項 `openspec`（`--config` 可給專案設定），必要工具清單加上 `sdd_gate.py`、`bootstrap_repo.py`。
- 新 `tools/bootstrap_repo.py`：BOOTSTRAP 10.5 的機械步驟。找到 CLI 就寫進 null 的 `sdd.openspec_bin`（只改那一個值）、專案沒有 `openspec/` 就跑 `openspec init --tools agents --language zh-TW --no-animation`、把 `.memsearch/` 加進 `.git/info/exclude`。做過的跳過，`--check` 只報告；找不到 CLI 就印 PO_PENDING「安裝 openspec」要寫什麼，不安裝任何東西。
- 文件：BOOTSTRAP 10.5 改成「先找本機已裝的」；`docs/13` 新增「誰能關」一節，程式會擋什麼的表格和「安裝」一節更新；`docs/02`、`docs/11`、`templates/WORK_ORDER.md`、`templates/DIRECTOR_FILES.md`、`director_work.example.json` 的說明同步；`templates/AGENTS_PROJECT_SECTION.md` 加「規格層」一行。
- 冒煙驗證（不是 DSH 試驗、不用額度）：全新的暫存專案、不設 `OPENSPEC_BIN`，照 BOOTSTRAP 跑 setup_check → bootstrap_repo（寫設定、init、exclude）→ 寫一個最小 change → `gate_check --order` 實際跑 `openspec validate --strict` 通過 → 拿掉 Scenario 後判不過 → 放回又通過，16 步全過。

### 試驗心得
- **邊界與壓力清單**（上游 2.2.3 L-048，文字照搬）：`templates/WORK_ORDER.md` E 節 8 行（深度、長度、重複符號、極大數字／溢位／除以零、非字串、Unicode／全形、錯誤訊息不漏原生或英文訊息；需求寫「不當掉」至少一條極端輸入的 AC），DS 多一行 OpenSpec 寫法：用得到的每一項在 `specs/` 寫成一個 `#### Scenario:`（WHEN 極端輸入，THEN 預期結果或錯誤訊息），需求寫「不當掉」至少一個 Scenario 用極端輸入。`templates/openspec_config.yaml` 的 specs 規則加同樣兩條（實測 openspec 1.16.0 `instructions specs` 會把它們交給 agent），`docs/13` 流程第 1 步同步。
- `templates/SPEC_REVIEW.md`：新第 7 項（上游第 7 項原文：清單沒涵蓋、需求寫「不當掉」卻沒有極端輸入的 AC 算 P1；DS 加一句 Scenario 也照算），原第 7～9 項改成第 8～10 項。第 11 項**逐一重算字面期望值**改成上游第 8 項的寫法：手算、不看被測程式，每個值一行「測試名｜期望值｜怎麼算的｜相符 / 不符 / 算不出」；DS 另外連 Scenario、AC 的寫死期望值一起算，「不符」是 P0（試驗：`2 + 3 * (4 - 1)` 被寫成 9，審查沒抓到）。總監第 2 步照上游第 3 步（L-049）：重算表寫進審查紀錄，有「不符」或「算不出」就不鎖。
- 工單改版同步：`gate_check.py --order` 對 REVISION ≥2 的工單提示同步 BRIEF.md、WORK_DIR/tasks.md、WORK_DIR/RESUME_STATE.md；WORK_DIR 裡比工單舊的那兩個檔印 `~ shadow: REVISION_SYNC`（不影響結果）。`docs/02`、`templates/WORK_ORDER.md` 同步（試驗：工單改到 rev2，tasks.md 還寫 9）。
- `.memsearch/`（DSH 的記憶索引）由 `bootstrap_repo.py` 自動排除（試驗裡 lead 要自己補 DD-11）。

### 上游 2.2.3 移植（L-052～L-055）
- `report_vs_audit.py` 照上游 2.2.3 三方合併（DS 只多保留 DSH 重建紀錄的說明和 note）：換行、`;`、`&&`、`||` 切段，多段主張對得到多行腳本；`RAN:` 下 ``` 包的一段算一個主張；`at=` 只取時間、全形備註不比；`AC-1/AC-2`、`AC-1/2`、`AC-1..AC-3` 每個編號各要一筆；省略的主張（`...`、`427fcef...`、「同上」）可跳過選項；被截的行 3 個詞對到行尾也算；顯示最接近 `at=` 的那筆；後面還跑了別段的印 `not checkable` 算 OK。兩種 shadow WARN（exit code 不變）：`RAN:` 一行沒有 `` `指令` ``；`SCOPE_CHECK: PASS` 但做事的 agent 最後一次 commit 之後沒再跑 `scope_check.py`。
  - 用 WO-DS-004 的封存輸入重跑（只讀，輸出在 WORK_DIR）：DSH 報告 FAIL 6 → PASS 11/11；Claude 報告 FAIL 2（剩下兩筆紀錄裡確實沒有），和 DW 2.2.3 的結果相同。
- `evidence_record.py` 和上游 2.2.3 逐位元相同：`verify --rerun` 的 CHECK 可以寫裸 `git`，只限唯讀子指令（diff、show、log、status、rev-parse、ls-files、cat-file）；子指令前的選項、其他子指令、會寫檔或執行程式的選項（縮寫也算）照樣 `NOT_RUN`、exit 2。在 `--repo` 頂層跑，關掉 replace 物件、fsmonitor、pager、optional locks、外部 diff、textconv，跑完照舊重讀 repo。
- `docs/02`：暫存檔放 WORK_DIR，不放 scratchpad 或系統暫存資料夾（L-053）；「AC 用 git」一段（唯讀 git，或改用 TESTS_LOCKED sha256）。`templates/TASK_REPORT.md` 的 RAN 段提醒一句。`tools/README.md`、`tools/DSH-TOOLS.md` 同步。
- 不搬：上游 `selftest.py` 的案例（DS 用自己的 `selftest_ds.py`，見「驗證」）。

### 工具修正
- `verify_dsh_run.py` D06：改看每個寫入動作的目標（cmdlet 路徑參數、重新導向、.NET File、node fs、rm／mv／cp，變數照腳本自己的字串展開），`tools.*(...)` 用括號配對剝除（跳過字串、樣板字串、regex、註解）；解不出目標時退回舊規則。ds.3 重跑原本誤判 FAIL，現在 34/34。
- `verify_dsh_run.py` D13：`is_write` 用同一個剝除（原本只「提到」檔名的 run_code 被算成改檔，返工 5 次 → 2 次、改工單 4 次 → 0 次）；步驟分界改成「第一個動作所在的那一輪」（`round_of`），第 8／9 步不再互相吃掉輪數。`calls_full.jsonl` 多存 `session`、`cwd`、`top`。
- 回歸測試：`tools/test_verify_dsh_run.py` 新增 8 項（D06 5、D13 3），共 33；fixture 是 ds.3 重跑的紀錄，放在 `tools/fixtures/`，使用者資料夾路徑換成 `%LOCALAPPDATA%`。
- `release.py` 版本規則（總監裁定 WO-DS-005 C）：「(上游版本, ds 序號)」整組要比遠端所有 tag 新、tag 還不存在；ds 序號不再單獨比。v2.2.2-ds.3 之後的 2.2.3-ds.3 可以，2.2.2-ds.2、2.2.2-ds.3 會停；沒有旗標可以跳過。`DEEPSEEK-PORT.md` 第 10 節、`docs/02`、`tools/README.md` 同步。

### token（只用 WO-DS-004 的現有紀錄，沒有新跑）
- DSH 一次 20.60M，lead 佔 14.39M（159 步，output 0.9%）。lead 的大項：自己的推理和呼叫重送 24.9%、系統提示 17.5%、規則包文件 10.9%、工具原始碼和 `--help` 8.5%、同一檔重讀 3.7%。
- 本版改了兩條規則：BOOTSTRAP 第 1 步「每支工具只讀一次，之後不重讀、不跑 `--help`，用法查 `tools/DSH-TOOLS.md`」（重讀加 `--help` 約 0.76M）；`docs/13`「省 token」第 8 條「讀過的檔不整份重讀」（其他檔重讀約 0.20M）。合計上限約 0.96M（lead 的 6.7%），要下次實機才知道實際省多少。
- 每輪必讀的 bytes：`docs/01`、`03`、`06`、`08` 合計 10,964，本版沒改（B3、B9 只改範本、`docs/02`、`docs/13`，寫工單、審規格、交件時才讀）；AGENTS 總監段落範本 2,360 → 2,601（＋241，「規格層」一行，估計約多 0.02%）。

### 下一版
- BOOTSTRAP 的讀檔清單分成「建置必讀」和「用到再讀」，或讓短上下文的子代理讀完回摘要：規則包文件佔 lead 的 10.9%，但會改變 lead 的讀法，要實機驗證不漏規則才改。
- 改檔用 `edit` 只送改的段落、不整份重寫：lead 自己的推理和呼叫重送佔 24.9%，其中有整份工單、初衷卡的內容，還沒量過。

### 驗證
- `selftest_ds.py` 30 → 37 項（新增 `sdd_cli_lookup`、`sdd_cli_setup`、`sdd_spec_off_gate`、`revision_sync`、`bootstrap_repo`；上游 2.2.3 移植的 `matching_223`（15 個比對案例、14 次 CLI 執行、16 個 mutation 都被抓到，案例取自上游 selftest）和 `evidence_git_223`（8 個允許、10 個拒跑、git_argv 的旗標、4 個 mutation）；`setup_shadow`、`report_skeleton`、`release_state` 更新），設與不設 `OPENSPEC_BIN` 各跑一次都全過；不設時 `sdd_real_openspec` 從第 3 層找到真的 CLI。
- `verify_dsh_run.py` 對 ds.3 重跑 34/34；`test_verify_dsh_run.py` 33/33。

## 2.2.2-ds.3（2026-11-14）

ds.3 對應上游 2.2.2，是工具版：發版一次到位、派工前確認 BASE_REF 是最新的、DSH 試跑驗證器通用化、根據 WO-101 實機紀錄的量測減少 DSH 的 token 用量，並移植上游 2.2.2 的 RESUME_STATE 大小檢查和原文搬移工具。工單格式沒有變；新的檢查預設只提示，不會讓舊工單判不過。

### 上游 2.2.2 移植：RESUME_STATE 大小（shadow）與 resume_archive.py
- 問題：RESUME_STATE 每次續接都整份讀進 context，DSH 每一步又重送整段對話；表頭 `Before:` 鏈越接越長。上游實測一份 115,026 bytes（約 57,513 token），最長一行 32,699 bytes。
- `memory_size_check.py --kind resume`：一次量多份（`--file` 多次、`--glob`、`--workstreams <ACTIVE_WORKSTREAMS.md>`），每檔一行（bytes、~token、最長行、可搬 bytes），最後一行 `SIZE: PASS|OVER|MISSING`；上限 20480 bytes、單行 4096（`director_work.json` 的 `resume.max_bytes`、`resume.max_line_bytes`）。只讀。單檔舊用法輸出不變，預設仍找最近的 `AGENTS.md`。
- `gate_check.py --resume`：超過時印 `~ shadow: RESUME_SIZE ...`，exit code 不變；`--strict` 才判不過；`--config` 讀上限。
- `dsh_setup_check.py`：RESUME_STATE 加大小檢查（shadow）；`director_work.json` 多查 `resume`、`base_ref`、`release` 區塊的型別；`sdd`／`resume`／`base_ref`／`release` 不再被誤報成「keys no tool reads」。
- 新 `tools/resume_archive.py`（上游原樣）：「壓縮」只代表原文搬到同資料夾 `RESUME_HISTORY_<YYYYMMDD>.md`，原處留索引（日期、歷史檔、sha256）。近期只看筆數（`resume.keep_recent`，預設 10），沒有 keep_days；四行表頭仍四行，`Before:` 鏈保留現況和最新 10 筆、只搬更舊的尾段；現況、保護標題（`resume.protect_headings`）、沒有完整日期的段落都不動；順序或筆數看不清就不搬並印 shadow。預設 dry-run；`--execute` 先寫 `.bak`，搬完驗 (a) 歷史檔逐字含搬走的內容 (b) 留下的部分 sha256 不變 (c) 放回去等於原檔，任一項不過就還原並 exit 1。
- `gate_check --order` 的 `base_ref` 讀法換成上游版：開關不是 true／false 會印 note 並用預設（以前靜默照用，字串 `"false"` 會被當成真）；設定檔先找工單資料夾再找上一層；BASE_REF 沒寫 commit 時不再印 note（和上游一樣，舊工單輸出不變）。
- `release.py` 從上游 2.2.2 帶回：`main(argv)`、公開掃描多擋 `CLAUDE.local.md`／`.claude/settings.local.json`／Claude session 紀錄。兩邊的工作樹與版本規則本來就一致。
- 文件：`docs/06` 的 gate_check 那一行加大小一句；細節在 `docs/06b`「RESUME_STATE 瘦身」和巡查第 4 步；`docs/02` 加「發版」一節；`templates/RESUME_STATE.md` 註明上限；`CHANGELOG-upstream.md` 附上游 2.2.2 段。逐檔差異和理由見 `DEEPSEEK-PORT.md` 第 12 節。
- 只由各工作線自己跑 resume_archive（總監巡查時用 memory_size_check 量），不是每輪步驟。

### 工具
- 新增 `tools/release.py`：發版一次跑完（fetch → 和遠端分支比落後／分岔 → VERSION＝CHANGELOG 最上面一段、版本比遠端所有 tag 新 → selftest → 公開掃描 → push → `ls-remote` 確認 → annotated tag → push tag → `ls-remote` 確認 → `gh release create --latest --verify-tag` → `gh release view`）。
  - 預設只演練；加 `--execute` 才動遠端。
  - `--merge`：分岔時開 `release/<版本>` 做 `merge --no-ff`，有衝突就停並列出檔案；演練時用 `git merge-tree` 先預測衝突。
  - 公開掃描範圍：金鑰與 token 格式（沿用 `secret_mask.py`）、`key = value` 形式的密碼、noreply 和 `*.invalid` 以外的 email、使用者資料夾路徑、`DIRECTOR/`、`_work/`、`AGENTS.local.md`、DSH session 檔、commit 訊息與作者 email。找到時不印出密碼本身；有 gitleaks 時一併跑。
  - 中途停掉後重跑，已完成的步驟會跳過。
  - VERSION 和 CHANGELOG 從 HEAD 讀（`git show HEAD:…`）；任何 tracked 檔有沒 commit 的改動就停（演練也一樣），避免 tag 名稱和 tag 裡的 VERSION 對不上（總監演練時抓到；DW 的 release.py 同樣修法）。
  - 版本檢查：整個版本號要比遠端所有 tag 新，而且 `-ds.N` 要比遠端所有 `-ds.*` tag 的 N 大（流水號不因上游換版本歸 1；規則寫在 `DEEPSEEK-PORT.md` 第 10 節）。
  - 選型：release-please 和 semantic-release 都要 CI 和 conventional commits，semver 也排不出 `2.2.1-ds.N`，所以不用；`gh release create` 已有 `--verify-tag`、`--notes-file`、`--latest`，直接用。
- `gate_check.py --order` 檢查 BASE_REF 是否最新：先自己 `git fetch`，再把 BASE_REF 的 commit 和遠端分支比。
  - 不存在或落後：印 `~ WARN BASE_REF`。
  - fetch 失敗或沒有遠端：明說「沒和遠端比」，不會靜默通過。
  - `--strict-base`：上面三種都改成判不過。
  - 開關在 `director_work.json` 的 `"base_ref"`。
- `gate_check.py --report-skeleton 工單 [--repo] [--evidence-dir] [--out]`：照工單產生 TASK REPORT 骨架，並印出錄證據（照 CHECKS）、scope_check、`--match` 的完整指令。
  - 已先填好：TASK_ID、worker、模型、BASE、ORDER、ORDER_SHA256，以及每條 AC 一列（附該類型可填的狀態）。
  - 骨架沒填完，`--report` 會判有 placeholder。
- 新增 `tools/verify_dsh_run.py`：DSH 試跑驗證器，由 ds.2 的 WO-101 `verify_run.py` 通用化。
  - R01–R21 看 repo，D01–D14 看 DSH session 紀錄。
  - 工單專屬的檔名、代理名、隱藏 oracle 寫在設定檔（`templates/VERIFY_DSH_RUN.json`）；CLI 參數優先於設定檔。
  - 用 WO-101 重跑：34/34 PASS，37 列結果和 ds.2 那次相同。
  - 修正兩個從 ds.2 帶來的錯：
    - 輪數表（D13）的「8 驗收」原本抓到規格審查期間的 `scope_check.py --help`；
    - 「9 裁決」「10 總結」原本永遠找不到。
- 新增 `tools/test_verify_dsh_run.py`（25 個單元測試：原本的 11 個 D08 案例，加設定、合成試跑和 D13 輪數表的步驟標記）。

### 省 token（先量測再改）
- 量測對象：WO-101 實機紀錄，共 829 萬 token、102 步。
  - 每步重送的固定部分約 46K token，佔 57%；所以步數是最大的成本。
  - worker 約 8 步在讀檢查器原始碼學報告格式；lead 約 13 步在試 provider、讀 `--help` 和解析程式。
- `docs/13` 新增「省 token（ds.3）」：7 條規則和一張指令表。
- 預估同一任務總 token 降 58%～60%（S 取 42K～49K、推理內容算或不算重送，都在這個範圍）。這是推算，還沒有 DSH 實機重跑；重跑列為 PO 選做步驟。
- `templates/TASK_REPORT.md`、`docs/02`：開工先跑 `--report-skeleton`。

### 文件
- `docs/02`：BASE_REF 新鮮度、`--report-skeleton`。
- `templates/WORK_ORDER.md`：BASE_REF 註明先 `git fetch`，格式 `<remote/branch @ commit>`。
- `docs/13`：省 token 一節、已知限制改指 `verify_dsh_run.py`。
- `BOOTSTRAP.md`：開線那一輪的 BASE_REF 提示，10.5 第 6 點（省 token、試跑驗證）。
- `DEEPSEEK-PORT.md` 第 10 節：發版用 `release.py`；版本號規則 `<上游版本>-ds.<N>`，N 一直往上加。
- `README.md`、`tools/README.md`、`tools/DSH-TOOLS.md`、`director_work.example.json`（`"release"`、`"base_ref"`、`"resume"` 三段）。
- `DEEPSEEK-PORT.md` 第 12 節：上游 2.2.2 逐檔比較與每個差異的理由。

### 驗證
- `selftest_ds.py` 30/30 PASS（OpenSpec 1.16.0 實機），新增 8 項：`release_state`、`release_execute`、`release_scan`、`base_ref_fresh`、`report_skeleton`、`verify_dsh_run_unit`、`resume_size`、`resume_archive`（後兩項是上游 2.2.2 的測試案例改寫，含 11 個突變都被抓到）。2.2.1-ds.2 是 22/22。
- `verify_dsh_run.py` 用 WO-101 設定：`VERIFY_DSH_RUN: PASS pass=34 fail=0 skip=0`。
- 上游 A5 的 115,026 bytes RESUME_STATE 複本：`gate_check --resume` 多一行 `~ shadow: RESUME_SIZE 115026 bytes ... ~57513 tokens, longest line 1: 32699 bytes`，exit code 和 2.2.1-ds.2 相同（都是 1，原因是檔裡原有的 placeholder，不是大小），`--strict` 時大小變成問題；`resume_archive --execute` 115,026 → 57,472 bytes（少 57,554 bytes，約 28,777 token），19 段 60,162 bytes 原文搬到歷史檔，(a)(b)(c) 都過，搬後的檔和上游 A5 結果逐 byte 相同（sha256 68efb13b…）。
- 每輪必讀：10,947 → 10,964 bytes（上限 11,000）。本版沒有新增每輪必讀的檔案或步驟：release.py 只在發版時跑，BASE_REF 只在派工時跑，resume_archive 只由各工作線自己跑。

對齊初衷：
1. 幫到誰：每次續接都整份讀 RESUME_STATE 的工作線（實測少讀一半）、派工的總監（從舊 commit 開工會先看到 WARN）、發版的人（從 HEAD 發、每步驗證）、DSH 的 worker（少讀原始碼、少走步）。依據：PO 2026-11-14 指示、WO-DS-003 REVISION 5、上游 WO-DW-222。
2. 平台：全是本機命令列工具，只用標準庫；release.py 需要 git 和 gh。
3. 服務：初衷 4（中斷不丟進度）：搬移是原文、可逐 byte 還原；初衷 5（成品要真的對）：發版從 HEAD；初衷 7（零成本）：額外花的少於省下的。
4. 核心：每輪必讀 10,964 bytes，仍在 11,000 以內；新檢查先 shadow／WARN。
5. 舊檔案和舊指令照樣能用；`memory_size_check` 單檔用法輸出不變。

## 2.2.1-ds.2（2026-11-14）

ds.2 SDD 建在 2.2.1-ds.1 之上：本版把 ds.2 分支（原本從 2.2.0-ds.1 開出，沒有單獨發佈）merge 進 2.2.1-ds.1。2.2.1-ds.1 從上游移植的工具改動全部保留，再加上 ds.2 的 SDD／OpenSpec。ds.2 分支上的小修正：`memory_size_check.py` 補 `import re`（上游沒有，帶進來）；`dsh_setup_check.py` 把 `CH-xx` 當完整條目的那一個不帶，改用 2.2.1-ds.1 已有的修法（`OD/ACT` 以外的 `ID:` 行跳過並提示，selftest `setup_shadow` 有測）。

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
- 新增 `templates/openspec_config.yaml`（OpenSpec 原生 `rules:`／`operations:`）；`director_work.example.json` 附上完整的 `"sdd"` 物件（全開，`openspec_bin: null`），說明在 `docs/13`。
- `metrics_report.py`：「額度用量」列改指 DSH 版的 `dsh_usage.py`（原本指 Claude 版的 `usage_report.py`，本版已移除）。

### 升級注意
- 預設全開：舊的 Standard／Strict 工單沒有 `SPEC_CHANGE`／`TESTS_LOCKED`、STOP_RULES 寫 2 輪，`gate_check.py --order` 會判不過。舊工單用 `--warn`／`--since`，或在專案 `director_work.json` 把對應開關設成 `false`。
- 沒裝 OpenSpec 的專案：關掉 `require_spec_for_standard`／`require_spec_for_strict`（BOOTSTRAP 10.5 第 5 點）。

### 驗證
- `selftest_ds.py`：2.2.1-ds.1 的 14 項加 ds.2 的 8 個 `sdd_*` → 22/22 PASS（`OPENSPEC_BIN` 指到實機 OpenSpec 1.16.0）；不設時 21 PASS、1 SKIP（`sdd_real_openspec`）。ds.2 分支在 2.2.0-ds.1 上是 11/11 → 19/19。
- 試跑找到並已修進來：`validate --strict` 要求 Requirement 含英文 SHALL／MUST（改用原生 `init --language zh-TW`）；archive 後主規格 Purpose 要 ≥50 字元；`python -I -m unittest <模組>` 找不到 cwd 的測試（CHECKS 改 `discover -s .`）；交件時未勾的任務原本不查。
- 試跑：`_work/demo-project` 一張 Standard 工單走完 propose → 審查 → tasks 核准 → apply → 交件檢查 → archive，見 `_work/ds2-openspec/TRIAL.md`（Claude 模擬 worker）。DSH 實機（deepseek-flash）：PO 照 `_work/ds2-openspec/PO_RUN.md` 貼一段 prompt 跑完，總監照 `_work/ds2-openspec/VERIFY.md` 驗，34/34 PASS；踩到的注意事項寫在 `docs/13`「DSH 實機注意」。

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