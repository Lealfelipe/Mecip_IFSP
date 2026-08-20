from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture(autouse=True)
def isolated_media_root(settings) -> Iterator[Path]:
    """Isola arquivos enviados por cada teste."""
    with TemporaryDirectory(prefix="mecip-test-media-") as temporary_directory:
        media_root = Path(temporary_directory) / "media"
        media_root.mkdir()
        settings.MEDIA_ROOT = media_root
        yield media_root
