"""Narrow MQL preflight: input is a global declaration modifier, not an identifier.
This does not replace MetaEditor compilation.
"""
from pathlib import Path
import re

def check_source(source):
    # Preserve line offsets while ignoring quoted literals and comments.
    masked = re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"',
                    lambda m: re.sub(r'[^\n]', ' ', m.group()), source)
    failures = []
    depth = 0
    for number, line in enumerate(masked.splitlines(), 1):
        for match in re.finditer(r'\binput\b|[{}]', line):
            token = match.group()
            if token == '{':
                depth += 1
            elif token == '}':
                depth -= 1
            elif depth != 0 or line[:match.start()].strip():
                failures.append(number)
    return failures

def check_tree(root):
    return [(str(p.relative_to(root)), n)
            for p in sorted(Path(root).rglob('*')) if p.suffix in ('.mq5', '.mqh')
            for n in check_source(p.read_text())]
