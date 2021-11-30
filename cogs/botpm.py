from discord.ext import commands
from utils.db import check_connection, init_db
from utils.misc import sendLongMsg
from enum import Enum

egglist_temp = []
egglist_active = {}
forbidden_words = []


class Operation(Enum):
    CREATE = 1
    READ = 2
    DELETE = 3


class Easteregg():
    def __init__(self, user, id):
        self.user = user
        self.id = id
        self.triggers_done = False
        self.triggers = []
        self.responses = []

    def add_trigger(self, trigger):
        self.triggers.append(trigger)

    def add_response(self, response):
        self.responses.append(response)

    def print_triggers(self):
        return ', '.join(self.triggers)

    def print_responses(self):
        return ', '.join(self.responses)


class botpm(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cnx = init_db()
        self.cursor = self.cnx.cursor(buffered=True)

        # Initialize the eastereggs after reload/load
        self.initEggs(self.cursor, self.cnx)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user or message.author.bot or message.content.startswith(
                '!'):
            return

        global egglist_temp
        # Continue editing open eggs if there are any for this user.
        for egg in egglist_temp:
            if egg.user == message.author.id:
                if message.content.strip().lower() == 'done':
                    if egg.triggers:
                        if egg.triggers_done:
                            await message.channel.send(
                                "Ohne Antwort wird's nix, Captain. Also?")
                        else:
                            await message.channel.send(
                                "Guad, dann brauchen wir noch eine Antwort, pls."
                            )
                            egg.triggers_done = True
                    else:
                        await message.channel.send(
                            "Ohne Trigger wird's nix, Captain. Also?")
                elif not egg.triggers_done:
                    if await self.checkContent(message.content):
                        egg.add_trigger(message.content.lower())
                        await message.channel.send(
                            "Läuft, läuft, lohnt! Schreib' entweder noch ein Triggerwort, oder 'done' für den nächsten Schritt."
                        )
                        return
                    else:
                        await message.channel.send(message.content +
                                                   ' is ned erlaubt. NEXT!')
                elif not egg.responses:
                    if await self.checkContent(message.content):
                        egg.add_response(message.content.replace("+>", ">"))
                        await message.channel.send(
                            "Das war's, thx! Wart', ich hau das in die Datenbank."
                        )
                        egglist_active[egg.id] = egg
                        egglist_temp.remove(egg)
                        try:
                            self.dbOperation(Operation.CREATE, egg)
                        except Exception as e:
                            await message.channel.send(
                                "Irgendwas kaputt :(\n" + str(e))
                            return
                        await message.channel.send(
                            "Erledigt! Probier' hier gleich noch aus, ob's auch wirklich funktioniert. Zur Erinnerung: \""
                            + egg.print_triggers() + "\" soll \"" +
                            egg.print_responses() + "\" triggern.")
                        return
                    else:
                        await message.channel.send(message.content +
                                                   ' is ned erlaubt. NEXT!')
            break

        # Check if an egg is triggered
        for egg in egglist_active.values():
            if any(x in message.content.lower() for x in egg.triggers):
                await message.channel.send(''.join(egg.responses))

    @commands.command(aliases=['ae', 'createegg'])
    @commands.dm_only()
    async def addegg(self, ctx):
        # Set flow to 'ADD' to mark we're in the adding flow
        global egglist_temp
        for egg in egglist_temp:
            if egg.user == ctx.author.id:
                await ctx.send("Du hast schon ein Ei offen, du Ei!")
                if not egg.triggers:
                    await ctx.send("Gib mir ein Triggerwort, pls.")
                else:
                    await ctx.send("Sag mir was der bot antworten soll, pls.")
                return

        # If no open egg is found, make a new one for this author
        # First grab the highest current id from the DB and add 1
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)

        query = (f'SELECT MAX(id) FROM eastereggs')

        self.cursor.execute(query)
        self.cnx.commit()

        row = self.cursor.fetchone()

        if row[0] is None:
            egg_id = 0
        else:
            egg_id = int(row[0]) + 1

        new_egg = Easteregg(ctx.author.id, egg_id)
        egglist_temp.append(new_egg)
        await ctx.send("Kk, los geht's! Erstes Triggerwort?")

    @commands.command(aliases=['le', 'showeggs'])
    @commands.dm_only()
    async def listeggs(self, ctx):
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)

        query = (
            f'SELECT id, date, triggers, responses FROM eastereggs WHERE author = {ctx.author.id}'
        )
        self.cursor.execute(query)
        self.cnx.commit()

        if self.cursor.rowcount == 0:
            await ctx.send(
                "Das Nichts nichtet. !addegg verwenden, um eins zu erstellen.")
        else:
            rows = self.cursor.fetchall()
            r = '```\n'
            for row in rows:
                r += ('#' + str(row[0]) + ' - ' + str(row[1]) +
                      ' - Trigger(s): ' + row[2] + ' - Antwort: ' +
                      row[3].replace("`", "") + '\n')
            r += '```'
            await sendLongMsg(ctx, r)

    @commands.command(aliases=['deleteegg', 'removeegg', 'se'])
    @commands.dm_only()
    async def scrapegg(self, ctx, delete_id=None):

        global egglist_active

        if delete_id is None:
            await ctx.send(
                "Ohne ID wird's nix. Um die IDs anzuzeigen, !listeggs verwenden."
            )
            return
        else:
            try:
                int(delete_id)

                # Check DB connection
                self.cnx = check_connection(self.cnx)
                self.cursor = self.cnx.cursor(buffered=True)

                query = (
                    f'SELECT id, author FROM eastereggs WHERE id = {delete_id}'
                )
                self.cursor.execute(query)
                self.cnx.commit()

                if self.cursor.rowcount == 0:
                    await ctx.send(
                        "ID nicht gefunden. !addegg verwenden, um ein neues zu erstellen."
                    )
                else:
                    row = self.cursor.fetchone()
                    if int(row[1]) != ctx.author.id:
                        await ctx.send(
                            "Eastereggs von anderen löschen is uncool! !listeggs um deine eigenen anzuzeigen."
                        )
                    else:
                        query = (
                            f'DELETE FROM eastereggs WHERE id = {delete_id}')
                        self.cursor.execute(query)
                        self.cnx.commit()
                        del egglist_active[int(delete_id)]
                        await ctx.send("Gelöscht :(")

            except Exception:
                await ctx.send("Kaputte ID, bitte nur Zahlen eingeben.")

    @commands.command(aliases=['hme', 'howmany', 'wieviele'])
    async def howmanyeggs(self, ctx):
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)

        query = (f'SELECT count(*) FROM eastereggs')
        self.cursor.execute(query)
        self.cnx.commit()

        if self.cursor.rowcount == 0:
            await ctx.send(
                "Das Nichts nichtet. !addegg verwenden, um ein neues zu erstellen."
            )
        else:
            row = self.cursor.fetchone()
            count = row[0]
            await ctx.send(f'Es gibt {count} custom eastereggs!1elf')

    # Check for forbidden words or if the word is too short
    async def checkContent(self, message):
        if len(message) < 3:
            return False
        elif '|' in message:
            return False
        elif message in forbidden_words:
            return False
        return True

    def dbOperation(self, operation, egg):
        # Check DB connection
        self.cnx = check_connection(self.cnx)
        self.cursor = self.cnx.cursor(buffered=True)

        if operation.name == 'CREATE':

            triggers = "|".join(egg.triggers)
            responses = "|".join(egg.responses)

            query = (
                f'INSERT INTO `eastereggs` (`id`, `date`, `author`, `triggers`, `responses`) VALUES ("{egg.id}", CURRENT_DATE(), "{egg.user}", "{triggers}", "{responses}")'
            )
            self.cursor.execute(query)
            self.cnx.commit()

    # Initialize eggs on startup or reload
    def initEggs(self, cursor, cnx):
        global egglist_active

        query = (f'SELECT id, author, triggers, responses FROM eastereggs')
        cursor.execute(query)
        cnx.commit()

        if cursor.rowcount == 0:
            return
        else:
            rows = cursor.fetchall()
            for row in rows:
                egg = Easteregg(row[1], row[0])
                # Add triggers
                triggers = row[2].split('|')
                for trigger in triggers:
                    egg.add_trigger(trigger)
                # Add responses
                responses = row[3].split('|')
                for response in responses:
                    egg.add_response(response)
                # Add the egg to the active list
                egglist_active[egg.id] = egg


def setup(client):
    client.add_cog(botpm(client))