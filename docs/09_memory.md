# 09 記憶與指示檔

DSH 沒有 Claude 版的記憶索引（`MEMORY.md`）。會被自動載入的只有指示檔，其餘記憶都是普通檔案。

## 規則

1. **會被每輪載入的是指示檔**：專案 `AGENTS.md`（含 `AGENTS.local.md`，從 git 根一路到 session 的 cwd），加上使用者層 `~/.dsh/AGENTS.md`、`~/.agents/AGENTS.md`。沒有獨立記憶索引；不要建一個以為會被自動載入的索引。
2. **每條指示鏈上限 64 KiB**（專案鏈、使用者鏈各一條）。接近上限先整理；必讀內容被截斷等於規則沒載入。量法（2.3.0-ds.6，一條指令量整條鏈）：`python -I -X utf8 <WS>/DIRECTOR/tools/memory_size_check.py --chain <REPO>/AGENTS.md <REPO>/AGENTS.local.md --max-bytes 65536`：每個檔一行、加總、約略 token，超過 65536 印 FAIL；各檔之間重複 3 行以上的段落列成 `DUP` 行，照第 7 點合併成一行指標。鏈上還有別的檔（cwd 所在子資料夾的 `AGENTS.md`）一起列；沒有 `AGENTS.local.md` 就不列。使用者鏈另量一次（`~/.dsh/AGENTS.md`、`~/.agents/AGENTS.md`）。
3. **AGENTS.md 只放每次都要看到的東西**：總監段落、本專案特有規則、指向 `DIRECTOR/` 的指標。進度寫 `RESUME_STATE.md`，決策寫 `DECISION_REGISTER.md`，不把 AGENTS.md 當工作日誌。
4. **長期記憶放 `DIRECTOR/`**：決策登記、風險登記、工單、待決帳、`DIRECTOR_LOG`；結案與歷史移到封存區，主檔留一行指標。
5. **記憶檔本身不刪。** 只移動索引或主檔裡的條目。
6. **進行中的不能洗掉**：要等工單結案（`DIRECTOR_STATE` 或工單寫 CLOSED）才能移進封存。
7. **規則類條目永遠留著。** 重複的合併成一行，指向主要那一份。
8. **何時整理**：每週一次；`AGENTS.md` 接近 64 KiB 或大小檢查報錯時；新增大量條目之後。
9. **先備份**：整理前把整份檔案備份到 `DIRECTOR/SNAPSHOT/`（檔名帶日期）；整理後重量一次大小。
10. 使用者層指示檔是 PO 的，總監只讀不改；要整理先開待決題。

## 為什麼

- 指示檔是固定成本：每一輪、每個請求都會重讀，越長越貴。DSH 每條指示鏈 64 KiB，超過會先丟較廣的檔、最後截斷最具體的檔，等於規則悄悄失效。
- 原專案（Claude 版）的記憶索引每輪載入，一度 8.4k token，整理到 2.5k，記憶檔總計從 12.3k 降到約 6.5k，一個檔都沒刪；dshdw 沒有這個索引，固定成本只剩指示鏈。
- 進行中的條目一旦移走，恢復的 session 就看不到它，等於遺失進度。
- 規則類條目決定 session 的行為；移走它，同樣的錯就會再犯。
- 先備份，整理錯了可以還原。