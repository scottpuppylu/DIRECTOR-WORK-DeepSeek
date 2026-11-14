# 規格審查（派工前，subagent 用）

Strict 和 Standard 工單必做（ds.2 起 Standard 也要，開關 `sdd.spec_review_for_standard`），Direct 不做（`docs/02`、`docs/13`）。總監用 `subagent` 開一個新 context 的子代理（不要用 `subagent_fork`，它會繼承整段對話）；DSH 子代理預設拿到完整工具集，也不能只給 Read / Glob / Grep，所以限制靠下面的提示寫明「只讀不寫」，總監事後用 `dsh_audit.py` 核對（`docs/07`）。effort 照 `docs/05` 選，機械性審查用 `low`／`high`。把下面的提示填好貼給它。結果只給總監參考，怎麼改工單由總監決定。時機：工單寫好、派工之前，在同一輪跑完（DSH 上的限制見 `docs/11_dsh_operations.md`「開 worker 的限制」）；審完工單又改版，就重審。

```text
你是規格審查員，只讀不寫。審這張工單能不能直接開工：<工單路徑>
也審它的 OpenSpec 變更：<專案>/openspec/changes/<名稱>/（proposal.md、specs/**、design.md；tasks.md 這時還沒寫）
需要時可以讀：<既有決定的檔案，例如 DIRECTOR/DECISION_REGISTER.md>、<凍結基準或規格的路徑>
不要讀程式碼全文，不要提出實作方法，不要用任何寫檔工具（Write / Edit）。

逐條檢查 E 節每個 AC，再看整張工單：
1. 能不能被別人獨立判定：驗證方法和預期具體到另一個人照做會得到同樣結論嗎？
2. 類型對不對：要用眼睛看的條件是不是 REVIEW，而且寫明誰看、從哪個角度、看多大範圍？只有 PO 能判的是不是 PO？
3. 條件之間、條件和 SCOPE / FORBIDDEN 之間有沒有矛盾。
4. 有沒有違反既有決定或凍結基準（指出是哪一條）。
5. 有畫面或成品的工作：有沒有問到「整個成品放在一起看，說得通嗎」，而不是只看被點名的部位？
6. 缺了什麼條件，做完會被 PO 一眼退回？
7. 規格（specs 的每個 Scenario）和工單驗收條件對得上嗎？有沒有 Scenario 沒有測試、或驗收條件在規格裡找不到？
8. TESTS_LOCKED 的測試真的測到 Scenario 說的行為嗎（讀測試檔，只看它斷言了什麼）？
9. 這張工單夠小嗎：預計 ≤3 個檔、約 200 行？太大就建議怎麼拆。

輸出，總長不超過 40 行：
- 每個問題一行：AC-x 或「整體」｜問題｜建議改法｜嚴重度 P0 / P1 / P2
- 沒有問題就寫 NO_ISSUES
- 最後一行：讀了哪些檔案
```

## 總監收到結果後

1. 決定改或不改工單，改了就 `REVISION` 加 1、記變更紀錄。
2. 在 `DIRECTOR_LOG` 記一行（整行，`gate_check.py --match --dispatch-log` 會找它）：`SPEC_REVIEW WO-<編號> tokens=<數字> issues=<P0/P1/P2 各幾個> adopted=<採用幾個>`；tokens 用 `tools/dsh_usage.py` 看該子代理 session 的用量，分不出來或讀不到就記 UNKNOWN。
3. 之後這張工單如果返工，查一下規格審查有沒有提過；用這些紀錄決定 Standard 要不要繼續做（`docs/02`）。
