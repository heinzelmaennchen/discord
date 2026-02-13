
from utils.bobbybquotes import bbquotes

def test_bbquotes_structure():
    """Test structure and content of bobbybquotes."""
    # Verify it is a list
    assert isinstance(bbquotes, list)
    
    # Verify it is not empty
    assert len(bbquotes) > 0
    
    # Verify all items are strings
    for quote in bbquotes:
        assert isinstance(quote, str)
        # Verify no empty strings
        assert len(quote) > 0

def test_bbquotes_content():
    """Test specific expected content in bobbybquotes."""
    # Check for a known quote to ensure correct file loaded
    known_quote = "IS THAT HOW YOU SPEAK TO YOUR KING??"
    assert known_quote in bbquotes
