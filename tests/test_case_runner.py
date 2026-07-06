from src.oracle_omega.reviewer import review


def test_review_imports():
    assert callable(review)
