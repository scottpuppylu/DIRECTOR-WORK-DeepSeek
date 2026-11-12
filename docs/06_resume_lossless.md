# 06 無損續航

目標：自動壓縮、錯誤、當機、重開機、關掉 DSH、PO 手動停止之後，每條工作線都從最後一個已驗證的 checkpoint 接著做，不重做已完成的事，也不沿用半成品。

## 規則

### RESUME_STATE.md

- 每條工作線在自己的工作資料夾根目錄維護一份（`templates/RESUME_STATE.md`），路徑登記在 `ACTIVE_WORKSTREAMS.md`。
- **頂部固定四行** `PROGRESS / DOING / NEXT_STEP / COMMS`，只看這四行就要能接手。其餘欄位照範本逐欄寫齊，沒有就寫 NONE；IN_FLIGHT 列背景 job id（`job_list`）、等誰、排程 id。
- **何時更新**：每個 checkpoint commit 之後、送 TEST REQUEST 之前、背景程序啟動和結束時、收到總監決定時。DSH 自動壓縮前後都一樣：一有進度就寫 RESUME_STATE，寫完才做下一步。
- `UPDATED` 時間一律讀系統時鐘（`date`），不估計。
- 寫完用 `tools/gate_check.py --resume <檔案>` 檢查格式；內容對不對要靠 `LAST_VERIFIED_CHECKPOINT` 和 repo 核對。
- 平常就要做，不是快停才做：有成果就 commit。進度不能只留在對話裡。

### 恢復

任何 session 被打斷後（包括 PO 手動停止後再繼續），第一件事照 `docs/06b` 的恢復程序做。中斷的擷取、量測、打包、匯入一律重做，不沿用。
worker 是子代理：總監用 `list_agents()` 找回、`send_message` 叫醒，子代理名稱登記在 `ACTIVE_WORKSTREAMS.md`。

### 每輪第一步

總監每次喚醒、壓縮或恢復後只有一個第一步：先唯讀跑檢查腳本、收集輸入（含待決帳與 `ask_user_question` 的回覆），再處理待決帳。見 `docs/06b`。

### 機制與喚醒

每個排程和防護機制都要能重建（`DIRECTOR/GUARDS.md`）。建立或修改機制、設定喚醒時，讀 `docs/06b`；DSH 沒有額度重置喚醒，排程喚醒只有 PO 明確要求才建。

## 為什麼

- 其他理由見 docs/10。