import os
import getpass

print("User:", getpass.getuser())
print("PID:", os.getpid())
print("CWD:", os.getcwd())

from pathlib import Path

p = Path(r"D:\\za\\260429_zzz\\hello.txt")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text("test")
print(p.resolve())