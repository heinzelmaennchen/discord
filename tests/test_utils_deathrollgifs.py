
from utils.deathrollgifs import gifdict

def test_gifdict_structure():
    """Test structure and content of gifdict."""
    # Verify it is a dictionary
    assert isinstance(gifdict, dict)
    
    # Verify expected keys exist
    expected_keys = [
        'start', 'bigloss', 'highroll', 'leet', '300', 
        '69', 'loser', 'lowroll', 'roll', 'whew', 'winner'
    ]
    for key in expected_keys:
        assert key in gifdict
        assert isinstance(gifdict[key], list)
        assert len(gifdict[key]) > 0
        
    # Verify all items in lists are strings (URLs)
    for key, gif_list in gifdict.items():
        for gif_url in gif_list:
            assert isinstance(gif_url, str)
            assert gif_url.startswith('http')
