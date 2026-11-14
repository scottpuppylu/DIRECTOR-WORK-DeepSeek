# 11 在 DeepSeek Harness 上操作

本檔是 DeepSeek Harness（DSH）版，取代 Claude 版的 `docs/11_claude_desktop.md`。
只在 DSH 上當總監時讀，不列入每輪必讀。規則照 `docs/01` 到 `docs/10`；這裡只寫「流程需要的能力，在 DSH 上用哪個工具做」。

## 先看平台

- 模型只有 `deepseek-flash`；思考程度 `off / low / high / max`。總監自己的模型與 effort 由 PO 在 DSH 設定：composer 的模型控制項或 `/model` 選單，套用到下一個請求（進行中的 step 不變）；新 session 的預設值在 Settings → Models。worker 開工時指定、不能中途改（`docs/05`）。
- 總監＝根 session（代理名 `lead`）；worker＝用 `subagent` 工具開的具名子代理。子代理共享同一個檔案系統、可指定 cwd、可續談、會回完成通知。
- 同一棵樹最多 8 個作用中子代理、委派深度 1（worker 不能再開子代理）；這兩個上限在 DSH「設定 → 子代理」。
- 總監必須是**根 session**：DSH 只讓根代理使用 `ask_user_question`、排程與 goal/plan 權限；被開成子代理的「總監」會直接被拒。
- Team 模式（`team_task_*` 共享工作板）預設關閉，可以由 PO 在 model menu 開啟；本版只把它當輔助，工單與狀態檔案才是真相來源。
- **所有子代理共享同一個 checkout 與檔案系統**（不是各自隔離的 worktree），一個子代理改了檔，其他人和總監立刻看得到；DSH 這個 profile 沒有 worktree 工具。Single Writer 靠檔案歸屬＋工單範圍＋總監最後看 diff。
- 工具名稱會隨 DSH 版本變。下面的名稱是 0.2.2 桌面版；找不到時用能力關鍵字在工具清單找，不要猜。

## 能力對照

