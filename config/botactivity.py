import discord

#playing    : Playing ...
#watching   : Watching ...
#listening  : Listening to ...

__activities__ = [(discord.ActivityType.playing, 'with cryptos'),
                  (discord.ActivityType.playing, 'with myself'),
                  (discord.ActivityType.watching, 'over the WLC server'),
                  (discord.ActivityType.watching, 'you right now'),
                  (discord.ActivityType.listening, 'bullshit'),
                  (discord.ActivityType.playing, 'crushing your enemies'),
                  (discord.ActivityType.watching, 'them driven before you'),
                  (discord.ActivityType.playing, 'Zeh oder Finger'),
                  (discord.ActivityType.listening,
                   'the lamentations of their women')]
__activityTimer__ = 5 * 60  #5 minutes
