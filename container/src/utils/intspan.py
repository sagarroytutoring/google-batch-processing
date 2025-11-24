import re

_INTSPAN_RE = re.compile(r'((\d+(-\d+)?),)*(\d+(-\d+)?)')
_INTSPAN_GROUP = re.compile(r'(\d+(?:-(\d+))?)')


class IntSpan:
    def __init__(self, span_str: str):
        if not _INTSPAN_RE.fullmatch(span_str):
            raise ValueError(f"Invalid IntSpan string: {span_str}")
        self.ranges = []
        for match in _INTSPAN_GROUP.finditer(span_str):
            part = match.group(1)
            if '-' in part:
                start, end = map(int, part.split('-'))
                if start > end:
                    raise ValueError(f"Invalid range in IntSpan: {part}")
            else:
                val = int(part)
                start, end = val, val
            self.ranges.append((start, end))

    def __iter__(self):
        for start, end in self.ranges:
            for val in range(start, end + 1):
                yield val

    def __contains__(self, item: int) -> bool:
        for start, end in self.ranges:
            if start <= item <= end:
                return True
        return False
    
    def __bool__(self) -> bool:
        return bool(self.ranges)
