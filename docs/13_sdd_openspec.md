# 13 規格先行（SDD）與 OpenSpec（ds.2）

本檔是 DeepSeek Harness 版新增的（2.2.0-ds.2）。寫 Standard／Strict 工單前讀。規則摘要也寫在 `docs/02`；本檔放完整流程、設定開關、安裝和選型理由。

## 為什麼要更嚴

- Claude 版很多品質靠 Opus 的判斷力和 Claude Desktop 的機制（hook、session、可中途改 effort）。DSH 上的 worker 是 `deepseek-flash`，判斷力較弱；DSH 0.2.2-rc.2 沒有 hook，子代理開完不能改 effort。
- 所以把判斷前移：**規格、驗收測試、計畫在寫程式前就寫死並鎖住**，worker 只照著做；做歪了由程式查出來，不靠 worker 自己發現。
- 規格層用現成的 OpenSpec（PO 規則：GitHub 有維護中、授權相容的方案就採用，自己只寫膠水）。DW-DS 自己只寫 `tools/sdd_gate.py`（接工單）和 `gate_check.py`／`scope_check.py` 的呼叫點。

## 流程（Standard／Strict）

| 步 | 誰 | 做什麼 | 留下什麼 |
|---|---|---|---|
| 1 | 總監（或總監開的規格子代理） | `openspec new change <名稱>`，寫 `proposal.md`、`specs/<能力>/spec.md`（每條 Requirement 至少一個 `#### Scenario:`）；需要時寫 `design.md`。不寫 `tasks.md`。 | `openspec/changes/<名稱>/` |
| 2 | 總監 | `openspec validate <名稱> --strict` 通過 | — |
| 3 | 總監（或測試子代理） | **測試先寫**：照 Scenario 寫驗收測試，和規格一起 commit 到 BASE_REF；`python -I -X utf8 tools/sdd_gate.py --lock-tests <測試檔> --repo <專案>` 印出 `TESTS_LOCKED:` 貼進工單；`CHECKS:` 寫跑這些測試的指令（AUTO 優先） | 工單 `TESTS_LOCKED`、`CHECKS` |
| 4 | 總監 | 寫工單：`SPEC_CHANGE = openspec/changes/<名稱>`；一張 ≤3 個檔、約 200 行（超過就拆）；`FORBIDDEN` 加上 `openspec/changes/<名稱>/specs/**`、`openspec/changes/<名稱>/proposal.md` 和鎖定的測試檔；`STOP_RULES` 寫「同一根因 1 輪沒進展就停」 | 工單 |
| 5 | 總監 | `gate_check.py --order <工單> --repo <專案>` 通過（會跑 `openspec validate --strict --json`、比對鎖定測試的雜湊） | — |
| 6 | 總監開的審查子代理 | 規格審查（`templates/SPEC_REVIEW.md`，Standard 也要做）；總監在 DIRECTOR_LOG 記 `SPEC_REVIEW <WO> tokens=… issues=… adopted=…` | DIRECTOR_LOG |
| 7 | 總監 | 派工：`gate_check.py --hash` 的 `DISPATCH` 行寫進 DIRECTOR_LOG；開 worker | DIRECTOR_LOG |
| 8 | worker | **計畫閘門**：只寫 `openspec/changes/<名稱>/tasks.md`（OpenSpec 的 tasks 格式，`- [ ] 1.1 …`），用 `send_message` 交給總監，**等核准才寫程式** | tasks.md |
| 9 | 總監 | 看 tasks.md 有沒有照規格、有沒有超出 SCOPE；核准就跑 `sdd_gate.py --plan-hash <tasks.md> --order <工單>`，把印出的 `PLAN_APPROVED <WO> sha=<64>` 整行寫進 DIRECTOR_LOG，再 `send_message` 通知 worker | DIRECTOR_LOG |
| 10 | worker | 照 tasks.md 實作（OpenSpec 的 `openspec-apply-change` skill），做完一項打勾一項；不改規格、不改鎖定的測試、不加 tasks（要改計畫先回報總監）；同一根因 1 輪沒進展就停並回報 | commit |
| 11 | worker → 總監 | 交件照 `docs/02`：`scope_check.py`（含大小上限）、`gate_check.py --match … --dispatch-log DIRECTOR_LOG.md --repo <專案>`、`evidence_record.py` | TASK REPORT |
| 12 | 總監 | 接受後 `openspec archive <名稱> --yes`（把 delta 併進 `openspec/specs/`）並 commit；之後這張工單 `--order` 會印「已封存，略過 validate」 | `openspec/changes/archive/` |

