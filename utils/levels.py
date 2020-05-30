from PIL import Image, ImageDraw, ImageFont
import requests
import math

# Helper functions for Level system


# Create a rankcard image (for !rank command in Cog levels)
def createRankcard(author, authornum, authorurl, rank, level, lvlxp, nlvlxp):
    # Parameter Aufbereitung
    if lvlxp >= 1000:
        lvlxp = math.floor(lvlxp / 10) * 10
        strLvlXp = f'{lvlxp/1000}K'
    else:
        strLvlXp = str(lvlxp)
    if nlvlxp >= 1000:
        nlvlxp = math.ceil(nlvlxp / 100) * 100
        strNlvlxp = f'{nlvlxp/1000}K'
    else:
        strNlvlxp = str(nlvlxp)
    # Neues Image in 8x Vergrößerung erstellen - Farbe: Schwarz
    img = Image.new('RGB', (886 * 8, 210 * 8), color='black')
    # Alpha Maske für kreisförmigen Ausschnitt des User Logos erstellen
    mask_im = Image.new('RGBA', (1280, 1280), color=(0, 0, 0, 0))
    mask = ImageDraw.Draw(mask_im)
    mask.ellipse([(0, 0), (1280, 1280)], fill=(0, 0, 0, 255))
    # User Logo einlesen und auf Faktor 10 vergrößern
    avatar_url = authorurl
    avatar = Image.open(requests.get(avatar_url, stream=True).raw)
    avatar = avatar.resize((1280, 1280), Image.LANCZOS)
    # User Logo mittels Alpha Maske in ein neues Image kopieren
    img2 = Image.new('RGBA', (1280, 1280), color=(0, 0, 0, 0))
    img2.paste(avatar, (0, 0), mask=mask_im)
    # Kreisförmiges Logo auf Hintergrundbild kopieren und auf gewollte Größe (x1/8) verkleinern
    img.paste(img2, (32 * 8, 26 * 8))
    img = img.resize((886, 210), Image.LANCZOS)
    # Progressbar Hintergrund und Progress erstellen
    barbg = Image.new('RGB', (632, 36), color='#484B4E')
    bar = Image.new('RGB', (math.floor(lvlxp / nlvlxp * 632), 36),
                    color='#62d3f5')
    # ... und einfügen
    img.paste(barbg, (234, 148))
    img.paste(bar, (234, 148))
    # Fonts definieren
    fntL = ImageFont.truetype('fonts/Poppins-Regular.ttf', 60)
    fntM = ImageFont.truetype('fonts/Poppins-Regular.ttf', 42)
    fntS = ImageFont.truetype('fonts/Poppins-Regular.ttf', 26)
    # Username - Text
    draw = ImageDraw.Draw(img)
    name_width = fntM.getsize(author)
    draw.text((234, 85), author, font=fntM, fill=(255, 255, 255))
    draw.text((234 + name_width[0], 102),
              f'  #{authornum}',
              font=fntS,
              fill='#7F8384')
    # Textbreiten ermitteln
    xp1_width = fntS.getsize(strLvlXp)
    xp2_width = fntS.getsize(f' / {strNlvlxp} XP')
    lvlnum_width = fntL.getsize(str(level))
    lvl_width = fntS.getsize("LEVEL ")
    ranknum_width = fntL.getsize(f'#{rank}  ')
    rank_width = fntS.getsize("RANK ")
    # XP - Text
    draw.text((866 - xp1_width[0] - xp2_width[0], 102),
              strLvlXp,
              font=fntS,
              fill=(255, 255, 255))
    draw.text((866 - xp2_width[0], 102),
              f" / {strNlvlxp} XP",
              font=fntS,
              fill='#7F8384')
    # Level - Text
    draw.text((866 - lvlnum_width[0], 0),
              str(level),
              font=fntL,
              fill='#62d3f5')
    draw.text((866 - lvlnum_width[0] - lvl_width[0], 36),
              "LEVEL",
              font=fntS,
              fill='#62d3f5')
    # Rank - Text
    draw.text((866 - lvlnum_width[0] - lvl_width[0] - ranknum_width[0], 0),
              f"#{rank}",
              font=fntL,
              fill='#ffffff')
    draw.text((866 - lvlnum_width[0] - lvl_width[0] - ranknum_width[0] -
               rank_width[0], 36),
              "RANK",
              font=fntS,
              fill='#ffffff')
    # Shadow Background
    rankcard = Image.new('RGB', (916, 240), color='#23272A')
    rankcard.paste(img, (15, 15))
    # neue Rankcard abspeichern
    rankcard.save(f'storage/levels/{author}.png')


# Create a leaderboard image (for !levels command in Cog levels)
def createLeaderboard(author, authorurl, level, xp, lvlxp, nlvlxp):

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