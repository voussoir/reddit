#/u/GoldenSights
import praw
import time
import sqlite3

'''USER CONFIGURATION'''
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "goldtesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
'''All done!'''


try:
	import bot
	USERAGENT = bot.aG
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users(NAME TEXT, POINTS TEXT)')
print('Loaded Completed table')
sql.commit()

print("Logging in")
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)


def operate():
	subreddit = r.get_subreddit(SUBREDDIT)
	name = input('Get flair for /u/')
	flair = subreddit.get_flair(name)
	name = flair['user']
	flair = flair['flair_text']
	if flair:
		print(flair)
		cur.execute('SELECT * FROM users WHERE NAME=?', [name])
		f= cur.fetchone()
		if f:
			print('updating')
			cur.execute('UPDATE users SET POINTS=? WHERE NAME=?', [flair, name])
		else:
			print('new entry')
			cur.execute('INSERT INTO users VALUES(?, ?)', [name, flair])
		sql.commit()
	else:
		print(name, "has no flair")
	print()

while True:
	operate()
	print()