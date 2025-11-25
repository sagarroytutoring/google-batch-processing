import re
import glob
import os
import fnmatch
from typing import Optional


class StarFormat:
    def __init__(self, format: str) -> None:
        if not format.count('*') == 1:
            raise ValueError("Format string must contain exactly one '*', found: " + format)
        self._format = format
    
    def match(self, filename: str) -> Optional[str]:
        pieces = self._format.split('*')
        if filename.startswith(pieces[0]) and filename.endswith(pieces[1]):
            return filename[len(pieces[0]):-len(pieces[1])] if pieces[1] else filename[len(pieces[0]):]
        return None
    
    def format(self, sub: str) -> str:
        return self._format.replace('*', sub)
