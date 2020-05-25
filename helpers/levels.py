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
    # Kreisförmiges Logo auf Hintergrundbild kopieren und auf gewollte Größe (x1/10) verkleinern
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
