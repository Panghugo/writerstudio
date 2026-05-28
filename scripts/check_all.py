import os
import subprocess
import sys


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = sys.executable


CHECKS = [
    [
        PYTHON,
        "-m",
        "compileall",
        "-q",
        "app.py",
        "web.py",
        "publisher.py",
        "writer_studio",
        "scripts",
    ],
    [PYTHON, "scripts/smoke_test.py"],
    [PYTHON, "scripts/check_text_formatting.py"],
    [PYTHON, "scripts/check_publisher_offline.py"],
]


def run_check(command):
    label = " ".join(command)
    print(f"\n==> {label}")
    subprocess.run(command, cwd=ROOT_DIR, check=True)


def main():
    for command in CHECKS:
        run_check(command)
    print("\nall-checks-ok")


if __name__ == "__main__":
    main()
