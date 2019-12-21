from pathlib import Path

import pytest

import tfont


@pytest.fixture
def original_shared_datadir(request) -> Path:
    return Path(request.fspath.dirname, "data")


@pytest.fixture
def ConvertedTestFont(original_shared_datadir) -> tfont.Font:
    return tfont.converters.UFOConverter().open(
        original_shared_datadir / "TestFont.ufo"
    )
