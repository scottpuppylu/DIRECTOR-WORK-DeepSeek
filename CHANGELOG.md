# CHANGELOG — DeepSeek Harness 版

本 repo 是 [DIRECTOR-WORK](https://github.com/scottpuppylu/DIRECTOR-WORK) v2.2.2（Claude Code／Claude Desktop 版，MIT）的移植。
上游的完整變更歷史保留在 [`CHANGELOG-upstream.md`](CHANGELOG-upstream.md)；本檔只記 DeepSeek 版自己的變更。

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