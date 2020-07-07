from datetime import datetime
from pytz import timezone

DISCORD_EPOCH = 1420070400000


def getMessageTime(message):
    ms = (message.id >> 22) + DISCORD_EPOCH
    time = datetime.fromtimestamp(ms / 1000, timezone('Europe/Vienna'))
    return time


def isDevServer(ctx):
    if ctx.guild.id == 405433814114893835:
        return True
    else:
        return False