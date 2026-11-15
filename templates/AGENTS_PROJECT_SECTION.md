<!-- 貼在專案 AGENTS.md 最上方。把 <...> 換掉後刪除本行。 -->
## 總監制（Director mode）

本專案用總監制開發，規則包：https://github.com/scottpuppylu/dsh-DIRECTOR-WORKER（本機：<RULES>）。本專案的規則和 PO 指示永遠優先於規則包。

- **總監**：DSH 根 session（代理名 `lead`），是 PO 的代理人。Worker 是總監用 `subagent` 開的具名子代理，接總監的工單（`<DIRECTOR>/orders/WO-*.md`），在 gate 完成、卡住、需要決定時，用 `send_message` 送一則完整的 TASK REPORT 給總監（`<RULES>/templates/TASK_REPORT.md`）。只有總監說可以時才直接找 PO；子代理不能直接問 PO。
- **狀態寫檔**：每條工作線在自己的工作資料夾維護 `RESUME_STATE.md`，頂部四行 PROGRESS / DOING / NEXT_STEP / COMMS，每個 checkpoint 更新。DSH 自動壓縮或任何中斷後，先跑一次 `python -I -X utf8 <RULES>/tools/resume_inject.py --file <自己的 RESUME_STATE.md>`（印表頭四行和未結段，最多 2 KB），再照 `<RULES>/docs/06b_on_demand_procedures.md` 的恢復程序做。
- **訊息**：用 `send_message`，只在 gate 報告、需要決定、要對方立刻改行動時發；不回 ACK；給同一人的內容一次發完。
- **要 PO 回覆的事**：先報總監（標題 `PO_REPLY_NEEDED`），由總監記進待決帳（`<DIRECTOR>/PO_PENDING.md`）並用 `ask_user_question` 問 PO。
- **上下文短**：長輸出寫檔、只看結論；大量閱讀和看圖交給 `off`／`low` 的子代理；DSH 會自動壓縮，一有進度就更新 `RESUME_STATE`，不為了縮上下文換 session。DSH 沒有專案級設定，新目錄或新 session 都不用跑專案設定工具。
- **安全閘門**（docs/13）：Standard／Strict 工單要有鎖定測試、計畫核准（`PLAN_APPROVED`）、規格審查；`director_work.json` 的 `safety` 開關不得自行關閉，要關先寫 PO_PENDING 等 PO 回答。
- **收尾**（2.2.5-ds.5）：時間不得手填（報告、裁決、DIRECTOR_LOG 的時間由工具產生）；報告的 `WORKTREE:` 行由 `dsh_session.py --worktree-status` 或 `gate_check.py --report-skeleton` 產生；最後一步跑 `dsh_usage.py --project-dir <WS> --out <WS>/DIRECTOR/usage.json`，再跑 `gate_check.py --final <WS>/DIRECTOR`（BOOTSTRAP「收尾」）。
- **品質**：工程狀態和成品狀態分開回報；數字不能代替看成品（<本專案的成品怎麼看>）；成品交件附常識閘門表；每個缺陷最多 3 輪假設驅動修正；不破壞已通過的基準；最終驗收屬 PO，絕不自稱通過。
- **安全**：push、公開、刪除、付費、帳號、使用者層設定都要 PO 核准；不 force push、不 `reset --hard`、不 `git clean`、不用裸 `git stash`；不批次刪證據；只停自己的 job；測試輸出寫到 <輸出位置>，不寫進 repo。DSH 沒有 hook 自動阻擋，防護靠沙箱模式、核准、工單範圍與事後 audit。
- **語言**：所有回報用 <繁體中文>；程式碼、檔名、commit 訊息、識別字可用英文。
- **時間**：時間戳一律讀系統時鐘。