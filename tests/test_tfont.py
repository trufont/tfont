import pytest


def test_import_tfont():
    import tfont
    assert hasattr(tfont, "Font")
    assert hasattr(tfont, "TFontConverter")