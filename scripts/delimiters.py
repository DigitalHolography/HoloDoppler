from PIL import Image, ImageDraw
from pathlib import Path

SUB_APS_Y, SUB_APS_X = 5, 5
THICKNESS, COLOR = 4, "black"

path = Path(r"C:\Users\Ivashka\Downloads\260717_AUZ.png")
img = Image.open(path).convert("RGB")
w, h = img.size

rw = (w - THICKNESS * (SUB_APS_X - 1)) // SUB_APS_X
rh = (h - THICKNESS * (SUB_APS_Y - 1)) // SUB_APS_Y

draw = ImageDraw.Draw(img)

for x in range(1, SUB_APS_X):
    x0 = x * rw + (x - 1) * THICKNESS
    draw.rectangle([x0, 0, x0 + THICKNESS - 1, h - 1], fill=COLOR)

for y in range(1, SUB_APS_Y):
    y0 = y * rh + (y - 1) * THICKNESS
    draw.rectangle([0, y0, w - 1, y0 + THICKNESS - 1], fill=COLOR)

output = path.with_name(f"{path.stem}_modified{path.suffix}")
img.save(output)
print(output)