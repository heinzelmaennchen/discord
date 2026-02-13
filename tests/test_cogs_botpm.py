
import pytest
from unittest.mock import MagicMock, patch
from cogs.botpm import botpm, Easteregg

# Mocking database connection and cursor to isolate tests
@patch('cogs.botpm.init_db')
@patch('cogs.botpm.check_connection')
def test_Easteregg_class(mock_check_connection, mock_init_db):
    """Test Easteregg class functionality."""
    # Test initialization
    egg = Easteregg(user="test_user", id=1)
    assert egg.user == "test_user"
    assert egg.id == 1
    assert egg.triggers == []
    assert egg.responses == []
    assert egg.triggers_done is False

    # Test adding triggers
    egg.add_trigger("hello")
    assert "hello" in egg.triggers
    assert egg.print_triggers() == "hello"

    egg.add_trigger("world")
    assert "world" in egg.triggers
    assert egg.print_triggers() == "hello, world"

    # Test adding responses
    egg.add_response("hi there")
    assert "hi there" in egg.responses
    assert egg.print_responses() == "hi there"

    egg.add_response("general kenobi")
    assert "general kenobi" in egg.responses
    assert egg.print_responses() == "hi there, general kenobi"

@pytest.mark.asyncio
async def test_checkContent():
    """Test checkContent method in botpm cog."""
    # Setup mock dependencies for botpm init
    mock_client = MagicMock()
    
    # Mock database interactions in __init__
    with patch('cogs.botpm.init_db') as mock_init_db:
        mock_cnx = MagicMock()
        mock_cursor = MagicMock()
        mock_init_db.return_value = mock_cnx
        mock_cnx.cursor.return_value = mock_cursor
        # Mock fetchall to return empty list for initEggs to avoid side effects
        mock_cursor.rowcount = 0
        
        cog = botpm(mock_client)
        
        # Test short message (len < 3)
        assert await cog.checkContent("hi") is False
        
        # Test message with forbidden char '|'
        assert await cog.checkContent("te|st") is False
        
        # Test normal valid message
        assert await cog.checkContent("hello world") is True
        
        # Test forbidden words
        # We need to modify the module-level forbidden_words variable
        # Since it's imported in cogs.botpm, we patch it there
        with patch('cogs.botpm.forbidden_words', ['badword']):
             assert await cog.checkContent("badword") is False
             assert await cog.checkContent("goodword") is True
