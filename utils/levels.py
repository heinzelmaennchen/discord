from PIL import Image, ImageDraw, ImageFont
import requests
import math


# Helper functions for Level system

# Create a rankcard image (for !rank command in Cog levels)
async def createRankcard(author, authorurl, rank, xp, level, lvlxp, nlvlxp):
    # Colors
    cGold = (218, 158, 59, 0)
    cSilver = (152, 152, 152, 0)
    cBronze = (174, 116, 65, 0)
    cDarkGrey = (80, 85, 90, 0)
    cLightGrey = (133, 135, 138, 0)
    cBlue = '#62d3f5'
    # Fonts
    fntXL = ImageFont.truetype('fonts/Poppins-Regular.ttf', 42)
    fntL = ImageFont.truetype('fonts/Poppins-Regular.ttf', 32)
    fntS = ImageFont.truetype('fonts/Poppins-Regular.ttf', 26)
    # Font heights
    fntXL_height = fntXL.getsize('gh')[1]
    fntL_height = fntL.getsize('gh')[1]

    # IMG Size
    (x, y) = (900, 116)
    border = 15

    # Hintergrundbild für Rank
    imgRankcard = Image.new('RGB', (x + 2 * border, y + 2 * border),
                            color='#23272A')

    # Parameter Aufbereitung
    msgtolvlup = '{:,}'.format(math.ceil(
        (nlvlxp - lvlxp) / 20)).replace(',', ' ')
    strXp = '{:,}'.format(xp).replace(',', ' ')

    if rank == 1:
        rankColor = cGold
    elif rank == 2:
        rankColor = cSilver
    elif rank == 3:
        rankColor = cBronze
    else:
        rankColor = cDarkGrey

    # RANK CIRCLE Size & Location
    disRankCircle = 10
    sizRankCircle = 60
    locRankCircle = (disRankCircle, int(y / 2 - sizRankCircle / 2))

    # LOGO Size & Location
    disLogo = 10
    sizLogo = 100
    locLogo = (locRankCircle[0] + sizRankCircle + disLogo,
               int(y / 2 - sizLogo / 2))

    # PROGRESS CIRCE Size & Location
    disProgress = 10
    sizProgress = 100
    locProgress = (x - disProgress - sizProgress, y / 2 - sizProgress / 2)
    widthProgress = 8
    # RANK TEXT location
    widthRank = fntL.getsize(str(rank))[0]
    locRank = (disRankCircle + sizRankCircle / 2 - widthRank / 2,
               y / 2 - fntL_height / 2 - 1)
    # NAME Location
    disName = 10
    locName = (disRankCircle + sizRankCircle + disLogo + sizLogo + disName,
               y / 2 - fntXL_height / 2)
    # LEVEL location
    widthLvl = fntXL.getsize(str(level))[0]
    locLvl = (locProgress[0] + sizProgress / 2 - widthLvl / 2,
              y / 2 - fntXL_height / 2 - 2)
    # EXPERIENCE TEXT & NUM location
    xptext_width = fntS.getsize('EXPERIENCE')[0]
    xpnum_width = fntL.getsize(strXp)[0]
    xp_width = max(xptext_width, xpnum_width)

    disXp = 35
    locXptext = (x - disProgress - sizProgress - disXp - xptext_width, 20)
    locXpnum = (x - disProgress - sizProgress - disXp - xpnum_width, 50)
    # MSG 2 LVLUP TEXT  & NUM location
    msgtext_width = fntS.getsize('^ MSGS')[0]
    msgnum_width = fntL.getsize(msgtolvlup)[0]

    disMsg = 35
    locMsgText = (x - disProgress - sizProgress - disXp - xp_width - disMsg -
                  msgtext_width, 20)
    locMsgNum = (x - disProgress - sizProgress - disXp - xp_width - disMsg -
                 msgnum_width, 50)
    # New Image with size x10 for antialiasing of Circles
    img = Image.new('RGB', (x * 10, y * 10), color=(0, 0, 0, 0))
    # Alpha Mask for User Logo (circle)
    mask_im = Image.new('RGBA', (sizLogo * 10, sizLogo * 10),
                        color=(0, 0, 0, 0))
    mask = ImageDraw.Draw(mask_im)
    mask.ellipse([(0, 0), (sizLogo * 10, sizLogo * 10)], fill=(0, 0, 0, 255))
    # Load Userlogo and resize to x10 of final size (antialiasing)
    avatar_url = authorurl
    avatar = Image.open(requests.get(avatar_url, stream=True).raw)
    avatar = avatar.resize((sizLogo * 10, sizLogo * 10), Image.LANCZOS)
    # Paste User Logo with alpha mask on Image
    img.paste(avatar, (locLogo[0] * 10, locLogo[1] * 10), mask=mask_im)
    # RANK Circle
    draw = ImageDraw.Draw(img)
    draw.ellipse([(locRankCircle[0] * 10, locRankCircle[1] * 10),
                  ((locRankCircle[0] + sizRankCircle) * 10,
                   (locRankCircle[1] + sizRankCircle) * 10)],
                 fill=rankColor)
    # Progress Circle Background
    draw.arc([(locProgress[0] * 10, locProgress[1] * 10),
              ((locProgress[0] + sizProgress) * 10,
               (locProgress[1] + sizProgress) * 10)],
             start=0,
             end=360,
             fill=cDarkGrey,
             width=widthProgress * 10)
    # Progress Circle Blue
    draw.arc([(locProgress[0] * 10, locProgress[1] * 10),
              ((locProgress[0] + sizProgress) * 10,
               (locProgress[1] + sizProgress) * 10)],
             start=-90,
             end=(lvlxp / nlvlxp * 360) - 90,
             fill=cBlue,
             width=widthProgress * 10)
    # Resize to x/y
    img = img.resize((x, y), Image.LANCZOS)
    # Draw Call
    draw = ImageDraw.Draw(img)
    # Username - Text
    name = author
    if fntXL.getsize(name)[0] > 271:
        while fntXL.getsize(name)[0] > 250:
            name = name[:-1]
        name += '...'
    draw.text((locName[0], locName[1]), name, font=fntXL, fill=(255, 255, 255))
    # LEVEL - Text
    draw.text(locLvl, str(level), font=fntXL, fill=cBlue)
    # XP - TEXT
    draw.text(locXptext, 'EXPERIENCE', font=fntS, fill=cLightGrey)
    draw.text(locXpnum, strXp, font=fntL, fill='white')
    # MSG - TEXT
    draw.text(locMsgText, '^ MSGS', font=fntS, fill=cLightGrey)
    draw.text(locMsgNum, msgtolvlup, font=fntL, fill='white')
    # RANK - TEXT
    draw.text(locRank, str(rank), font=fntL, fill='white')
    # PASTE IMAGE into Rankcard
    imgRankcard.paste(img, (border, border))
    # SAVE RANKCARD as .png
    imgRankcard.save(f'storage/levels/{author}.png')


