import subprocess
import sys

commands = [
    [sys.executable, "source/SAT/z3_SAT.py"],
    [sys.executable, "source/MIP/MIP.py"],
    [sys.executable, "source/CP/runCP_solvers.py"],
]

for cmd in commands:
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

print("All tasks completed!")
