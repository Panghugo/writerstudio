import os
import shutil
import subprocess
import sys
from pathlib import Path


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
    [PYTHON, "scripts/check_web_services_offline.py"],
    [PYTHON, "scripts/check_text_formatting.py"],
    [PYTHON, "scripts/check_publisher_offline.py"],
    [PYTHON, "scripts/check_pipeline_offline.py"],
    [PYTHON, "scripts/check_renderer_offline.py"],
    [PYTHON, "scripts/check_wechat_client_offline.py"],
]


def js_files():
    return sorted(Path(ROOT_DIR, "static", "js").glob("*.js"))


def run_check(command):
    label = " ".join(command)
    print(f"\n==> {label}")
    subprocess.run(command, cwd=ROOT_DIR, check=True)


def run_js_checks():
    node = shutil.which("node")
    if not node:
        print("\n==> node --check static/js/*.js")
        print("js-check-skipped: node not found")
        return

    files = js_files()
    if not files:
        print("\n==> node --check static/js/*.js")
        print("js-check-skipped: no JavaScript files found")
        return

    print("\n==> node --check static/js/*.js")
    for path in files:
        subprocess.run([node, "--check", str(path.relative_to(ROOT_DIR))], cwd=ROOT_DIR, check=True)


def main():
    for command in CHECKS:
        run_check(command)
    run_js_checks()
    print("\nall-checks-ok")


if __name__ == "__main__":
    main()
