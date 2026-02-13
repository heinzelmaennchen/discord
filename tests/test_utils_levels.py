
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import io

# We need to mock PIL and aiohttp before importing utils.levels if they are not installed in the environment where tests run,
# but since they are in requirements.txt, we assume they are installed.
# However, we want to mock the network calls and image operations to verify logic without side effects.

from utils.levels import createRankcard

@pytest.mark.asyncio
async def test_createRankcard():
    """Test createRankcard generation sanity."""
    
    # Mock inputs
    author = "TestUser"
    authorurl = "http://example.com/avatar.png"
    rank = 1
    xp = 1000
    level = 5
    lvlxp = 500
    nlvlxp = 2000
    
    # Mock aiohttp ClientSession and response
    mock_response = AsyncMock()
    mock_response.status = 200
    # Return a 1x1 black pixel image bytes for PIL to open
    # 1x1 black pixel PNG base64: iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=
    import base64
    pixel_bytes = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
    mock_response.read.return_value = pixel_bytes
    
    # Mock session
    # aiohttp.ClientSession is used as an async context manager
    mock_session = AsyncMock()
    # session.get() returns an async context manager (not awaitable itself)
    # So we make get a MagicMock that returns an AsyncMock (the context manager)
    mock_get_cm = AsyncMock()
    mock_session.get = MagicMock(return_value=mock_get_cm)
    mock_get_cm.__aenter__.return_value = mock_response
    
    # Patch aiohttp.ClientSession to return our mock session object when instantiated
    # The class instance itself is an async context manager
    mock_session_cls_cm = AsyncMock()
    mock_session_cls_cm.__aenter__.return_value = mock_session
    
    with patch('aiohttp.ClientSession', return_value=mock_session_cls_cm):
        # Patch ImageDraw.Draw to avoid actual drawing logic which requires valid font/image objects
        with patch('PIL.ImageDraw.Draw') as mock_draw:
            # We also patch ImageFont.truetype just to avoid file not found error, 
            # but the font object won't be used for drawing since Draw is mocked
            with patch('PIL.ImageFont.truetype') as mock_truetype:
                mock_font = MagicMock()
                # getbbox is still called to calculate positions
                # returns (left, top, right, bottom)
                mock_font.getbbox.return_value = (0, 0, 20, 30) 
                mock_truetype.return_value = mock_font
                
                # Mock the draw object returned by ImageDraw.Draw
                mock_draw_instance = MagicMock()
                mock_draw.return_value = mock_draw_instance
            
                result = await createRankcard(author, authorurl, rank, xp, level, lvlxp, nlvlxp)
            
            # Verify result is a BytesIO object
            assert isinstance(result, io.BytesIO)
            
            # Verify the position is at 0 (ready to read)
            assert result.tell() == 0
            
            # Check content is not empty
            content = result.getvalue()
            assert len(content) > 0