Direct 工單不走這套（純查詢、文件、沒有風險）。

## 程式會擋什麼

| 規則 | 誰查 | 什麼時候 | 設定開關（`director_work.json` 的 `"sdd"`，預設全開） |
|---|---|---|---|
| Standard／Strict 必須有 `SPEC_CHANGE`，資料夾存在，`openspec validate <名稱> --strict --json` 通過；找不到 CLI 或跑不起來**判不過** | `gate_check.py --order / --match` | 派工前、交件時 | `require_spec_for_standard`、`require_spec_for_strict` |
| Strict 的變更不能 `skip_specs: true`（Standard 只提示） | 同上 | 同上 | — |
| 測試先寫且鎖定：要有 `TESTS_LOCKED`（docs-only 寫 `- NONE  # 理由`），檔案雜湊不符就判不過 | `gate_check.py --order / --match` | 同上 | `tests_first` |
| Standard 也要規格審查：DIRECTOR_LOG 要有 `SPEC_REVIEW <WO>` 整行 | `gate_check.py --match --dispatch-log` | 交件時 | `spec_review_for_standard`（Strict 一律要） |
| 計畫閘門：DIRECTOR_LOG 要有 `PLAN_APPROVED <WO> sha=<64>`；tasks.md 和核准的版本比，只准多打勾，而且交件時要全部勾完（只有 `[x]` 算完成，照 OpenSpec） | `gate_check.py --match --dispatch-log` | 交件時 | `plan_gate` |
| 工單大小：最後結果 ≤3 個檔、≤200 行（新增＋刪除；`openspec/` 不算） | `scope_check.py` | 交件時 | `max_files_per_order`、`max_lines_per_order`（0＝關） |
| STOP_RULES 允許的輪數不能超過 1 | `gate_check.py --order` | 派工前 | `stop_after_rounds` |
| 至少一條 AUTO 驗收（只提示） | `gate_check.py --order` | 派工前 | `prefer_auto` |
| openspec 執行檔位置 | `sdd_gate.py` | — | `openspec_bin`（環境變數 `OPENSPEC_BIN` 優先） |

要對某個專案關掉一條，就把開關設成 `false`（大小設 0），並在 DIRECTOR_LOG 寫理由。沒寫的鍵一律用預設值（全開）；把下面這段併進專案的 `DIRECTOR/director_work.json` 就是完整寫法：

```json
"sdd": {
  "require_spec_for_strict": true,
  "require_spec_for_standard": true,
  "spec_review_for_standard": true,
  "tests_first": true,
  "plan_gate": true,
  "max_files_per_order": 3,
  "max_lines_per_order": 200,
  "stop_after_rounds": 1,
  "prefer_auto": true,
  "openspec_bin": null
}
```

工具通過只代表規格格式對、測試沒被改、計畫沒被偷換、改動夠小；**不代表規格寫對了**。規格對不對靠第 6 步的審查和總監自己讀。

## 哪些是 OpenSpec 原生、哪些是膠水

