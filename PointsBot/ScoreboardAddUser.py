#/u/GoldenSights
import praw
import time
import sqlite3

'''USER CONFIGURATION'''
USERNAME = ""
PASSWORD = ""
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "goldtesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
'''All done!'''


try:
	import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
	USERNAME = bot.uG
	PASSWORD = bot.pG
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
r.login(USERNAME, PASSWORD)


def operate():
	subreddit = r.get_subreddit(SUBREDDIT)
	name = input('Get flair for /u/')
	flair = subreddit.get_flair(name)
	flair = flair['flair_text']
	if flair:
		print(flair)
		cur.execute('SELECT * FROM users WHERE LOWER(NAME)=?', [name.lower()])
		f= cur.fetchone()
		if f:
			cur.execute('UPDATE users SET POINTS=? WHERE NAME=?', [flair, name])
		else:
			cur.execute('INSERT INTO users VALUES(?, ?)', [name, flair])
		sql.commit()
	else:
		print(name, "has no flair")
	print()

while True:
	operate()
	print()