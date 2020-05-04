import discord

    #playing    : Playing ...
    #watching   : Watching ...
    #listening  : Listening to ...

__activities__ = [
    (discord.ActivityType.playing, 'with Cryptos'),
    (discord.ActivityType.playing, 'with myself'),
    (discord.ActivityType.watching, 'over the WLC Server'),
    (discord.ActivityType.watching, 'you right now'),
    (discord.ActivityType.listening, 'bullshit')
]
__activityTimer__ = 5 * 60 #5 minutes