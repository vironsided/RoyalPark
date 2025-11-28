from pathlib import Path

text = Path('public/admin/content_css/tenants.css').read_text()
count = 0
for idx, ch in enumerate(text, 1):
    if ch == '{':
        count += 1
    elif ch == '}':
        count -= 1
    if count < 0:
        print('extra closing before char', idx)
        break
else:
    print('balance', count)