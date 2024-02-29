from utils.db import check_connection
  
# Get OurCoins and BannedCoins from DB
def getTrackedBannedCoins(self):
    query = ('SELECT coin, is_banned FROM `tracked_banned_coins`')
    ourCoins = []
    bannedCoins = []
    # Check DB connection
    self.cnx = check_connection(self.cnx)
    self.cursor = self.cnx.cursor(buffered=True)
    # Execute query
    self.cursor.execute(query)
    self.cnx.commit()
    rows = self.cursor.fetchall()
    for r in rows:
        if r[1] == 0:
            ourCoins.append(r[0])
        else:
            bannedCoins.append(r[0])
    return ourCoins, bannedCoins