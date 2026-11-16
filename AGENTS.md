# AGENTS.md

這個專案（會考複習講義庫）的完整規則寫在 **[CLAUDE.md](./CLAUDE.md)**。
不論你是 Claude、Codex 或其他 AI 工具，**開工前請先完整讀完 CLAUDE.md**，再依照裡面的流程工作。

最重要的五件事（細節以 CLAUDE.md 為準）：

1. 每篇講義是 `lessons/<slug>/index.html` 單一檔案，從 `templates/guwen.html` 複製，**只改 LESSON DATA 區塊**。
2. 新增講義先寫 `ideas/<slug>.md` 備課筆記，原文與事實都要有來源，查不到就標「資料需再確認」。
3. 測驗剛好 10 題、每題 4 個選項並附詳解；探索段的互動模式不可和上一篇相同（看 CLAUDE.md §12）。
4. 改完一定執行 `python3 tools/check.py --sync`，顯示「通過：0 個錯誤」才算過。
5. 不加框架、套件或建置流程；不改單篇的 ENGINE 區塊；不手改首頁登記表。
