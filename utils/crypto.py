from utils.db import get_db_connection
  
# Get OurCoins and BannedCoins from DB
def getTrackedBannedCoins():
    query = ('SELECT coin, is_banned FROM `tracked_banned_coins`')
    ourCoins = []
    bannedCoins = []
    
    cnx = get_db_connection()
    try:
        cursor = cnx.cursor(buffered=True)
        # Execute query
        cursor.execute(query)
        cnx.commit()
        rows = cursor.fetchall()
        for r in rows:
            if r[1] == 0:
                ourCoins.append(r[0])
            else:
                bannedCoins.append(r[0])
    finally:
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()

    return ourCoins, bannedCoins