
import pytest
from cogs.hltb import getTimeString

def test_getTimeString():
    """Test getTimeString for formatting hours."""
    # 0 hours returns -- Hrs
    assert getTimeString(0) == "-- Hrs"
    
    # Integers are formatted as integer strings
    assert getTimeString(10) == "10 Hrs"
    assert getTimeString(5) == "5 Hrs"
    
    # 0.5 round logic. The function: round(timeInHours * 2) / 2
    # 10.5 -> 21 / 2 -> 10.5 -> floor(10.5) is 10, remainder is 0.5 so "10½ Hrs"
    assert getTimeString(10.5) == "10½ Hrs"
    
    # Test rounding behavior
    # 10.2 -> 20.4 -> round(20.4)=20 -> 10.0 -> "10 Hrs"
    assert getTimeString(10.2) == "10 Hrs"
    
    # 10.3 -> 20.6 -> round(20.6)=21 -> 10.5 -> "10½ Hrs"
    assert getTimeString(10.3) == "10½ Hrs"
    # 10.7 * 2 = 21.4 -> round(21.4) = 21 -> 21/2 = 10.5 -> "10½ Hrs"
    assert getTimeString(10.7) == "10½ Hrs"
    
    assert getTimeString(10.7) == "10½ Hrs"
    
    # 10.8 * 2 = 21.6 -> round(21.6) = 22 -> 11.0 -> "11 Hrs"
    assert getTimeString(10.8) == "11 Hrs"

