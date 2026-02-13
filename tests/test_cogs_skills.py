
import pytest
from unittest.mock import MagicMock
import sys

# Mock dependencies if needed, but doCalculate relies mainly on regex and eval
from cogs.skills import skills

def test_doCalculate():
    """Test doCalculate method in skills cog."""
    # Setup mock client for init (though not used in doCalculate)
    mock_client = MagicMock()
    # We need to set env vars usually for init, but let's see if we can instantiate without
    # The init access os.environ['YOUTUBE_KEY'] and 'KLIPY_KEY'
    # We should mock os.environ
    
    with pytest.MonkeyPatch().context() as m:
        m.setenv("YOUTUBE_KEY", "dummy")
        m.setenv("KLIPY_KEY", "dummy")
        
        cog = skills(mock_client)
        
        # Simple arithmetic
        assert cog.doCalculate("1+1") == "2"
        assert cog.doCalculate("2*3") == "6"
        assert cog.doCalculate("10/2") == "5"
        
        # Power
        assert cog.doCalculate("2^3") == "8"
        
        # Comma handling
        assert cog.doCalculate("1,5+0,5") == "2"
        
        # Factorial
        # 5! = 120
        assert cog.doCalculate("5!") == "120"
        
        # Invalid characters / Syntax Error
        # doCalculate catches SyntaxError and returns specific strings
        # "I glaub des is a Bledsinn"
        assert cog.doCalculate("1+") == "I glaub des is a Bledsinn"
        
        # Invalid input (regex mismatch)
        # allowed: 0-9 + - * / ( ) . % , ^ !
        # letters are not allowed
        assert cog.doCalculate("abc") == "Keine gültige Berechnung!"
