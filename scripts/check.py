import json
from pathlib import Path
from urllib.parse import urlparse
root = Path(__file__).resolve().parents[1] / 'site'
data = json.loads((root/'data.json').read_text())
sources = {s['id']: s for s in data['sources']}
assert len(sources) == len(data['sources'])
for s in sources.values():
    assert urlparse(s['url']).scheme == 'https' and urlparse(s['url']).netloc
for category in ('strategies', 'gates', 'flags'):
    for row in data[category]:
        assert row['source'] in sources, (category, row)
for name in ('index','sources','strategies','validation','flags'):
    html = (root/f'{name}.html').read_text()
    assert 'app.js' in html and 'style.css' in html
for resource in ('app.js','style.css'):
    assert (root/resource).is_file()
print('PASS: source references, URLs, pages and assets are structurally valid (not remote-link availability).')
