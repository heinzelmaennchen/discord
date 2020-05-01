import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ['DATABASE_URL']

conn = psycopg2.connect(DATABASE_URL, sslmode='require')

def randomQuote():
  cur = conn.cursor()
  sql = 'SELECT * FROM wlc_quotes ORDER BY RANDOM() LIMIT 2'
  cur.execute(sql)

  row = cur.fetchone()
  r = ''

  while row is not None:
    r+= (row[1] + ' ' + str(row[2]) + ' ' + row[3] + '\n')
    row = cur.fetchone()

  cur.close()
  return r
