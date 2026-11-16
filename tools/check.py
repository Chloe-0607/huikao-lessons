#!/usr/bin/env python3
"""會考複習講義庫｜檢查與同步工具（只用 Python 內建模組，不需安裝任何套件）

用法（在專案根目錄執行）：
  python3 tools/check.py          只檢查，不改檔案
  python3 tools/check.py --sync   先用 templates/ 的共用引擎更新每篇講義，
                                  再依各篇資料重寫首頁登記表，最後檢查

檢查項目：
  1. 每篇講義的資料區能解析成 JSON，必填欄位齊全，slug 和資料夾同名
  2. 共用引擎區塊和模板一致（不一致代表有人改了單篇的引擎）
  3. 測驗剛好 10 題、每題 4 個選項、答案編號有效、id 不重複、有詳解
  4. 原文中每個 [注釋] 都有對應的 notes 內容
  5. 探索段格式正確；related 指到存在的講義
  6. 首頁登記表和各篇資料一致
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
LESSONS = ROOT / 'lessons'
INDEX = ROOT / 'index.html'

DATA_RE = re.compile(r'(<!-- ===== LESSON DATA START.*?-->)(.*?)(<!-- ===== LESSON DATA END ===== -->)', re.S)
JSON_RE = re.compile(r'<script type="application/json" id="lesson-data">(.*?)</script>', re.S)
REG_RE = re.compile(r'(<script type="application/json" id="registry">)(.*?)(</script>)', re.S)
TITLE_RE = re.compile(r'<title>.*?</title>', re.S)
BLOCK_RE = {
    'style': re.compile(r'<!-- ===== ENGINE:STYLE START.*?<!-- ===== ENGINE:STYLE END ===== -->', re.S),
    'script': re.compile(r'<!-- ===== ENGINE:SCRIPT START.*?<!-- ===== ENGINE:SCRIPT END ===== -->', re.S),
}
REQUIRED = ['slug', 'type', 'subject', 'title', 'author', 'grade', 'textbook', 'palette', 'lead',
            'card', 'background', 'text', 'words', 'quiz', 'footer']
QUIZ_TYPES = {'choice', 'cloze'}
EXPLORE_TYPES = {'match', 'classify'}

errors, warns = [], []

def err(where, msg): errors.append(f'✗ {where}：{msg}')
def warn(where, msg): warns.append(f'△ {where}：{msg}')

def plain(s): return re.sub(r'\{([^:{}]+):[^{}]+\}', r'\1', s)

def load(path):
    html = path.read_text(encoding='utf-8')
    m = JSON_RE.search(html)
    if not m:
        err(path.parent.name, '找不到 <script id="lesson-data"> 資料區')
        return html, None
    try:
        return html, json.loads(m.group(1))
    except json.JSONDecodeError as e:
        err(path.parent.name, f'資料區不是合法 JSON（第 {e.lineno} 行附近）：{e.msg}')
        return html, None

def sync_lesson(path, data_html):
    """用模板重新包住這篇的資料區，保留資料、更新引擎。"""
    html = path.read_text(encoding='utf-8')
    m = DATA_RE.search(html)
    d = json.loads(JSON_RE.search(html).group(1))
    tpl = (ROOT / 'templates' / f"{d['type']}.html").read_text(encoding='utf-8')
    out = DATA_RE.sub(lambda _: m.group(0), tpl, count=1)
    out = TITLE_RE.sub(f"<title>{d['title']}｜互動國文講義</title>", out, count=1)
    if out != html:
        path.write_text(out, encoding='utf-8')
        print(f'↻ 已同步引擎：lessons/{path.parent.name}/index.html')

def check_lesson(path, d, html, slugs):
    w = f'lessons/{path.parent.name}'
    for k in REQUIRED:
        if k not in d: err(w, f'缺少欄位 {k}')
    if d.get('slug') != path.parent.name: err(w, f'slug「{d.get("slug")}」要和資料夾名稱相同')
    tpl_path = ROOT / 'templates' / f"{d.get('type')}.html"
    if not tpl_path.exists():
        err(w, f'type「{d.get("type")}」沒有對應模板 templates/{d.get("type")}.html')
    else:
        tpl = tpl_path.read_text(encoding='utf-8')
        for name, rx in BLOCK_RE.items():
            a, b = rx.search(html), rx.search(tpl)
            if not a: err(w, f'找不到共用引擎區塊 ENGINE:{name.upper()}')
            elif a.group(0) != b.group(0): err(w, f'共用引擎 ENGINE:{name.upper()} 和模板不同，請改模板後執行 --sync，不要改單篇')
    for k in ('main', 'deep', 'soft', 'gold'):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', str(d.get('palette', {}).get(k, ''))): err(w, f'palette.{k} 要是 #RRGGBB 色碼')
    lead = d.get('lead', '')
    if not 60 <= len(lead) <= 140: warn(w, f'導言 {len(lead)} 字，建議 80–120 字')
    # 課文與注釋
    for pi, p in enumerate(d.get('text', {}).get('paragraphs', []), 1):
        notes = p.get('notes', {})
        used = set()
        for s in p.get('sentences', []):
            if not s.get('tr'): err(w, f'第 {pi} 段有句子沒有語譯')
            for term in re.findall(r'\[([^\]]+)\]', s.get('src', '')):
                key = plain(term); used.add(key)
                if key not in notes: err(w, f'第 {pi} 段注釋「{key}」沒有寫在 notes')
        for key in notes:
            if key not in used: warn(w, f'第 {pi} 段 notes 有「{key}」但原文沒有標 [{key}]')
    # 測驗
    items = d.get('quiz', {}).get('items', [])
    if len(items) != 10: err(w, f'測驗要 10 題，目前 {len(items)} 題')
    ids = [it.get('id') for it in items]
    if len(set(ids)) != len(ids): err(w, '測驗題 id 有重複')
    for it in items:
        q = f"題目 {it.get('id')}"
        if it.get('type') not in QUIZ_TYPES: err(w, f'{q} type 只能是 choice 或 cloze')
        if len(it.get('options', [])) != 4: err(w, f'{q} 要剛好 4 個選項')
        if not isinstance(it.get('answer'), int) or not 0 <= it['answer'] < len(it.get('options', [])): err(w, f'{q} answer 編號無效')
        if len(set(it.get('options', []))) != len(it.get('options', [])): err(w, f'{q} 選項重複')
        if not it.get('explain'): err(w, f'{q} 缺少詳解')
        if not it.get('tag'): err(w, f'{q} 缺少題型標籤 tag')
        if it.get('type') == 'cloze' and '＿＿' not in it.get('q', ''): err(w, f'{q} 克漏字題的題幹要有「＿＿」')
    # 探索
    x = d.get('explore')
    if x:
        if x.get('type') not in EXPLORE_TYPES: err(w, f'explore.type 只能是 {"、".join(sorted(EXPLORE_TYPES))}')
        if x.get('type') == 'match' and len(x.get('pairs', [])) < 4: err(w, '連連看至少 4 組')
        if x.get('type') == 'classify':
            n = len(x.get('categories', []))
            for it in x.get('items', []):
                if not 0 <= it.get('cat', -1) < n: err(w, f'分類項目「{it.get("text")}」的 cat 編號無效')
    for r in d.get('related', []):
        if r.get('slug') not in slugs: err(w, f'related 指到不存在的講義 {r.get("slug")}')

def registry_entries(datas):
    rows = []
    for d in datas:
        c = d.get('card', {})
        rows.append({'slug': d['slug'], 'path': f"lessons/{d['slug']}/", 'subject': d['subject'],
                     'title': d['title'], 'dynasty': d.get('dynasty', ''), 'author': d['author'],
                     'grade': d['grade'], 'desc': c.get('desc', ''), 'modes': c.get('modes', []),
                     'color': d.get('palette', {}).get('main', ''), 'order': c.get('order', 999)})
    rows.sort(key=lambda r: (r['order'], r['slug']))
    return rows

def main():
    sync = '--sync' in sys.argv
    paths = sorted(LESSONS.glob('*/index.html'))
    if sync:
        for p in paths: sync_lesson(p, None)
    loaded = [(p,) + load(p) for p in paths]
    slugs = {p.parent.name for p in paths}
    datas = []
    for p, html, d in loaded:
        if d is None: continue
        check_lesson(p, d, html, slugs); datas.append(d)
    # 首頁登記表
    idx = INDEX.read_text(encoding='utf-8')
    m = REG_RE.search(idx)
    want = registry_entries(datas)
    if not m: err('index.html', '找不到 <script id="registry"> 登記表')
    else:
        have = json.loads(m.group(2) or '[]')
        if have != want:
            if sync:
                body = '\n' + json.dumps(want, ensure_ascii=False, indent=2) + '\n'
                INDEX.write_text(REG_RE.sub(lambda mm: mm.group(1) + body + mm.group(3), idx, count=1), encoding='utf-8')
                print('↻ 已依各篇資料重寫首頁登記表')
            else:
                err('index.html', '首頁登記表和講義資料不一致，請執行 python3 tools/check.py --sync')
    print(f'\n檢查 {len(paths)} 篇講義')
    for line in warns: print(line)
    for line in errors: print(line)
    if errors:
        print(f'\n未通過：{len(errors)} 個錯誤、{len(warns)} 個提醒'); sys.exit(1)
    print(f'通過：0 個錯誤、{len(warns)} 個提醒')

if __name__ == '__main__':
    main()