| 需要 | 用什麼 | 為什麼不是 OpenSpec 原生 |
|---|---|---|
| 規格、提案、設計、任務的格式和資料夾 | OpenSpec 原生（`openspec new change`、spec-driven schema） | — |
| 規格驗證 | OpenSpec 原生（`openspec validate --strict --json`） | — |
| 給 DSH 代理的操作說明 | OpenSpec 原生（`openspec init --tools agents` 寫進 `.agents/skills/`） | — |
| 專案層的寫作規則（tasks 要小、測試先寫…） | OpenSpec 原生（`openspec/config.yaml` 的 `rules:`；範本 `templates/openspec_config.yaml`） | — |
| 封存、把 delta 併進主規格 | OpenSpec 原生（`openspec archive`） | — |
| 工單要指到哪個變更、沒 CLI 不能算過 | 膠水：`sdd_gate.py`（`gate_check.py` 呼叫） | OpenSpec 不知道工單和治理模式 |
| 鎖定驗收測試 | 膠水：`TESTS_LOCKED` + 雜湊 | OpenSpec 有 Scenario，沒有測試檔和雜湊 |
| 計畫核准 | 膠水：`PLAN_APPROVED` 行 + 去掉勾選後的雜湊 | OpenSpec 有 tasks 勾選，沒有「核准」這一步 |
| 規格審查紀錄 | 沿用 DW 的 `SPEC_REVIEW` 行 | OpenSpec 沒有審查紀錄 |
| 工單大小上限 | 膠水：`scope_check.py` 的 `OVERSIZE` | OpenSpec 不限變更大小 |

## 安裝（免費、本機、鎖版本）

- 版本鎖 **`@fission-ai/openspec@1.16.0`**（2026-10-30 發布，MIT）。不用 2.0.0：2026-11-11 才發布的大版本，還沒經過兩週；要升級時另開工單，先跑 `selftest_ds.py`。
- 需要 Node 22.12 以上（本機實測 Node 24.14.1）。
- 裝在使用者層的獨立資料夾，不裝全域、不改 PATH、不跑套件的安裝腳本：

```bash
npm install --prefix "%LOCALAPPDATA%/dw-ds-tools/openspec-1.16.0" --ignore-scripts --no-fund --no-audit @fission-ai/openspec@1.16.0
```

- 告訴工具在哪裡（擇一）：專案 `DIRECTOR/director_work.json` 的 `"sdd": {"openspec_bin": "<上面資料夾>/node_modules/.bin/openspec.cmd"}`；或環境變數 `OPENSPEC_BIN`；或自己把 `node_modules/.bin` 加進 PATH。指到 `node_modules/@fission-ai/openspec/bin/openspec.js` 也可以（工具用 `node` 跑它）。
- 確認：`python -I -X utf8 tools/sdd_gate.py --which --config DIRECTOR/director_work.json` 印出 `OPENSPEC: … version=1.16.0`。
- OpenSpec 預設會送匿名使用統計（只有指令名和版本）。DW-DS 的工具呼叫時一律帶 `OPENSPEC_TELEMETRY=0`；自己在終端機手動跑時也設這個環境變數，或跑一次 `openspec config set telemetry.enabled false`。
- 專案初始化：在專案根目錄跑 `openspec init --tools agents --language zh-TW --no-animation`，產生 `openspec/` 和 `.agents/skills/openspec-*`（6 個 skill，DSH 從 `<專案>/.agents/skills` 載入）。`--language zh-TW` 是 OpenSpec 原生選項，會在 `openspec/config.yaml` 寫「產出用 zh-TW、結構標題和 SHALL/MUST 保留英文」。再把 `templates/openspec_config.yaml` 的 `context:` 其餘幾行和 `rules:`、`operations:` 併進去。
- 寫 `CHECKS:` 跑 Python 測試時用 `python -B -I -m unittest discover -s . -p <測試檔>`：`-I` 不把目前資料夾放進 sys.path，`python -I -m unittest <模組名>` 會找不到測試（試跑時規格審查抓到）。
- 實測：`validate --strict` 要求每條 Requirement 的句子含英文 `SHALL` 或 `MUST`，中文也一樣（例：「計算機 SHALL 用 a 減 b。」）；只寫「要能」會判不過。
- 實測：`openspec archive` 把新能力併進 `openspec/specs/<能力>/spec.md` 時，`## Purpose` 少於 50 個字元會被 `validate --specs --strict` 判太短。中文 50 個字元大約是兩句話，新能力的 Purpose 要寫足。
- 實測補充：OpenSpec 1.16.0 也有原生的 `--tools dsh`（寫進 `.dsh/skills/`，DSH 一樣會讀）。工單指定用 `agents`；`agents` 也能給其他代理工具共用，所以照用。