| 流程需要 | DSH 的做法 | 注意 |
|---|---|---|
| 開 worker | `subagent({name, cwd, prompt, provider, model, reasoning_effort})` | 先寫好工單再開；prompt 只給工單路徑、RESUME_STATE 路徑、一句目標。回傳 `started subagent <name>` 就代表已受理，不會等它做完。第一批要 PO 同意（`docs/12`）。 |
| 傳訊息給 worker | `send_message({agent, message})` | 只在 `docs/03` 的三種情況發。訊息會叫醒閒置的子代理並讓它跑一輪；送達不代表已讀。長內容寫檔，訊息只給路徑。 |
| 看 worker 列表與狀態 | `list_agents()` | 只給名字、running/inactive、description；沒有「正在做什麼」的細節，細節讀它的 `RESUME_STATE.md`。inactive 可能只是做完一輪，不代表結束。 |
| worker 回報 | worker 自己用 `send_message` 傳給總監，或做完一輪後 DSH 送完成通知 | 完成通知會帶最後結論；要它繼續就用 `send_message`。 |
| 讀用量與上下文 | `python -I -X utf8 <WS>/DIRECTOR/tools/dsh_usage.py --project-dir <WS>`（<WS>＝總監 session 啟動資料夾；單一工作線用 `--session <agent>`；加 `--json` 給程式讀）；GUI：每個回合可展開 token usage、composer 的用量統計、Settings → General → Performance & usage | 沒有 `get_usage` 工具。數字是從 session 紀錄算的，量不到記 UNKNOWN，不當成 0；帳號餘額只在 GUI 的帳號頁（模型讀不到）。 |
| 調 worker 的模型/effort | 開子代理時帶 `reasoning_effort`（總監自己的由 PO 在 GUI 設定） | 不能中途改。要換 effort 就開接班子代理，交接靠 `RESUME_STATE.md`，並在 `ACTIVE_WORKSTREAMS.md` 記新 effort。 |
| 叫醒／排程 | `schedule_create`／`schedule_list`／`schedule_view`／`schedule_edit` | 依工具政策**只有 PO 明確要求**才能建立或修改排程；桌面版要開著才會到點；停機後只送最近一次。排程只能送給 session，子代理（delegated）不能用排程工具。 |
| PO 待決 | `ask_user_question`（一次一題到三題，選項各一句說明）＋本機帳 `DIRECTOR/PO_PENDING.md` | 沒有 Claude 的私人頁面、置頂、留言叫醒。答案記回 `PO_PENDING.md` 的 `ANSWER`；聊天只說「待決帳新增 OD-xx」。 |
| 要 PO 看圖挑 | 先把成品截圖用 markdown 圖放在同一則訊息，再用 `ask_user_question` 問 A/B | `ask_user_question` 的選項只有文字與說明，不能放圖；`present` 檔案卡回合結束後才出現，不能當成 PO 已先看到。 |
| 成品給 PO 看 | `present({files:[{path, description}]})`；就在聊天附圖 | 一次 1～2 個最重要的檔（上限 8）；檔案卡在回合結束後出現在右側 sidebar，可預覽圖片；`present` 只宣告成品，不會替你判斷對不對。子代理做的成品要由**總監自己**呼叫 `present` 才會被宣告。 |
| 結束工作線 | 沒有 interrupt／archive 工具 | 先 `send_message` 請它停在安全狀態並寫好 `RESUME_STATE.md`；完成後讓它閒置。真的失控時請 PO 在 GUI 的 subagent catalog 按 Stop，或在工作列的選單封存 session。 |
| 等 worker 做完 | 結束本回合等完成通知；或 `wait_agent`（10 秒～1 小時）等子代理傳來的訊息 | 不要一直發「做完了嗎」；沒有 notify_when_idle。 |
| 禁止 worker 自己問 PO | 規則：worker 只能回報總監 | 已查證：`ask_user_question` 對 delegated 子代理會被拒絕（DELEGATED_CALLER），worker 想問也問不到；工單仍要寫明「有問題回報總監」。 |
| 限制 reviewer 工具 | 子代理預設拿到完整工具集，沒有 per-child 工具限制工具 | 用指示「只准讀」＋總監事後用 `tools/dsh_audit.py` 核對它有沒有寫檔；真的要限制只能改 DSH preset（使用者層，需要 PO 同意）。 |
| 專案指示 | `AGENTS.md`（DSH 也載入 `CLAUDE.md`；本版統一 `AGENTS.md`）＋ `AGENTS.local.md` 疊加；使用者層 `~/.dsh/AGENTS.md`、`~/.agents/AGENTS.md` | 子代理 session 會自動載入（已實測）。改指示後要讓相關 session 重新讀到：下一次成功讀寫到那個目錄，或重開 session。 |
| 檔案沙箱與核准 | 每個 session 有 `read-only / workspace-write / danger-full-access`；核准政策是 session 設定 | **沒有** PreToolUse hooks，hook_guard 不移植。`docs/08` 的「會擋」改成「規則＋PO 核准＋事後 audit」；不要宣稱自動擋。 |
| 規格先行（OpenSpec，ds.2） | 專案根目錄 `openspec init --tools agents --language zh-TW --no-animation`；`openspec new change <名稱>`、`openspec validate <名稱> --strict`、`openspec archive <名稱> --yes`；工單閘門用 `gate_check.py --order <工單> --repo <專案>` | OpenSpec 的 6 個 skill 寫進 `<專案>/.agents/skills/openspec-*`，DSH 的 filesystem skill provider 從這裡載入（rank 200；`.dsh/skills` 是 rank 100，`openspec init --tools dsh` 寫那裡，也能用）。CLI 位置與安裝見 `docs/13`。 |
| 動作紀錄 | `python -I -X utf8 <WS>/DIRECTOR/tools/dsh_audit.py build --session <agent> --out <WS>/DIRECTOR/research/audit-<日期>.jsonl`（`--project-dir <WS>` 抓整個工作區） | 事後從 session 紀錄重建，不是即時 hook；給 `report_vs_audit.py` 和 gate 審查用。子代理 session 記在總監 session 的啟動資料夾下，所以 `--project-dir <REPO>` 抓不到 worker。input 經 secret_mask 後最多記 500 字，長指令尾端會截斷。 |

## 開 worker 的流程

