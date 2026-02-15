
import pytest
from unittest.mock import MagicMock
from cogs.crypto import crypto
from unittest.mock import patch

@patch('cogs.crypto.get_db_connection')
@patch('cogs.crypto.getTrackedBannedCoins')
def test_calculateRating_logic(mock_getCoins, mock_get_db):
    """Test logic of calculateRating."""
    mock_getCoins.return_value = ([], []) # ourCoins, bannedCoins
    mock_get_db.return_value = MagicMock()
    
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
