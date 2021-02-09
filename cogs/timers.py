import discord
from discord.ext import commands

import re
import asyncio
import datetime
from pytz import timezone
import json

from main import taskDict


class timers(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Timer
    #@commands.command(aliases=['reminder'])
    @commands.group(aliases=['reminder'], invoke_without_command=True)
    @commands.guild_only()
    async def timer(self, ctx, *, arg):
        '''creates a timer
    ---------------
    !timer <duration> or !timer <duration> <reason> OR
    !timer <date> <time> or !timer <date> <time> <reason>

    <duration> Each of the following terms is optional but at least one has to be used. Timer durations < 10s and > 10y aren't allowed.
    
    2years 3weeks 2days 7hours 30minutes 17seconds
     year   week   day   hour    minute    second
     y      w      d     h       min       sec
                                 m         s

    <date>: D.M.YYYY
    <time>: hh:mm
    The duration from now until <date> <time> isn't allowed to be < 10s or > 10y.
    
    <reason> (optional) text which will be added to the mention
    
    Examples: 
    !timer 4h 30min Zockerdonnerstag!!!
    !timer 13.7.1337 13:37 Oaschradieren!!!
    '''
        compiled = re.compile(
            r'((?P<years>[0-9]+) ?y(ears?)?)?( ?(?P<weeks>[0-9]+) ?w(eeks?)?)?( ?(?P<days>[0-9]+) ?d(ays?)?)?( ?(?P<hours>[0-9]+) ?h(ours?)?)?( ?(?P<minutes>[0-9]+) ?m(in(utes?)?)?)?( ?(?P<seconds>[0-9]+) ?s(ec(onds?)?)?)?( (?P<reason>.+))?',
            flags=re.I)
        match = compiled.match(arg)
        if match is None or not match.group(0):
            compiled = re.compile(
                r'(?P<reDateTime>(?P<day>[0-9]{1,2}).(?P<month>[0-9]{1,2}).(?P<year>[0-9]{4}) *(?P<hour>[0-9]{1,2}):(?P<minute>[0-9]{1,2}))( (?P<reason>.+))?',
                flags=re.I)
            match = compiled.match(arg)
            if match is None or not match.group(0):
                await ctx.send(
                    'Heast Gschissana, die Dauer bzw. Datum/Zeit musst schon richtig eingeben, damit das was wird!'
                )
                return
            else:
                timerStatus = 1
        else:
            timerStatus = 0
        duration = 0
        endtime = None

        if timerStatus == 0:
            years = match.group('years')
            if years is not None:
                duration += int(years.rstrip(' yY')) * 60 * 60 * 24 * 365

            weeks = match.group('weeks')
            if weeks is not None:
                duration += int(weeks.rstrip(' wW')) * 60 * 60 * 24 * 7

            days = match.group('days')
            if days is not None:
                duration += int(days.rstrip(' dD')) * 60 * 60 * 24

            hours = match.group('hours')
            if hours is not None:
                duration += int(hours.rstrip(' hH')) * 60 * 60

            minutes = match.group('minutes')
            if minutes is not None:
                duration += int(minutes.rstrip(' mM')) * 60

            seconds = match.group('seconds')
            if seconds is not None:
                duration += int(seconds.rstrip(' sS'))
        elif timerStatus == 1:
            # TO DO : Werte auf gültige Werte begrenzen
            day = int(match.group('day'))
            month = int(match.group('month'))
            year = int(match.group('year'))
            hour = int(match.group('hour'))
            minute = int(match.group('minute'))

            tz = timezone('Europe/Vienna')
            try:
                endtime = tz.localize(
                    datetime.datetime(year, month, day, hour,
                                      minute)).timestamp()
            except ValueError:
                await ctx.send(
                    'So wird des nix. Diese Jahr/Monat/Tag/Stunden/Minuten - Kombi gibts nicht.'
                )
                return
            starttime = datetime.datetime.now().timestamp()
            duration = int(endtime - starttime)

        reason = match.group('reason')
        if duration < 10 or duration > 315360000:
            await ctx.send(
                f'Oida du Heisl, gib g\'fälligst eine Dauer oder Datum/Zeit innerhalb von 10s bis 10y ein.'
            )
            return

        response = getTimerResponse(reason)
        timer = [ctx.author.id, ctx.channel.id, duration, reason, response]
        tId = saveTimerToJSON(timer, endtime)
        timer.append(tId)

        await ctx.send(response[0].format(ctx.author,
                                          secondsToReadable(duration), reason,
                                          tId))
        newTask = {
            tId: (asyncio.create_task(createTimer(self.client, timer),
                                      name=tId))
        }
        taskDict.update(newTask)

    @timer.command(name='list')
    @commands.guild_only()
    async def timer_list(self, ctx, arg=None):
        response = ''
        count = 0
        with open('storage/timer.json') as json_file:
            jsonTimerData = json.load(json_file)
        for timer in jsonTimerData['timers']:
            if jsonTimerData['timers'][timer]['author'] == ctx.author.id:
                if arg != 'all' and jsonTimerData['timers'][timer][
                        'channel'] != ctx.channel.id:
                    continue
                else:
                    if jsonTimerData['timers'][timer]['reason'] != None:
                        reason = jsonTimerData['timers'][timer]['reason']
                    else:
                        reason = '<keine Beschreibung>'
                    remaining = int(jsonTimerData['timers'][timer]['endtime'] -
                                    datetime.datetime.now().timestamp())
                    enddatetime = str(
                        datetime.datetime.fromtimestamp(
                            jsonTimerData['timers'][timer]['endtime'],
                            timezone('Europe/Vienna')))[:-9]
                    channelname = self.client.get_channel(
                        jsonTimerData['timers'][timer]['channel']).name

                    response += f"\n[#{timer}] [{enddatetime}] {reason} ({secondsToReadable(remaining)} remaining)"
                    if arg == 'all':
                        response += f' [#{channelname}]'
                count += 1
        if count == 1:
            strTimer = 'timer'
        else:
            strTimer = 'timers'
        response = f'```{count} {strTimer} open [{ctx.author.name}]' + response + '```'
        await ctx.send(response)

    @timer.command(name='cancel')
    @commands.guild_only()
    async def timer_cancel(self, ctx, tId):
        with open('storage/timer.json') as json_file:
            jsonTimerData = json.load(json_file)
        #check if it's your own timer
        tId = tId.lstrip('#')
        if tId not in jsonTimerData['timers'] or jsonTimerData['timers'][tId][
                'author'] != ctx.author.id:
            await ctx.send(
                f'Timer #{tId} ist nicht von dir oder existiert nicht!')
            return
        tId = int(tId)
        task = taskDict[tId]
        task.cancel()
        taskDict.pop(tId)
        removeTimerFromJSON(tId)
        await ctx.send(f'Timer #{tId} wurde gelöscht!')


def getTimerResponse(reason):
    response = []
    if reason is not None:
        response.append('Yesh. Timer für {2} ist auf [{1}] gestellt! [#{3}]')
        response.append(
            'Hey {0.mention}! Ich soll dich an "{2}" erinnern! [#{3}]')
        response.append(
            'Hey {0.mention}! Ich hätte dich an "{2}" erinnern sollen. Leider war ich zu der Zeit offline. :((((( [#{3}]'
        )
    else:
        response.append('Okay. Habe einen Timer auf [{1}] gestellt! [#{3}]')
        response.append('Huhu {0.mention}: Dein Timer ist abgelaufen! [#{3}]')
        response.append(
            'Hey {0.mention}! Ich hätte dich an irgendetwas erinnern sollen. Leider war ich zu der Zeit offline. :((((( [#{3}]'
        )
    return response


async def createTimer(bot, timer):
    # timer[0:AuthorId, 1:ChannelId, 2:duration, 3:reason, 4:respone, 5:tId]
    await asyncio.sleep(timer[2])
    await bot.get_channel(timer[1]
                          ).send(timer[4][1].format(bot.get_user(timer[0]),
                                                    timer[2], timer[3],
                                                    timer[5]))
    taskDict.pop(timer[5])
    removeTimerFromJSON(timer[5])


def saveTimerToJSON(timer, endtime):
    with open('storage/timer.json') as json_file:
        jsonTimerData = json.load(json_file)

    timerCounter = jsonTimerData['counter'] + 1
    starttime = datetime.datetime.now().timestamp()
    if endtime == None:
        endtime = int(starttime + timer[2])
    newCounter = {"counter": timerCounter}
    jsonTimerData.update(newCounter)
    newTimer = {
        str(timerCounter): {
            "author": timer[0],
            "channel": timer[1],
            "starttime": starttime,
            "duration": timer[2],
            "endtime": endtime,
            "reason": timer[3]
        }
    }
    jsonTimerData['timers'].update(newTimer)

    with open('storage/timer.json', 'w') as json_file:
        json.dump(jsonTimerData, json_file, indent=4, ensure_ascii=True)
    return timerCounter


def removeTimerFromJSON(tId):
    with open('storage/timer.json') as json_file:
        jsonTimerData = json.load(json_file)
        jsonTimerData['timers'].pop(str(tId))
    with open('storage/timer.json', 'w') as json_file:
        json.dump(jsonTimerData, json_file, indent=4, ensure_ascii=True)


async def restartTimersOnBoot(self):
    with open('storage/timer.json') as f:
        jsonTimerData = json.load(f)
        for jsontimer in jsonTimerData['timers']:
            tId = int(jsontimer)
            tAuthor = jsonTimerData['timers'][jsontimer]['author']
            tChannel = jsonTimerData['timers'][jsontimer]['channel']
            endtime = jsonTimerData['timers'][jsontimer]['endtime']
            reason = jsonTimerData['timers'][jsontimer]['reason']
            response = getTimerResponse(reason)
            now = datetime.datetime.now().timestamp()

            if now + 1 > endtime:
                await self.get_channel(tChannel).send(response[2].format(
                    self.get_user(tAuthor), None, reason, tId))
                removeTimerFromJSON(tId)
            else:

                duration = endtime - now
                tList = [tAuthor, tChannel, duration, reason, response, tId]
                newTask = {
                    tId: (asyncio.create_task(createTimer(self, tList),
                                              name=tId))
                }
                taskDict.update(newTask)


def secondsToReadable(seconds=600):
    years, remainder = divmod(seconds, 60 * 60 * 24 * 365)
    weeks, remainder = divmod(remainder, 60 * 60 * 24 * 7)
    days, remainder = divmod(remainder, 60 * 60 * 24)
    hours, remainder = divmod(remainder, 60 * 60)
    minutes, seconds = divmod(remainder, 60)
    readable = ''
    if years > 0:
        readable += f'{years}y '
    if weeks > 0:
        readable += f'{weeks}w '
    if days > 0:
        readable += f'{days}d '
    if hours > 0:
        readable += f'{hours}h '
    if minutes > 0:
        readable += f'{minutes}m '
    if seconds > 0:
        readable += f'{seconds}s'
    readable = readable.strip()
    return readable


def setup(client):
    client.add_cog(timers(client))
