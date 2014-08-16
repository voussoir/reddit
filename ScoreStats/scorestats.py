import praw
try:
	import bot
	USERAGENT = bot.uG
except ImportError:
	USERAGENT = ""

SUBREDDIT = "mildlyinteresting"




r = praw.Reddit(USERAGENT)

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS submissiondata(id TEXT, created INT, title TEXT, score INT)')
cur.execute('CREATE TABLE IF NOT EXISTS commentdata(id TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS oldlinks(ID TEXT)')
print('Loaded Completed table')


MAXPOSTS

def 