1. 先在待決帳列好要開的線：名稱（`w1`…）、工單路徑、effort、cwd（工作副本；DSH 沒有 per-worker worktree）、範圍。放進 `ACTIVE_WORKSTREAMS.md` 的草案。
2. 請 PO 同意（第一批可以併進初衷卡確認那一句）。沒有同意不開。
3. 同一輪把要開的都開完：每個子代理的 prompt 只給「工單路徑、RESUME_STATE 路徑、一句目標」和限制（不改驗收條件、不碰範圍外、有問題回報總監、不要問 PO）。
4. 開完用 `list_agents()` 確認名字和數量；把實際名稱寫進 `ACTIVE_WORKSTREAMS.md` 和 `DIRECTOR_LOG.md` 的 DISPATCH 行。
5. 之後只靠 `send_message` 和檔案交接；不要為了問進度發訊息（`docs/03`）。
6. Standard／Strict 工單（ds.2，`docs/13`）：開 worker 前，規格（`SPEC_CHANGE`）、鎖定的測試（`TESTS_LOCKED`）和 `SPEC_REVIEW` 都要先完成；prompt 加一句「第一步只寫 tasks.md 交給總監，等 `PLAN_APPROVED` 的通知才寫程式；同一根因 1 輪沒進展就停」。worker 交 tasks.md 時，總監在同一輪看完、核准並 `send_message` 回覆，不讓 worker 空等。

## 常見用法

- **確認指示有載入**：在專案 `AGENTS.md` 寫總監段落後，開一個小探測子代理（cwd 指到專案），請它回報有沒有看到段落；看得到才算生效。
- **量用量**：`dsh_usage.py --since <建置日>` 看專案相關 session 的 tokens 與上下文壓力；GUI 對照看目前 session。
- **核對動作**：worker 交件後 `dsh_audit.py build`，再把 `RAN:` 的聲明用 `report_vs_audit.py` 對一次。
- **待決問題**：一次最多三題，每題給選項和建議；PO 在 GUI 回答，總監把原文寫進 `PO_PENDING.md` 再處理。
- **排程喚醒**：只有 PO 明確要求才建；建完用 `schedule_list` 記進 `GUARDS.md`。
- **確認 OpenSpec skill 有載入**：開一個小探測子代理（cwd 指到專案），請它列出看得到的 `openspec-*` skill；看得到 6 個才算生效。看不到時確認 `.agents/skills/` 在專案根目錄，或改用 `openspec init --tools dsh`。
- **確認 openspec 指令找得到**：`python -I -X utf8 <WS>/DIRECTOR/tools/sdd_gate.py --which --config <WS>/DIRECTOR/director_work.json`；印 `NOT_FOUND` 時照 `docs/13` 安裝並設定 `sdd.openspec_bin`。

## 已知限制（不要假裝有）

- 沒有 Claude 的 Artifact 私人頁面、置頂、留言叫醒；待決與選擇改成 `ask_user_question`＋`PO_PENDING.md`。
- 沒有 `interrupt_agent`、session 封存、讀別人的 context/用量工具；只能傳訊息、看列表、讀檔案與 session 紀錄。
- 子代理不能中途改模型或 effort；只能開接班人。
- 子代理預設全工具，不能 per-child 只給讀取；reviewer 限制靠指示與事後核對。
- 沒有 hooks，命令層級的自動阻擋做不到；只能靠沙箱模式、核准政策、工單範圍、事後 audit。
- 排程工具只給 PO 明確要求的用途，且只有總監（根 session）能用。
- 沒有容器 worker、沒有外掛專案級開關、沒有記憶索引檔。
- DSH 版本更新可能改工具名與 GUI 路徑；不確定時以工具說明與 `tools/dsh_doctor.py` 的結果為準。

## 為什麼

- Claude Desktop 版靠「開 session、SendMessage、list_sessions、get_usage、Artifact」；DSH 用子代理、send_message、list_agents、session 紀錄與 ask_user_question。能力對照寫下來，新總監不用自己摸索就不會誤判成做不到。
- DSH 沒有 hook 和權限詢問可依賴，所以安全規則從「工具會擋」改成「規則、PO 核准、沙箱模式、事後 audit」四層；寫清楚才不會讓 PO 以為有自動保護。
- 子代理的模型與 effort 開工就固定，把限制寫明才不會有人以為可以中途調；接班流程反而讓交接有紀錄。