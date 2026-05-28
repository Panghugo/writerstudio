import os
import sys


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from writer_studio.renderer import auto_format_text


CASES = {
    "这是一个**test**测试。": "这是一个 **test** 测试。",
    "测试“引号”测试": "测试「引号」测试",
    "“中文”": "「中文」",
    "我爱Apple。": "我爱 Apple。",
    "Apple我爱。": "Apple 我爱。",
    "测试`code`测试。": "测试 `code` 测试。",
    "测试_test_测试。": "测试 _test_ 测试。",
    "测试123测试。": "测试 123 测试。",
}


def run_check():
    failures = []
    for source, expected in CASES.items():
        actual = auto_format_text(source)
        if actual != expected:
            failures.append((source, expected, actual))

    if failures:
        details = "\n".join(
            f"- {source!r}\n  expected: {expected!r}\n  actual:   {actual!r}"
            for source, expected, actual in failures
        )
        raise AssertionError(f"Text formatting check failed:\n{details}")

    print("text-formatting-ok")


if __name__ == "__main__":
    run_check()
