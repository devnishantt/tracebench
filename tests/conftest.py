from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from tracebench.dataset import Dataset, load_dataset


@pytest.fixture
def dataset_factory(tmp_path: Path) -> Iterator[Callable[..., Dataset]]:
    opened: list[Dataset] = []
    counter = 0

    def make(text: str, *, filename: str | None = None, **options: object) -> Dataset:
        nonlocal counter
        counter += 1
        path = tmp_path / (filename or f"source-{counter}.csv")
        path.write_text(text, encoding="utf-8")
        dataset = load_dataset(path, **options)
        opened.append(dataset)
        return dataset

    yield make
    for dataset in opened:
        dataset.close()