## 選型：OpenSpec 和 Spec Kit

| | OpenSpec（Fission-AI/OpenSpec） | Spec Kit（github/spec-kit） |
|---|---|---|
| 授權 | MIT | MIT |
| 需要 | Node 22.12+（npm 一行裝） | Python 3.11+ 和 uv |
| 單位 | 每個變更一個資料夾（proposal／specs delta／design／tasks），做完封存併進主規格 | 每個功能一套 spec／plan／tasks，流程分 constitution → specify → plan → tasks → implement |
| 機器可讀的驗證 | `openspec validate <名稱> --strict --json`，exit code＋JSON | 以斜線指令和模板為主；總監 2026-11-14 讀文件時沒有找到同等的 `--json` 驗證指令（worker 沒有實裝 Spec Kit 驗證這一點） |
| DSH 能不能直接用 | `init --tools agents` 寫 `.agents/skills/`（DSH 讀這裡）；1.16.0 另有原生 `dsh` 目標 | 要自己把指令接到 DSH |
| 重量 | 輕：只在要改的地方寫 delta | 較重：每個功能從頭走完整流程 |

- 選 OpenSpec：輕、可以用 exit code＋JSON 讓 `gate_check.py` 判定、能直接被 DSH 讀到。對能力較弱的模型，「能用程式判定」比「流程完整」重要。
- Spec Kit 是**備案**：OpenSpec 停止維護、授權改變、或驗證指令拿掉時才換；換的時候只改 `sdd_gate.py` 的 `validate_change`，工單欄位和其他規則不動。
- 查過什麼（2026-11-14）：總監讀了兩邊的 README 與文件（證據等級：文件）；worker 在本機實裝 OpenSpec 1.16.0，實測 `init --tools agents`／`--tools dsh`、`new change`、`validate --strict --json`（成功、失敗、找不到變更三種輸出）、`instructions apply`、`archive --help`（證據等級：VERIFIED_LOCAL）。Spec Kit 沒有實裝。

## 已知限制

- DSH 實機（deepseek-flash）照本流程跑一張工單還沒做；是 PO 步驟，見 `_work/ds2-openspec/TRIAL.md`。
- `openspec validate` 只查格式（每條 Requirement 有 Scenario、delta 標題對），不查規格內容對不對。
- worker 仍然改得動規格和測試檔；工具做的是事後查出（`FORBIDDEN`＋`TESTS_LOCKED` 雜湊＋`PLAN_APPROVED` 雜湊），不是事前擋住（DSH 沒有 hook）。
- 大小上限算的是最後結果的行數，搬檔案、重排格式也會算進去；真的需要大改就拆工單或由總監在 DIRECTOR_LOG 寫理由後調開關。

## 為什麼

- 規格和測試先寫死，弱模型的錯就會變成「測試不過」這種程式查得到的失敗，不會變成「看起來做完了」。
- 一張工單小到 3 個檔、200 行，worker 一次只需要記住一件事；返工時損失也小。
- 計畫先核，總監花幾分鐘看 tasks.md，就能擋掉整輪做錯方向的實作；DSH 子代理開完不能改 effort，做錯方向的代價比 Claude 版高。
- STOP 從 2 輪改 1 輪：弱模型第二輪常常重複第一輪的錯，早停交給總監換做法或開更高 effort 的接班人比較便宜。
