# 13 安全閘門（2.2.5-ds.5；原「規格先行（SDD）與 OpenSpec」，ds.2～ds.4）

本檔是 DeepSeek Harness 版自己的規則。寫 Standard／Strict 工單前讀。規則摘要也寫在 `docs/02`；本檔放完整流程、設定開關和「誰能關」。

## 2.2.5-ds.5 改了什麼

- **拿掉 OpenSpec**：CLI 的尋找、安裝、`init`、`openspec_bin`、`openspec validate`／`archive`、工單的 `SPEC_CHANGE` 欄位、`openspec/changes/` 資料夾、`require_spec_for_*` 開關都不再使用。
  - 理由（WO-DS-008 r2，總監依評分判斷，PO 授權）：OpenSpec 本身沒有量到正確性效益。`validate` 全過，隱藏測試卻是 85/107（開 SDD）對 101/107（關 SDD）。
  - 失分的兩個原因：拆成 8 個 change 後沒做整合驗收；規格裡自訂的限制擋掉真實資料，Traceback 外漏。這兩項改由最終端到端驗收（移植 DW 2.2.5）和規格審查清單處理。
  - sdd 組的額度是 UNKNOWN，OpenSpec 的成本也無法證明划算。
  - ds.4 的程式在 tag `v2.2.4-ds.4`。日後重測若證明 OpenSpec 有用，從那裡拿回來。
- **安全閘門保留**：同一次試驗量到它們有用。
  - 派工段：sdd 組 31 分，nosdd 組 29 分。
  - 計畫關：sdd 組 3 分，PLAN_APPROVED 在 worker 動工前；nosdd 組 1 分，5 張是事後補寫。
  - 審查關：sdd 組 3 分，有 8 個獨立審查 session；nosdd 組 2 分，lead 自審。
  - 這些閘門不需要 OpenSpec。原本的 `tools/sdd_gate.py` 改名成 `tools/safety_gate.py`；設定從 `"sdd"` 改到 `"safety"`。

## 為什麼要比 Claude 版嚴

- Claude 版很多品質靠 Opus 的判斷力，以及 Claude Desktop 的機制（hook、session、可以中途改 effort）。
- DSH 上的 worker 是 `deepseek-flash`，判斷力較弱；DSH 0.2.2-rc.2 沒有 hook，子代理開了以後不能改 effort。
- 所以把判斷前移：**驗收測試和計畫在寫程式前就寫好並鎖住**，worker 照著做。做歪了由程式查出來，不靠 worker 自己發現。

## 流程（Standard／Strict）

| 步 | 誰 | 做什麼 | 留下什麼 |
|---|---|---|---|
| 1 | 總監 | 寫需求：寫在工單的 ACCEPTANCE。逐項想過 `templates/WORK_ORDER.md` E 節的邊界與壓力清單，用得到的每一項都要有一條 AC 或測試；需求寫「不當掉」時，至少一條用極端輸入 | 工單草稿 |
| 2 | 總監（或測試子代理） | **測試先寫**：照 AC 寫驗收測試，commit 到 BASE_REF。`python -I -X utf8 tools/safety_gate.py --lock-tests <測試檔> --repo <專案>` 印出 `TESTS_LOCKED:`，貼進工單。`CHECKS:` 寫跑這些測試的指令（AUTO 優先） | 工單 `TESTS_LOCKED`、`CHECKS` |
| 3 | 總監 | 完成工單：一張最多 3 個檔、約 200 行，超過就拆；`FORBIDDEN` 加上鎖定的測試檔；`STOP_RULES` 寫「同一根因 1 輪沒進展就停」；`WORK_DIR` 寫好（計畫檔放在那裡） | 工單 |
| 4 | 總監 | 跑 `gate_check.py --order <工單> --repo <專案>`，要通過。這一步會比對鎖定測試的雜湊、輪數，也會查安全開關有沒有被關掉 | — |
| 5 | 總監開的審查子代理 | 規格審查，照 `templates/SPEC_REVIEW.md`；Standard 也要做。總監在 DIRECTOR_LOG 記 `SPEC_REVIEW <WO> tokens=… issues=… adopted=…` | DIRECTOR_LOG |
| 6 | 總監 | 派工：`gate_check.py --hash` 的 `DISPATCH` 行寫進 DIRECTOR_LOG；開 worker，worker 用自己的 worktree（`docs/11`） | DIRECTOR_LOG |
| 7 | worker | **計畫閘門**：只寫 `<WORK_DIR>/<WO>/PLAN.md`，格式是 `- [ ] 1.1 …`，每項對到一條 AC。用 `send_message` 交給總監，**等核准才寫程式** | PLAN.md |
| 8 | 總監 | 看計畫有沒有照 AC、有沒有超出 SCOPE。核准就跑 `safety_gate.py --plan-hash <PLAN.md> --order <工單>`，把印出的 `PLAN_APPROVED <WO> sha=<64>` 整行寫進 DIRECTOR_LOG，再 `send_message` 通知 worker | DIRECTOR_LOG |
| 9 | worker | 照 PLAN.md 實作，做完一項打勾一項。不改鎖定的測試，不加項目（要改計畫先回報總監）。同一根因 1 輪沒進展就停並回報 | commit |
| 10 | worker → 總監 | 交件照 `docs/02`：`scope_check.py`（含大小上限）、`gate_check.py --match … --dispatch-log DIRECTOR_LOG.md --repo <專案>`、`evidence_record.py` | TASK REPORT |
| 11 | 總監 | 收尾：最終端到端驗收（移植 DW 2.2.5 後的版本）、`dsh_usage.py --out`（BOOTSTRAP「收尾」） | 裁決 |