# Create a leaderboard image (for !levels command in Cog levels)
async def createLeaderboard(author, authorurl, level, xp, lvlxp, nlvlxp):

    # Colors
    cGold = (218, 158, 59, 0)
    cSilver = (152, 152, 152, 0)
    cBronze = (174, 116, 65, 0)
    cDarkGrey = (80, 85, 90, 0)
    cLightGrey = (133, 135, 138, 0)
    cBlue = '#62d3f5'
    # Fonts
    fntXL = ImageFont.truetype('fonts/Poppins-Regular.ttf', 42)
    fntL = ImageFont.truetype('fonts/Poppins-Regular.ttf', 32)
    fntS = ImageFont.truetype('fonts/Poppins-Regular.ttf', 26)
    # Font heights
    fntXL_height = fntXL.getsize('gh')[1]
    fntL_height = fntL.getsize('gh')[1]

    # IMG Size
    (x, y) = (900, 116)
    usercount = len(author)
    border = 15
    space = 3

    # Hintergrundbild für Levels
    imgLevels = Image.new('RGB', (x + 2 * border, y * usercount + space *
                                  (usercount - 1) + 2 * border),
                          color='#23272A')

    for i in range(0, len(author)):
        # Parameter Aufbereitung
        msgtolvlup = '{:,}'.format(math.ceil(
            (nlvlxp[i] - lvlxp[i]) / 20)).replace(',', ' ')
        strXp = '{:,}'.format(xp[i]).replace(',', ' ')

        if i == 0:
            rankColor = cGold
        elif i == 1:
            rankColor = cSilver
        elif i == 2:
            rankColor = cBronze
        else:
            rankColor = cDarkGrey

        # RANK CIRCLE Size & Location
        disRankCircle = 10
        sizRankCircle = 60
        locRankCircle = (disRankCircle, int(y / 2 - sizRankCircle / 2))

        # LOGO Size & Location
        disLogo = 10
        sizLogo = 100
        locLogo = (locRankCircle[0] + sizRankCircle + disLogo,
                   int(y / 2 - sizLogo / 2))

        # PROGRESS CIRCE Size & Location
        disProgress = 10
        sizProgress = 100
        locProgress = (x - disProgress - sizProgress, y / 2 - sizProgress / 2)
        widthProgress = 8
        # RANK TEXT location
        widthRank = fntL.getsize(str(i + 1))[0]
        locRank = (disRankCircle + sizRankCircle / 2 - widthRank / 2,
                   y / 2 - fntL_height / 2 - 1)
        # NAME Location
        disName = 10
        locName = (disRankCircle + sizRankCircle + disLogo + sizLogo + disName,
                   y / 2 - fntXL_height / 2)
        # LEVEL location
        widthLvl = fntXL.getsize(str(level[i]))[0]
        locLvl = (locProgress[0] + sizProgress / 2 - widthLvl / 2,
                  y / 2 - fntXL_height / 2 - 2)
        # EXPERIENCE TEXT & NUM location
        xptext_width = fntS.getsize('EXPERIENCE')[0]
        xpnum_width = fntL.getsize(strXp)[0]
        xp_width = max(xptext_width, xpnum_width)

        disXp = 35
        locXptext = (x - disProgress - sizProgress - disXp - xptext_width, 20)
        locXpnum = (x - disProgress - sizProgress - disXp - xpnum_width, 50)
        # MSG 2 LVLUP TEXT  & NUM location
        msgtext_width = fntS.getsize('^ MSGS')[0]
        msgnum_width = fntL.getsize(msgtolvlup)[0]

        disMsg = 35
        locMsgText = (x - disProgress - sizProgress - disXp - xp_width -
                      disMsg - msgtext_width, 20)
        locMsgNum = (x - disProgress - sizProgress - disXp - xp_width -
                     disMsg - msgnum_width, 50)
        # New Image with size x10 for antialiasing of Circles
        img = Image.new('RGB', (x * 10, y * 10), color=(0, 0, 0, 0))
        # Alpha Mask for User Logo (circle)
        mask_im = Image.new('RGBA', (sizLogo * 10, sizLogo * 10),
                            color=(0, 0, 0, 0))
        mask = ImageDraw.Draw(mask_im)
        mask.ellipse([(0, 0), (sizLogo * 10, sizLogo * 10)],
                     fill=(0, 0, 0, 255))
        # Load Userlogo and resize to x10 of final size (antialiasing)
        avatar_url = authorurl[i]
        avatar = Image.open(requests.get(avatar_url, stream=True).raw)
        avatar = avatar.resize((sizLogo * 10, sizLogo * 10), Image.LANCZOS)
        # Paste User Logo with alpha mask on Image
        img.paste(avatar, (locLogo[0] * 10, locLogo[1] * 10), mask=mask_im)
        # RANK Circle
        draw = ImageDraw.Draw(img)
        draw.ellipse([(locRankCircle[0] * 10, locRankCircle[1] * 10),
                      ((locRankCircle[0] + sizRankCircle) * 10,
                       (locRankCircle[1] + sizRankCircle) * 10)],
                     fill=rankColor)
        # Progress Circle Background
        draw.arc([(locProgress[0] * 10, locProgress[1] * 10),
                  ((locProgress[0] + sizProgress) * 10,
                   (locProgress[1] + sizProgress) * 10)],
                 start=0,
                 end=360,
                 fill=cDarkGrey,
                 width=widthProgress * 10)
        # Progress Circle Blue
        draw.arc([(locProgress[0] * 10, locProgress[1] * 10),
                  ((locProgress[0] + sizProgress) * 10,
                   (locProgress[1] + sizProgress) * 10)],
                 start=-90,
                 end=(lvlxp[i] / nlvlxp[i] * 360) - 90,
                 fill=cBlue,
                 width=widthProgress * 10)
        # Resize to x/y
        img = img.resize((x, y), Image.LANCZOS)
        # Draw Call
        draw = ImageDraw.Draw(img)
        # Username - Text
        if fntXL.getsize(author[i])[0] > 271:
            while fntXL.getsize(author[i])[0] > 250:
                author[i] = author[i][:-1]
            author[i] += '...'
        draw.text((locName[0], locName[1]),
                  author[i],
                  font=fntXL,
                  fill=(255, 255, 255))
        # LEVEL - Text
        draw.text(locLvl, str(level[i]), font=fntXL, fill=cBlue)
        # XP - TEXT
        draw.text(locXptext, 'EXPERIENCE', font=fntS, fill=cLightGrey)
        draw.text(locXpnum, strXp, font=fntL, fill='white')
        # MSG - TEXT
        draw.text(locMsgText, '^ MSGS', font=fntS, fill=cLightGrey)
        draw.text(locMsgNum, msgtolvlup, font=fntL, fill='white')
        # RANK - TEXT
        draw.text(locRank, str(i + 1), font=fntL, fill='white')
        # PASTE IMAGE into LEADERBOARD
        imgLevels.paste(img, (border, border + (y + space) * i))
    # SAVE LEADERBOARD as .png
    imgLevels.save('storage/levels/leaderboard.png')