import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import discord
from discord.ext import commands
import cogs.asdf as asdf_module
from cogs.asdf import asdf
import datetime

@pytest.fixture
def mock_client():
    client = MagicMock()
    client.user = MagicMock()
    return client

@pytest.fixture
def mock_ctx():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.get_member.return_value = MagicMock(display_name="TestUser")
    
    # Fix for async with ctx.channel.typing():
    # typing() is not async, it returns an async context manager
    cm = MagicMock()
    cm.__aenter__ = AsyncMock()
    cm.__aexit__ = AsyncMock()
    ctx.channel.typing = MagicMock(return_value=cm)
    
    return ctx

@pytest.fixture
def cog(mock_client):
    with patch('cogs.asdf.init_db') as mock_init_db, \
         patch('cogs.asdf.levels') as mock_levels:
        mock_init_db.return_value = MagicMock()
        
        # fx for levels.updateXp being awaited/create_task'd
        levels_instance = MagicMock()
        levels_instance.updateXp = AsyncMock() 
        mock_levels.return_value = levels_instance
        
        return asdf(mock_client)

@pytest.mark.asyncio
async def test_asdf_command(cog, mock_ctx):
    # Call the callback directly to bypass Command object wrapper
    await cog.asdf.callback(cog, mock_ctx)
    mock_ctx.send.assert_called_once_with('@everyone Verachtung!!! Guade lupe uiuiui')

@pytest.mark.asyncio
async def test_on_message_ignore_bot(cog, mock_client):
    message = MagicMock()
    message.author = mock_client.user
    await cog.on_message(message)
    # fast return, no other calls expected

@patch('cogs.asdf.getMessageTime')
@patch('cogs.asdf.asyncio.create_task')
@pytest.mark.asyncio
async def test_on_message_asdf_reset_trigger(mock_create_task, mock_getTime, cog):
    message = MagicMock()
    message.channel.id = 405433814547169301 # Valid channel
    message.author.bot = False
    
    # Mock time to be 13:35
    mock_time = MagicMock()
    mock_time.hour = 13
    mock_time.minute = 35
    mock_getTime.return_value = mock_time

    # Reset global state
    asdf_module.asdfReset = False

    await cog.on_message(message)
    
    assert asdf_module.asdfReset is True
    # create_task is called for startReset
    mock_create_task.assert_called()

@patch('cogs.asdf.getMessageTime')
@pytest.mark.asyncio
async def test_on_message_holy_rules_strict_fail(mock_getTime, cog):
    message = MagicMock()
    message.channel.id = 405433814547169301
    message.author.bot = False
    message.content = "not asdf"
    message.add_reaction = AsyncMock()

    # Time 13:37
    mock_time = MagicMock()
    mock_time.hour = 13
    mock_time.minute = 37
    mock_getTime.return_value = mock_time
    
    # Set combo to True to trigger strict rules at :37
    asdf_module.asdfCombo = True

    await cog.on_message(message)
    
    # helper enforceRules -> updatePoints -> cursor.execute
    # verifying reactions are added
    message.add_reaction.assert_any_call('🥚')
    message.add_reaction.assert_any_call('👏')

@patch('cogs.asdf.getMessageTime')
@pytest.mark.asyncio
async def test_on_message_first_asdf_triggers_enforce(mock_getTime, cog):
    """Test that the first 'asdf' validates AND triggers enforceRules (logic check)."""
    message = MagicMock()
    message.channel.id = 405433814547169301
    message.author.bot = False
    message.content = "asdf"
    message.author.id = 123
    message.add_reaction = AsyncMock()

    # Time 13:37
    mock_time = MagicMock()
    mock_time.hour = 13
    mock_time.minute = 37
    mock_getTime.return_value = mock_time
    
    # Reset/Set state
    asdf_module.asdfMention = False
    asdf_module.asdfList = []

    await cog.on_message(message)
    
    assert asdf_module.asdfMention is True
    assert asdf_module.asdfCombo is True
    assert 123 in asdf_module.asdfList
    
    # Existing logic: first user gets reactions!
    message.add_reaction.assert_any_call('🥚')
    message.add_reaction.assert_any_call('👏')

@patch('cogs.asdf.getMessageTime')
@pytest.mark.asyncio
async def test_on_message_subsequent_asdf_valid(mock_getTime, cog):
    """Test that subsequent 'asdf' messages do NOT trigger enforceRules."""
    message = MagicMock()
    message.channel.id = 405433814547169301
    message.author.bot = False
    message.content = "asdf"
    message.author.id = 456
    message.add_reaction = AsyncMock()

    # Time 13:37
    mock_time = MagicMock()
    mock_time.hour = 13
    mock_time.minute = 37
    mock_getTime.return_value = mock_time
    
    # State: Already mentioned
    asdf_module.asdfMention = True
    asdf_module.asdfCombo = True # Assuming combo keeps going
    asdf_module.asdfList = [123]

    await cog.on_message(message)
    
    assert 456 in asdf_module.asdfList
    # Should NOT have added reactions
    message.add_reaction.assert_not_called()

@pytest.mark.asyncio
async def test_printStats(cog, mock_ctx):
    # Mock cursor return
    cog.cursor.rowcount = 1
    cog.cursor.fetchall.return_value = [(123, 5)] # user_id, count
    
    await cog.printStats(mock_ctx, "asdf")
    
    mock_ctx.send.assert_called_once()
    args, kwargs = mock_ctx.send.call_args
    embed = kwargs.get('embed')
    assert embed is not None
    assert "ASDF ranking" in embed.title

