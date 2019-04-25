from nlpnewt import GenericLabel


def test_get_repr():
    label = GenericLabel(0, 20, a="x", y=20, z=20.0)

    assert repr(label) == "GenericLabel(0, 20, a='x', y=20, z=20.0)"


