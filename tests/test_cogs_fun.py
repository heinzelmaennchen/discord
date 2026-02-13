
import pytest
from cogs.fun import cleanupString

def test_cleanupString():
    """Test cleanupString function to remove punctuation."""
    # ".,?!" are replaced by space
    assert cleanupString("Hello.World") == "Hello World"
    assert cleanupString("Hello,World") == "Hello World"
    assert cleanupString("Hello?World") == "Hello World"
    assert cleanupString("Hello!World") == "Hello World"
    assert cleanupString("Hello.,?!World") == "Hello    World"
    assert cleanupString("NoPunctuation") == "NoPunctuation"
