
import pytest
from cogs.timers import secondsToReadable

def test_secondsToReadable():
    """Test secondsToReadable formatting."""
    # 1 minute
    assert secondsToReadable(60) == "1m"
    # 1 hour
    assert secondsToReadable(3600) == "1h"
    # 1 day
    assert secondsToReadable(86400) == "1d"
    # 1 week
    assert secondsToReadable(604800) == "1w"
    # 1 year
    assert secondsToReadable(31536000) == "1y" # 365 days
    
    # Complex duration
    # 1h 1m 1s = 3600 + 60 + 1 = 3661
    assert secondsToReadable(3661) == "1h 1m 1s"
    
    # 1w 2d = 604800 + 2*86400 = 604800 + 172800 = 777600
    assert secondsToReadable(777600) == "1w 2d"
    
    # Zero?
    # Function default kwarg is 600, but if passed 0:
    # returns empty string if all are 0?
    # Let's see code: readable = '' ... if > 0 append. return readable.strip()
    assert secondsToReadable(0) == ""
