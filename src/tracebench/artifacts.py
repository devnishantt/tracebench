import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from pydantic import ValidationError
from .errors import ArtifactError
from .fingerprint import canonical_digest
from .models import DriftReport, ProfileReport, QualityReport

Report = ProfileReport | QualityReport | DriftReport

def report_json(report: Report) -> str:
    return json.dumps(report.model_dump(mode='json'), ensure_ascii=False, allow_nan=False, indent=2) + '\n'

def write_atomic(path: Path, text: str, *, overwrite: bool = False) -> None:
    path = path.expanduser().absolute()
    if path.exists() and not overwrite:
        raise ArtifactError('Output exists; choose another path or pass --overwrite')
    if path.is_symlink():
        raise ArtifactError('Refusing to overwrite a symbolic-link output')
    temporary: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, prefix='.tracebench-', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if overwrite:
            os.replace(temporary, path)
        else:
            # An exclusive link avoids a check-then-replace overwrite race.
            os.link(temporary, path)
            temporary.unlink()
    except OSError as exc:
        raise ArtifactError(f'Cannot publish report: {type(exc).__name__}') from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

def load_profile(path: Path) -> ProfileReport:
    try:
        if path.stat().st_size > 20_000_000:
            raise ArtifactError('Profile exceeds 20 MB artifact limit')
        report = ProfileReport.model_validate_json(path.read_text(encoding='utf-8'))
        payload = report.model_dump(mode='json', exclude={'generated_at', 'content_fingerprint'})
        if canonical_digest(payload) != report.content_fingerprint:
            raise ArtifactError('Profile fingerprint mismatch; report was changed or is incomplete')
        names = [column.name for column in report.columns]
        if names != report.source.columns or len(set(names)) != len(names):
            raise ArtifactError('Profile column structure is inconsistent')
        for column in report.columns:
            present = column.rows - column.nulls
            total = sum(item['count'] for item in column.categories)
            if column.rows != report.source.rows or column.nulls > column.rows or column.distinct > present:
                raise ArtifactError('Profile counts are inconsistent')
            if abs(column.null_fraction - (column.nulls / column.rows if column.rows else 0)) > 1e-12:
                raise ArtifactError('Profile missing-value fraction is inconsistent')
            if any(not isinstance(item.get('count'), int) or item['count'] < 1 or not isinstance(item.get('key'), str) for item in column.categories):
                raise ArtifactError('Profile category counts are invalid')
            if len({item['key'] for item in column.categories}) != len(column.categories) or total > present or (not column.categories_truncated and total != present):
                raise ArtifactError('Profile category distribution is inconsistent')
        return report
    except (OSError, UnicodeError, ValidationError, TypeError, KeyError) as exc:
        raise ArtifactError(f'Cannot load profile: {type(exc).__name__}') from exc