Direct 工單不走這套（純查詢、文件、沒有風險）。

## 程式會擋什麼

| 規則 | 誰查 | 什麼時候 | 開關（`director_work.json` 的 `"safety"`，預設全開） |
|---|---|---|---|
| 測試先寫且鎖定：Standard／Strict 要有 `TESTS_LOCKED`（docs-only 寫 `- NONE  # 理由`），檔案雜湊不符就**判不過** | `gate_check.py --order / --match` | 派工前、交件時 | `tests_first` |
| 規格審查：要有 `SPEC_REVIEW <WO> tokens=… issues=… adopted=…` 整行。沒給 `--dispatch-log` 也查：工單所在 DIRECTOR 的 DIRECTOR_LOG.md，或 `reviews/` 下檔名有工單編號和 SPEC_REVIEW 的檔。找不到就**判不過**；行裡缺 tokens／issues／adopted 印 note | `gate_check.py --match` | 交件時 | `spec_review_for_standard`（Strict 一律要） |
| 計畫閘門：DIRECTOR_LOG 要有 `PLAN_APPROVED <WO> sha=<64>`；`<WORK_DIR>/<WO>/PLAN.md` 和核准的版本比，只准多打勾，交件時要全部勾完（只有 `[x]` 算完成）；找不到 PLAN.md 也**判不過** | `gate_check.py --match --dispatch-log` | 交件時 | `plan_gate` |
| STOP_RULES 允許的輪數不能超過 1 | `gate_check.py --order` | 派工前 | `stop_after_rounds` |
| 至少一條 AUTO 驗收（只提示，不是閘門；關掉只印 note） | `gate_check.py --order` | 派工前 | `prefer_auto` |
| 安全閘門不得自行放寬：對 Standard／Strict 把 `tests_first`、`plan_gate`、`spec_review_for_standard` 設成 `false`，或把 `stop_after_rounds` 設成 0／`false`、調高到超過 1，要有 PO 的答覆；還在 open 或沒寫就**判不過**（下一節） | `gate_check.py --order` | 派工前 | — |
| 工單大小：最後結果最多 3 個檔、200 行（新增＋刪除）；測試檔（`test_*.py`、`*_test.py`、`tests/` 下）算檔數，行數另算，最多 400 | `scope_check.py` | 交件時 | 頂層 `"order_limits"`：`max_files_per_order`、`max_lines_per_order`、`max_test_lines_per_order`（0＝關） |
| 受保護的測試只准新增：`TESTS_LOCKED` 的檔和頂層 `"protected_tests"` 列的檔 | `scope_check.py`、`gate_check.py --match` | 交件時 | `"protected_tests"` |

沒寫的鍵一律用預設值（全開）。把下面這段併進專案的 `DIRECTOR/director_work.json` 就是完整寫法（`director_work.example.json` 已附上同一段）：

```json
"safety": {
  "tests_first": true,
  "plan_gate": true,
  "spec_review_for_standard": true,
  "stop_after_rounds": 1,
  "prefer_auto": true
},
"order_limits": {
  "max_files_per_order": 3,
  "max_lines_per_order": 200,
  "max_test_lines_per_order": 400
}
```

`scope_check.py` 的 `SIZE:` 行印三個數：`files= lines= test_lines= limit=3/200/400`。

工具通過只代表測試沒被改、計畫沒被偷換、審查有記錄、改動夠小。**不代表需求寫對了**。需求對不對，靠第 5 步的審查和總監自己讀。

## 誰能關（2.2.3-ds.3 起；2.2.5-ds.5 套到安全開關）

WO-DS-004 試驗：DSH lead 自己寫一筆 DD，把保護關掉，整層規則沒用上。所以：

- **lead 不得自行關閉或放寬安全閘門。** 要對 Standard／Strict 關掉 `tests_first`、`plan_gate`、`spec_review_for_standard`，或把 `stop_after_rounds` 設成 0／`false`、調高到超過 1（例如 2），先在 PO_PENDING 寫一項（寫明開關名稱、理由、建議），等 PO 回答。
- PO 答應後（STATUS answered／closed，有 ANSWER），`gate_check.py --order` 才會放行，只印 note。沒寫、或還是 open，`--order` 判不過。
- `prefer_auto` 只是提示，不是閘門：設成 `false` 不用 PO 答覆，`--order` 只印一行 note。

## 舊設定檔的 `"sdd"` 區塊

舊的 `"sdd"` 區塊照讀，不會報錯。工具會印 WARN：

- `tests_first`、`plan_gate`、`spec_review_for_standard`、`stop_after_rounds`、`prefer_auto` 照讀，印「請搬到 safety」。
- `"safety"` 也寫了同一個鍵時，以 `"safety"` 為準，`sdd` 那一個印「被忽略」。
- `openspec_bin`、`require_spec_for_*` 和其他鍵忽略，印「OpenSpec 已在 2.2.5-ds.5 移除，此鍵被忽略」。
- `sdd.max_files_per_order`／`sdd.max_lines_per_order` 照讀，印「請搬到 order_limits」（2.2.4-ds.4 起）。
- `bootstrap_repo.py` 不找 CLI、不跑 init、不寫設定（L-061 的重現案例）。
- 工單還有 `SPEC_CHANGE` 這一行時，只印 note，不檢查。
