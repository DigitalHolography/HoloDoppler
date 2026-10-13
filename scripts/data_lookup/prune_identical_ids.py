import re

with open(r"C:\Users\Domodekavkaz\Downloads\list_controles_holo.txt") as f:
    files = f.read().splitlines()

seen = set()
out = []

for path in files:
    name = path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
    m = re.match(r"\d+_(.+?)(?:_\d+)?\.holo$", name)

    if m:
        tag = m.group(1)
        if tag not in seen:
            seen.add(tag)
            out.append(path)

with open(r"C:\Users\Domodekavkaz\Downloads\list_controles_holo2.txt", "w+") as f:
    f.write("\n".join(out))