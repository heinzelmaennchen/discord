import pytest
from unittest.mock import MagicMock, patch
from cogs.botpm import botpm, Easteregg

# Mocking database connection and cursor to isolate tests
@patch('cogs.botpm.get_db_connection')
def test_Easteregg_class(mock_get_db):
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

    # Test adding responses
    egg.add_response("hi there")
    assert "hi there" in egg.responses
    assert egg.print_responses() == "hi there"

@pytest.mark.asyncio
async def test_checkContent():
    """Test checkContent method in botpm cog."""
    # Setup mock dependencies for botpm init
    mock_client = MagicMock()
    
    # Mock database interactions in __init__? 
    # botpm __init__ doesn't use db anymore.
    # It just sets self.client.
    
    # checkContent calls get_db_connection if len > 2... wait, checkContent uses Easteregg.
    # Let's check botpm.py again. checkContent does NOT use DB directly, it uses self.eggs.
    # But initEggs uses DB.
    

    # Mock get_db_connection for botpm
    with patch('cogs.botpm.get_db_connection') as mock_get_db:
         mock_get_db.return_value = MagicMock()
         
         cog = botpm(mock_client)
         
         # checkContent does not use DB or self.eggs, it uses global forbidden_words
         
         # Test short message (len < 3)
         assert await cog.checkContent("hi") is False
         
         # Test message with forbidden char '|'
         assert await cog.checkContent("te|st") is False
         
         # Test normal valid message
         assert await cog.checkContent("hello world") is True
         
         # Test forbidden words
         with patch('cogs.botpm.forbidden_words', ['badword']):
                assert await cog.checkContent("badword") is False
                assert await cog.checkContent("goodword") is True
