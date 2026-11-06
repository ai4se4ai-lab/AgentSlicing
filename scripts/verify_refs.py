"""Verify candidate references against Crossref and arXiv; write a verification table.

Each candidate: key, title, first-author surname, year, source ('crossref'|'arxiv'|'both').
A reference is accepted only if a record with a near-identical title (similarity >= 0.9)
and the expected first author is found. Output: docs/TSE/refs_verification.json/.csv.
"""
from __future__ import annotations

import csv
import difflib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {'User-Agent': 'slicing-artifact-reference-check/1.0'}


def norm(s):
    return re.sub(r'[^a-z0-9 ]', '', re.sub(r'\s+', ' ', s.lower())).strip()


def sim(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.read()
        except Exception as e:      # noqa: BLE001
            err = e
            time.sleep(2 * (i + 1))
    raise err


def crossref(title, author):
    q = urllib.parse.urlencode({'query.bibliographic': title, 'query.author': author, 'rows': 5})
    items = json.loads(get('https://api.crossref.org/works?' + q))['message']['items']
    best = None
    for it in items:
        t = (it.get('title') or [''])[0]
        s = sim(t, title)
        if best is None or s > best[0]:
            best = (s, it)
    if not best:
        return None
    s, it = best
    auth = [f"{a.get('family', '')}, {a.get('given', '')}".strip(', ') for a in it.get('author', [])]
    year = (it.get('issued', {}).get('date-parts') or [[None]])[0][0]
    return {'sim': round(s, 3), 'title': (it.get('title') or [''])[0], 'authors': auth, 'year': year,
            'venue': (it.get('container-title') or [''])[0], 'doi': it.get('DOI'), 'type': it.get('type'),
            'publisher': it.get('publisher'), 'volume': it.get('volume'), 'issue': it.get('issue'), 'pages': it.get('page')}


def arxiv(title):
    q = urllib.parse.urlencode({'search_query': f'ti:"{title}"', 'max_results': 5})
    root = ET.fromstring(get('http://export.arxiv.org/api/query?' + q))
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    best = None
    for e in root.findall('a:entry', ns):
        t = ' '.join(e.find('a:title', ns).text.split())
        s = sim(t, title)
        if best is None or s > best[0]:
            auth = [a.find('a:name', ns).text for a in e.findall('a:author', ns)]
            aid = e.find('a:id', ns).text.rsplit('/', 1)[-1]
            best = (s, {'sim': round(s, 3), 'title': t, 'authors': auth, 'year': int(e.find('a:published', ns).text[:4]),
                        'arxiv': re.sub(r'v\d+$', '', aid)})
    return best[1] if best else None


def main(path):
    cands = json.loads(Path(path).read_text(encoding='utf-8'))
    out = []
    for c in cands:
        rec = {'key': c['key'], 'title': c['title'], 'author': c['author'], 'year': c['year']}
        for src in ([c['src']] if c['src'] != 'both' else ['crossref', 'arxiv']):
            try:
                r = crossref(c['title'], c['author']) if src == 'crossref' else arxiv(c['title'])
            except Exception as e:  # noqa: BLE001
                r = {'error': str(e)}
            rec[src] = r
            time.sleep(1.0 if src == 'crossref' else 3.0)
        def ok(r):
            return bool(r) and r.get('sim', 0) >= 0.9 and any(norm(c['author']) in norm(a) for a in r.get('authors', []))
        rec['verified'] = any(ok(rec.get(s)) for s in ('crossref', 'arxiv'))
        out.append(rec)
        print(c['key'], rec['verified'], {s: (rec[s] or {}).get('sim') for s in ('crossref', 'arxiv') if s in rec}, flush=True)
    dst = ROOT / 'docs/TSE/refs_verification.json'
    dst.write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    with open(ROOT / 'docs/TSE/refs_verification.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['key', 'verified', 'title', 'crossref_doi', 'crossref_venue', 'crossref_year', 'arxiv_id'])
        for r in out:
            cr, ax = r.get('crossref') or {}, r.get('arxiv') or {}
            w.writerow([r['key'], r['verified'], r['title'], cr.get('doi', ''), cr.get('venue', ''), cr.get('year', ''), ax.get('arxiv', '')])


if __name__ == '__main__':
    main(sys.argv[1])
