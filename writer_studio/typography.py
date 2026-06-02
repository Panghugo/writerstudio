import re


def auto_format_text(text):
    text = re.sub(r'["“”]([^"“”]*)["“”]', r'「\1」', text)
    text = text.replace('“', '「').replace('”', '」')
    text = text.replace('‘', '『').replace('’', '』')
    text = re.sub(r'([\u4e00-\u9fa5])([*_\`]*[A-Za-z0-9])', r'\1 \2', text)
    text = re.sub(r'([A-Za-z0-9][*_\`]*)([\u4e00-\u9fa5])', r'\1 \2', text)
    return text


def strip_markers(text):
    return text.replace('\x01', '')


def wrap_text_by_width(text, font, max_width):
    tokens = tokenize_wrap_text(text)
    lines = []
    current = ""
    for token in tokens:
        if token.isspace() and not current:
            continue
        candidate = current + token
        if current and font.getlength(strip_markers(candidate)) > max_width:
            lines.append(current.rstrip())
            current = token.lstrip()
        else:
            current = candidate
    if current:
        lines.append(current.rstrip())
    return refine_wrapped_lines(lines, font, max_width)


def tokenize_wrap_text(text):
    pattern = r'[A-Za-z0-9]+(?:[._/+&-][A-Za-z0-9]+)*|\s+|.'
    return re.findall(pattern, text)


def refine_wrapped_lines(lines, font, max_width):
    lines = [line for line in lines if line]
    lines = avoid_leading_punctuation(lines)
    lines = avoid_trailing_opening_punctuation(lines)
    lines = avoid_short_lines(lines, font, max_width)
    return avoid_leading_punctuation(lines)


def avoid_leading_punctuation(lines):
    leading_punctuation = set("，。！？；：、,.!?;:)）]】}》」』’”％%")
    adjusted = []
    for line in lines:
        while adjusted and line and line[0] in leading_punctuation:
            adjusted[-1] += line[0]
            line = line[1:].lstrip()
        if line:
            adjusted.append(line)
    return adjusted


def avoid_trailing_opening_punctuation(lines):
    opening_punctuation = set("(（[【{《「『‘“")
    adjusted = []
    carry = ""
    for line in lines:
        line = carry + line
        carry = ""
        if line and line[-1] in opening_punctuation:
            carry = line[-1]
            line = line[:-1].rstrip()
        if line:
            adjusted.append(line)
    if carry:
        if adjusted:
            adjusted[-1] += carry
        else:
            adjusted.append(carry)
    return adjusted


def avoid_short_lines(lines, font, max_width):
    if len(lines) < 2:
        return lines

    for index in range(len(lines) - 1, 0, -1):
        if meaningful_length(lines[index]) >= 3:
            continue

        previous = lines[index - 1].rstrip()
        base_line = lines[index].lstrip()
        line = base_line
        move_tokens = []
        tokens = tokenize_wrap_text(previous)

        while tokens and meaningful_length(line) < 3:
            token = tokens.pop()
            if token.isspace():
                continue
            move_tokens.insert(0, token)
            line = "".join(move_tokens) + base_line

        new_previous = "".join(tokens).rstrip()
        if new_previous and font.getlength(strip_markers(line)) <= max_width:
            lines[index - 1] = new_previous
            lines[index] = line

    return [line for line in lines if line]


def meaningful_length(line):
    count = 0
    for token in re.findall(r'[A-Za-z0-9]+|[\u4e00-\u9fff]', line):
        count += len(token) if token.isascii() else 1
    return count
