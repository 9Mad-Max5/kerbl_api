import re

with open("main.js", encoding="utf8", errors="ignore") as f:
    data = f.read()

for match in sorted(set(re.findall(r'/api/v0\.1/[A-Za-z0-9_/\-]+', data))):
    print(match)