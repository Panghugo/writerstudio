import os
import sys


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from writer_studio.typography import auto_format_text, meaningful_length, wrap_text_by_width


class FakeFont:
    def getlength(self, text):
        return len(text) * 10


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

    wrapped = wrap_text_by_width("梁泽祖把车停下，打开 OPPO 手机。", FakeFont(), 110)
    if any(line.startswith(("，", "。", "！", "？", "；", "：", "、")) for line in wrapped):
        raise AssertionError(f"closing punctuation should not start a line: {wrapped}")
    if "OPPO" not in "".join(wrapped):
        raise AssertionError(f"OPPO should remain intact: {wrapped}")

    quoted = wrap_text_by_width("「这是一个重要判断」。", FakeFont(), 70)
    if not any(line.startswith("「") for line in quoted):
        raise AssertionError(f"opening quote may stand at line start: {quoted}")

    short_line = wrap_text_by_width("2025 年的一个工作日下午一点多。", FakeFont(), 125)
    if meaningful_length(short_line[-1]) < 3:
        raise AssertionError(f"last line should have at least 3 meaningful chars: {short_line}")

    print("text-formatting-ok")


if __name__ == "__main__":
    run_check()
