import pytest
from cogs.timers import secondsToReadable, getTimerResponse
from unittest.mock import MagicMock

def test_secondsToReadable():
    """Test secondsToReadable function formatting."""
    assert secondsToReadable(60) == "1m"
    assert secondsToReadable(3600) == "1h"
    assert secondsToReadable(3661) == "1h 1m 1s"
    assert secondsToReadable(86400) == "1d"
    assert secondsToReadable(604800) == "1w"
    # returns empty string if all are 0?
    # Let's see code: readable = '' ... if > 0 append. return readable.strip()
    assert secondsToReadable(0) == ""
