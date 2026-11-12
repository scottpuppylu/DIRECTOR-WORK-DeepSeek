<!-- PO 待決帳（docs/03）。新項目加在「未關閉」最上面；關閉後移到「已關閉」。 -->
# PO 待決帳 — <專案名稱>
UPDATED: <YYYY-MM-DD HH:MM ±TZ，讀 date>
回覆方式：總監用 `ask_user_question` 問（GUI 跳出選項，可自訂答案），PO 在對話回答；也可以直接在聊天回「OD-01：A」。本檔是唯一的長期紀錄：總監每一輪先讀這頁和聊天裡還沒處理的回答（`docs/03`），答案原文貼回 `ANSWER`。DSH 沒有待決頁網頁、沒有置頂、沒有留言叫醒。
<!-- 「初衷卡確認 + 授權開工」那一項（docs/12 第三節第 6 點）另外記：CARD_REV（卡版次）、ORDER / ORDER_REV / ORDER_SHA256（首批工單、版次、雜湊）、LANES（開幾位子代理、effort）、SCOPE（動哪些檔、哪份工作副本）、COST（DeepSeek Harness 帳號用量；時間標「估計」）。回覆後依 LOCK_ONLY / NO_START / LOCK_AND_USER_ASKED 處理，兩個決定分開登記。 -->

## 未關閉

ID: OD-01（要 PO 決定）或 ACT-01（要 PO 動手）
CREATED: <YYYY-MM-DD HH:MM，讀 date>
STATUS: open | answered | closed
QUESTION: <一句話>
QUESTION_TOOL: <用 ask_user_question 問的題號或一句話；只在聊天問的寫 NONE>
OPTIONS: <A / B / C，各一句影響>
RECOMMENDED: <總監建議與一句理由>
IMAGES: <要 PO 看畫面判斷時附圖路徑，同一視角的前後對照放一起並標明方案；沒有寫 NONE>
SOURCE: <回覆從哪來：ask_user_question / 聊天；沒有回覆寫 NONE>
ANSWER: <PO 填，或總監把回覆原文貼上>
RESOLUTION: <總監處理結果、時間>

## 待預覽（看過真實畫面才選；不發待答、不編 B 號）

- <配色／字型／版面…>：<要等什麼畫面（至少兩種真實畫面）>

## 已關閉
