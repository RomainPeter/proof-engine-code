# examples/pilot-python/tests/test_main.py
from src.core.api import add, subtract


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(5, 3) == 2
