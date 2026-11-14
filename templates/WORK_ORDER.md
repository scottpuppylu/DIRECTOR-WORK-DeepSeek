# WO-<編號> — <短名>
**<一句話目標>**

```text
ISSUED_BY      = 總監  <YYYY-MM-DD HH:MM，讀 date>
REVISION       = 1    # 開工後每改一次 +1，並在 H 節加一列
TRACES_TO      = <這張工單服務的初衷卡、需求或決定編號，逗號分隔，例如 B-2, DD-03；有初衷卡時至少一個 B 編號（docs/12）；沒有寫 NONE>
BRIEF_REVISION        = <選用：初衷卡版次；不用就刪掉這兩行>
BRIEF_FINGERPRINTS_V1 = <選用：gate_check.py --brief BRIEF.md 印的 {"B-2": "<64 位雜湊>"}>
PRIMARY_WORKER = 子代理「<名稱>」（例：w1；總監用 subagent 開，名稱只能小寫英數和 -）
MODEL / EFFORT = deepseek-flash / <off|low|high|max>（理由見 docs/05；開工時指定，開完不能中途改）
FALLBACK       = <同名子代理續談（send_message 從 RESUME_STATE 接續）| 開接班子代理>
GOVERNANCE     = <Direct | Standard | Strict>
BASE_REF       = <branch @ commit 或 tag>
NEW_BRANCH     = <分支名>
WORKTREE       = <選用：自己用 git worktree 開的隔離目錄；DSH 沒有 worktree 機制，預設所有子代理共用同一 checkout，不用就填「共用 checkout」>
WORK_DIR       = <放報告、RESUME_STATE.md、輸出的資料夾>
BUDGET         = <US$0 | PO 核准的金額>
HEAVY_RESOURCE = <無 | 需先 TEST REQUEST：類型、預估分鐘>
SPEC_CHANGE    = <openspec/changes/<名稱> | NONE>   # Standard／Strict 必填且不可為 NONE（docs/13）；Direct 寫 NONE
```

`SPEC_CHANGE`（ds.2）：派工前由總監寫好的 OpenSpec 變更資料夾（相對專案根目錄）。`gate_check.py --order <本工單> --repo <專案>` 會確認資料夾存在並實際跑 `openspec validate <名稱> --strict --json`；找不到 openspec 指令也判不過。

兩個 `BRIEF_` 欄位是選用的：寫了以後，工單依據的初衷卡列被改掉時，`gate_check.py --order / --match --brief BRIEF.md` 印 `~ BRIEF_STALE`（舊條件驗過，新條件待重驗）；只是提示，不改結果。不寫照樣通過。

## A. 背景
需求、已知事實（附證據等級）、限制。只寫 worker 需要知道的。

## B. 目標
- MUST HAVE：
- OPTIONAL：
- OUT OF SCOPE：

可以改和不准碰的路徑（`tools/scope_check.py` 直接讀這兩份清單）：

```text
SCOPE:
- <相對 repo 根目錄的路徑或 glob，一行一個>
FORBIDDEN:
- <不准碰的路徑或 glob；沒有就寫 NONE>
```

大小上限（ds.2，Standard／Strict）：最後結果 ≤3 個檔、約 200 行（新增＋刪除；`openspec/` 不算），`scope_check.py` 超過就印 `OVERSIZE`。估計會超過就拆成幾張工單。FORBIDDEN 加上 `openspec/changes/<名稱>/specs/**`、`openspec/changes/<名稱>/proposal.md` 和 TESTS_LOCKED 的測試檔：worker 只寫 `openspec/changes/<名稱>/tasks.md` 和程式。

`*` 不跨資料夾，`**` 跨資料夾，沒有萬用字元的名稱連底下全部都算。兩邊都符合時以 FORBIDDEN 為準。不要寫「相關檔案」這種話。

DSH 的子代理共用同一個 checkout（沒有 per-workstream worktree 隔離），所以 SCOPE / FORBIDDEN 和檔案歸屬（Single Writer）就是唯一的寫入邊界；總監交件時用 `scope_check.py` 對 diff，再看過實際改動。

選用：一定要改到的路徑。`scope_check.py` 會查每一條都有對到改動，沒對到就印 `MISSING` 並判越界；每一條都要在 SCOPE 裡、不在 FORBIDDEN 裡（`gate_check.py --order` 會查）。不需要就整段不寫。比的是最後結果（2.2）：改了又改回的不算；總監審查時用 `scope_check.py --order 本工單 --repo <repo> --candidate <候選 commit>`。

```text
REQUIRED_CHANGES:
- <一定要改到的路徑或 glob，例如 src/parser.py>
```

## C. 執行前檢查
repo 與分支、工作樹乾淨、未提交修改、相關規範、相依、實際行為、能否重現、基準測試。路徑不存在先搜尋，不假設。
製作類工單先做既有資產盤點：未合併分支（`git log --all -- <路徑>`）、需求方提供過的檔案、舊報告；結果寫進 TASK REPORT 的 DONE（docs/02）。

