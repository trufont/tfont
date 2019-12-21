import tfont.converters


def test_convert_TestFont(original_shared_datadir):
    tf = tfont.converters.UFOConverter().open(original_shared_datadir / "TestFont.ufo")
    assert tf
