
import pytest
from unittest.mock import MagicMock
from cogs.crypto import crypto

def test_calculateRating():
    """Test calculateRating method in crypto cog."""
    # Mock init dependencies
    # crypto init calls init_db, getTrackedBannedCoins
    # and needs COINGECKO_KEY env var
    
    with pytest.MonkeyPatch().context() as m:
        m.setenv("COINGECKO_KEY", "dummy")
        
        # Mock init_db and getTrackedBannedCoins
        # We can mock the class methods or just mock the instance attributes after creation if we mock __init__?
        # Better: Mock imports in cogs/crypto.py before importing crypto class? 
        # But we already imported crypto. Too late?
        # Actually, if we just instantiate, we need to handle what __init__ does.
        # It calls `self.cnx = init_db()` and `getTrackedBannedCoins(self)`.
        
        # Let's try to mock the methods on the class before instantiation if possible, 
        # or just mock the module level functions.
        pass

# Redoing import strategy for mocking side effects during import/class definition if needed
# But here `init_db` is called inside `__init__`.
# So we can patch `cogs.crypto.init_db` and `cogs.crypto.getTrackedBannedCoins`.

from unittest.mock import patch

@patch('cogs.crypto.init_db')
@patch('cogs.crypto.getTrackedBannedCoins')
def test_calculateRating_logic(mock_getCoins, mock_init_db):
    """Test logic of calculateRating."""
    mock_getCoins.return_value = ([], []) # ourCoins, bannedCoins
    mock_init_db.return_value = MagicMock()
    
    mock_client = MagicMock()
    with pytest.MonkeyPatch().context() as m:
        m.setenv("COINGECKO_KEY", "dummy")
        cog = crypto(mock_client)
        
        # <= -5
        # pos 1
        assert cog.calculateRating("-10", 1) == '<:meatonbone_mgr_1:1184563797810216980>'
        # pos 2
        assert cog.calculateRating("-5", 2) == '<:meatonbone_mgr_2:1184563834590072902>'
        
        # >= 5
        # pos 3
        assert cog.calculateRating("10", 3) == '<:fullmoon_mgr_3:1184563746371272754>'
        assert cog.calculateRating("5", 1) == '<:fullmoon_mgr_1:1184563679287591052>'
        
        # Between -5 and 5
        assert cog.calculateRating("0", 1) == '<:cucumber_mgr_1:1184563462953775134>'
        assert cog.calculateRating("4.9", 2) == '<:cucumber_mgr_2:1184563534667972628>'
        assert cog.calculateRating("-4.9", 3) == '<:cucumber_mgr_3:1184563581228961943>'
        
        # Invalid
        # pos 4 (else case)
        assert cog.calculateRating("10", 4) == '❌'
        
        # ValueError case
        assert cog.calculateRating("abc", 1) == '❌'