## D. 實作要求
沿用現有架構；最小但完整；處理例外；必要的向後相容；補上直接相關的測試；不做無關重構。每項修改做成開關，方便批次驗證（docs/02）。

計畫閘門（ds.2，Standard／Strict）：第一步只寫 `openspec/changes/<名稱>/tasks.md`（OpenSpec 格式 `- [ ] 1.1 …`，每項對到 specs 的 Requirement），用 `send_message` 交給總監，**等總監回覆已核准（DIRECTOR_LOG 有 `PLAN_APPROVED`）才寫程式**。之後照 tasks.md 做，做完一項打勾一項；要加、改、刪任務先回報總監。不改 specs、proposal 和 TESTS_LOCKED 的測試。

## E. 驗收條件
| ID | 類型 | 要求 | 驗證方法 | 預期 |
|---|---|---|---|---|
| AC-1 | <AUTO / REVIEW / PO> | | | |

- `AUTO`：有指令可以重跑。總監自己重跑後判定；驗證指令用 `evidence_record.py` 留紀錄。核准的指令寫在下面的 `CHECKS:`（選用，Strict 建議寫），一條 AUTO 一行，JSON 字串陣列、不經 shell；` #` 之後是註解，要保留 ` #` 就把整個項目用反引號包起來；派工雜湊會鎖住它，總監用 `evidence_record.py verify --rerun --order` 跑的就是這一行，worker 用同一個指令記錄（`evidence_record.py run --order <本工單>`）：

```text
CHECKS:
- AC-1: ["python", "-I", "-m", "unittest", "tests.test_parser"]
```

  CHECKS 可以放任何可重跑的指令，包括本規則包的檢查工具（路徑照專案實際位置寫）：`["python", "-I", "-X", "utf8", "<WS>/DIRECTOR/tools/round_check.py", "--resume", "<WS>/DIRECTOR/RESUME_STATE.md"]`。放進 CHECKS 就等於核准它在 `--rerun` 時被執行。
- `REVIEW`：要有人看成品。開工前寫明誰看、從哪個角度看、看多大範圍、看哪些常識閘門項目（docs/07）。reviewer 用 `subagent` 開；DSH 子代理預設拿到完整工具集，不能只給讀取工具，所以 review 的範圍靠工單指示＋總監事後用 `dsh_audit.py` 核對（docs/07）。worker 最多填 `READY_FOR_REVIEW`。
- `PO`：PO 保留的判定，例如最終驗收。worker 和總監都只填 `PENDING_PO`。同一個 commit 給 PO 看兩份以上成品時，報告寫 `CANDIDATE_ID: <PO_ACCEPTANCE 的 candidate_id>`（2.2）。
- 接手演練、要用 `metrics_report --run --compare` 比較的工單：run 資料夾的 `run.json` 要寫 `sampling` 標記（`complete`、`scenario`），否則比較結果是 UNKNOWN（2.2，`tools/README.md`）。
- 選用的 `追溯` 欄（加在表的最後一欄）：這條 AC 驗證 TRACES_TO 的哪些編號，例如 `DD-03`；沒有寫 `—`。不加這欄也照樣通過；加了之後 `trace_report.py` 每個編號一列，不必猜哪條 AC 服務哪個需求。

- 驗收優先寫 `AUTO`（ds.2）：能用指令判定的就不要寫成 REVIEW／PO。
- 測試先寫並鎖定（ds.2，Standard／Strict）：驗收測試在派工前寫好並 commit 到 BASE_REF，`python -I -X utf8 tools/sdd_gate.py --lock-tests <測試檔> --repo <專案>` 印的清單貼在下面；worker 不得改，改了 `gate_check.py` 判不過。沒有測試的文件類工單寫 `- NONE  # 理由`。

```text
TESTS_LOCKED:
- <相對專案根目錄的測試檔> sha256=<64 位>
```

結果不寫在這裡，寫在 TASK REPORT 的 ACCEPTANCE 表。成品類交件另附常識閘門表（docs/07）。

## F. 安全與版控
照 docs/08。驗收條件和規格不准改，有問題回報 BLOCKED 由總監裁決（docs/02）。總監派工時記下本檔雜湊，交件時比對；DSH 沒有 hook 主動擋改工單，改了會被雜湊查出來，但工具擋不住改動。本工單特別禁止：<...>

## G. 交付與停止規則
- DELIVERABLES：<檔案、commit / tag、審查包>
- 完成：一則 TASK REPORT 給總監（templates/TASK_REPORT.md），並用 `send_message` 通知總監。
- STOP_RULES：同一根因 1 輪沒進展就停並回報（ds.2；開關 `sdd.stop_after_rounds`）；超出 SCOPE 先問；超過測試上限 10 分鐘先停下回報。

## H. 變更紀錄
只有總監能改本工單。REVISION 1 不用寫；之後每改一次加一列，再把新的雜湊告訴 worker。

| 版本 | 時間 | 誰改 | 原因 | 影響的 AC |
|---|---|---|---|---|
