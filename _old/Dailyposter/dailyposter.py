#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import datetime

'''USER CONFIGURATION'''

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub you will make the post in.
WAIT = 200
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

PTIME = "07:45"
#HH:MM Format
#TWENTY-FOUR HOUR STYLE
#UTC TIMEZONE
#http://www.timeanddate.com/time/map/


#The Following Post title and Post text can be customized using the strftime things
#    https://docs.python.org/2/library/time.html#time.strftime
#    Ex: "Daily thread for %A %B %d %Y" = "Daily thread for Tuesday November 04 2014"
#Don't forget that the text will be wrung through reddit Markdown
PTITLE = "Automated post for %B %d, %Y"
PTEXT = """
This post is being made by a robot

Creating a new line on reddit requires hitting Enter twice

*test*

Heyo | Woah | Numbers
:- | :- | -:
Text | Box | 9000
Foo | Bar | 32
"""


'''All done!'''


WAITS = str(WAIT)
try:
	import bot
	USERAGENT = bot.aG
except ImportError:
	pass


sql = sqlite3.connect('sql.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS posts(ID TEXT, STAMP TEXT, CREATED INT)')
print('Loaded SQL Database')
sql.commit()

print('Logging in')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

ptime = PTIME.split(':')
ptime = (60*int(ptime[0])) + int(ptime[1])

def dailypost():
	subreddit = r.get_subreddit(SUBREDDIT, fetch=True)
	#I want to ping reddit on every cycle. I've had bots lose their session before
	now = datetime.datetime.now(datetime.timezone.utc)
	daystamp = datetime.datetime.strftime(now, "%d%b%Y")
	cur.execute('SELECT * FROM posts WHERE STAMP=?', [daystamp])
	nowtime = (60*now.hour) + now.minute
	print('Now: ' + str(nowtime) + ' ' + datetime.datetime.strftime(now, "%H:%M"))
	print('Pst: ' + str(ptime) + ' ' + PTIME)
	if not cur.fetchone():
		diff = nowtime-ptime
		if diff > 0:
			print('t+ ' + str(abs(diff)) + ' minutes')
			makepost(now, daystamp)
		else:
			print('t- ' + str(diff) + ' minutes')
	else:
		print("Already made today's post")



def makepost(now, daystamp):
	print('Making post...')
	ptitle = datetime.datetime.strftime(now, PTITLE)
	ptext = datetime.datetime.strftime(now, PTEXT)
	try:			
		newpost = r.submit(SUBREDDIT, ptitle, text=ptext, captcha=None)
		print('Success: ' + newpost.short_link)
		cur.execute('INSERT INTO posts VALUES(?, ?, ?)', [newpost.id, daystamp, newpost.created_utc])
		sql.commit()
	except praw.requests.exceptions.HTTPError as e:
		print('ERROR: PRAW HTTP Error.', e)


while True:
	try:
		dailypost()
	except Exception as e:
		print("ERROR:", e)
	print('Sleeping ' + WAITS + ' seconds.\n')
	time.sleep(WAIT)