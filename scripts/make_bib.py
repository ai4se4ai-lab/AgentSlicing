"""Build docs/TSE/references.bib from verified records only (refs_verification.json)."""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
recs = json.loads((ROOT/'docs/TSE/refs_verification.json').read_text(encoding='utf-8'))
# manually confirmed by DOI lookup / web search (logged in refs_manual.json)
manual = json.loads((ROOT/'docs/TSE/refs_manual.json').read_text(encoding='utf-8'))
DROP = {'tip1995survey', 'vesely1981fault'}
def esc(s):
    s = s.replace('&', r'\&').replace('_', r'\_').replace('%', r'\%')
    return re.sub(r'([A-Z]{2,}[a-z]*|[A-Z][a-z]*[A-Z]\w*)', r'{\1}', s)
def authors(lst):
    out = []
    for a in lst:
        out.append(a if ',' in a else (a.rsplit(' ', 1)[1] + ', ' + a.rsplit(' ', 1)[0] if ' ' in a else a))
    return ' and '.join(out)
TYPES = {'journal-article': 'article', 'proceedings-article': 'inproceedings', 'book': 'book', 'monograph': 'book',
         'book-chapter': 'incollection', 'posted-content': 'misc'}
out = []
for r in recs:
    k = r['key']
    if k in DROP: continue
    if k in manual: out.append(manual[k]); continue
    cr, ax = r.get('crossref') or {}, r.get('arxiv') or {}
    good = lambda x: x and x.get('sim', 0) >= 0.9
    if good(cr) and cr.get('type') != 'posted-content':
        t = TYPES.get(cr.get('type'), 'misc')
        f = {'title': '{' + esc(cr['title']) + '}', 'author': authors(cr['authors']), 'year': cr['year']}
        if t == 'article': f['journal'] = cr['venue']
        elif t in ('inproceedings', 'incollection'): f['booktitle'] = cr['venue']
        elif t == 'book': f['publisher'] = cr.get('publisher', '')
        for x in ('volume', 'pages'):
            v = cr.get('issue' if False else x if x != 'pages' else 'pages')
            if v: f[x] = str(v).replace('-', '--')
        if cr.get('issue'): f['number'] = cr['issue']
        f['doi'] = cr['doi']
    elif good(ax):
        t = 'misc'
        f = {'title': '{' + esc(ax['title']) + '}', 'author': authors(ax['authors']), 'year': ax['year'],
             'howpublished': f'arXiv:{ax["arxiv"]}', 'url': f'https://arxiv.org/abs/{ax["arxiv"]}'}
    else:
        raise SystemExit('unverified: ' + k)
    body = ',\n'.join(f'  {a} = {{{v}}}' if a != 'title' else f'  {a} = {v}' for a, v in f.items() if v not in (None, ''))
    out.append(f'@{t}{{{k},\n{body}\n}}')
(ROOT/'docs/TSE/references.bib').write_text('\n\n'.join(out) + '\n', encoding='utf-8')
print(len(out), 'entries')
