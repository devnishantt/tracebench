from hashlib import sha256
from pathlib import Path
import json

def file_digest(path: Path) -> str:
    result = sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            result.update(chunk)
    return result.hexdigest()

def canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    return sha256(encoded.encode('utf-8')).hexdigest()
