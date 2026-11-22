from scripts.session_runner import normalize_answer


def test_normalize_yaml_true_as_confirm():
    assert normalize_answer(True) == "yes"


def test_normalize_yaml_false_as_cancel():
    assert normalize_answer(False) == "no"


def test_normalize_text_answers():
    assert normalize_answer("second one") == "second one"
    assert normalize_answer(None) is None
