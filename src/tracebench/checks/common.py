from typing import Literal
from ..models import Finding

def finding(code: str, column: str | None, rows: list[int], checked: int, message: str, severity: Literal['error', 'warning'] = 'error', limit: int = 5) -> Finding:
    return Finding(code=code, column=column, severity=severity, failures=len(rows), checked=checked, message=message, sample_rows=rows[:limit])
