# 會考複習講義庫

給國中生複習會考的互動講義網站。每篇講義都依照同一份規則（[CLAUDE.md](./CLAUDE.md)）製作：先讀懂原文、再整理字詞、最後馬上練習並看詳解。

- 網站：https://chloe-0607.github.io/huikao-lessons/
- 目前收錄：〈愛蓮說〉、〈陋室銘〉（國中八年級古文）

## 這個專案怎麼運作

| 檔案 | 用途 |
|---|---|
| `CLAUDE.md` | AI 的工作手冊：成品長什麼樣、哪些能動、怎樣算做完 |
| `AGENTS.md` | 給其他 AI 工具的入口，指回 CLAUDE.md |
| `templates/guwen.html` | 古文講義模板：共用引擎＋本篇資料區 |
| `lessons/<slug>/index.html` | 每篇講義，單一檔案可離線開啟 |
| `ideas/<slug>.md` | 每篇的備課筆記：來源、事實核對、題目規劃 |
| `tools/check.py` | 檢查題數、注釋、登記表；`--sync` 同步模板與首頁 |

## 新增一篇講義

對 AI 說：

> 請先讀 CLAUDE.md，再製作〈篇名〉講義。

AI 會依序寫備課筆記、複製模板填資料、執行 `python3 tools/check.py --sync`、做桌機與手機驗收。

## 自己檢查

```bash
python3 tools/check.py          # 只檢查
python3 tools/check.py --sync   # 同步模板到每篇講義並更新首頁，再檢查
```

只用 Python 內建模組，不需要安裝任何套件。

---

製作：Chloe｜生成式 AI 課程第 9 週作業（建立自己的 AGENTS.md／CLAUDE.md）。內容以學生使用的課本為準。
