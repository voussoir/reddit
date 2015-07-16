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

MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 40
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''


WAITS = str(WAIT)
try:
    import bot
    USERAGENT = bot.aG
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS upcoming(ID TEXT, SUBREDDIT TEXT, TIME INT, TITLE TEXT, URL TEXT, BODY TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS past(ID TEXT, SUBREDDIT TEXT, TIME INT, TITLE TEXT, URL TEXT, BODY TEXT, POSTLINK TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS internal(NAME TEXT, ID INT)')
print('Loaded Completed table')
cur.execute('SELECT * FROM internal')
f = cur.fetchone()
if not f:
	print('Database is new. Adding ID counter')
	cur.execute('INSERT INTO internal VALUES(?, ?)', ['counter', 1])
else:
	print('Current ID counter: ' + str(f[1]))

sql.commit()

r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)
print(r.user)

def getTime(bool):
	timeNow = datetime.datetime.now(datetime.timezone.utc)
	timeUnix = timeNow.timestamp()
	if bool == False:
		return timeNow
	else:
		return timeUnix

print()
def runtime():
	print('Checking Database')
	now = getTime(True)
	print('Now:' + '.'*15, now)
	cur.execute('SELECT * FROM upcoming')
	fetched = cur.fetchall()
	fetched.sort(key=lambda x: x[2], reverse=False)
	try:
		print('Earliest post:' + '.'*5,fetched[0][2], 'Item ' + fetched[0][0] + ',', round(fetched[0][2] - now), 'seconds')
	except:
		pass

	for member in fetched:
		mtime = member[2]
		if now > mtime:
			iid = member[0]
			title = member[3]
			print('Posting to /r/' + member[1] + ': ' + title)
			if member[5] == '':
				url = member[4]
				text = None
			if member[4] == '':
				text = member[5]
				url =None
			try:
				if text != None:
					newpost = r.submit(member[1], title, text=text, captcha=None, resubmit=True, send_replies=True)
				if url != None:
					newpost = r.submit(member[1], title, url=url, captcha=None, resubmit=True, send_replies=True)
				cur.execute('DELETE FROM upcoming WHERE ID=?', [iid])
				cur.execute('INSERT INTO past VALUES(?, ?, ?, ?, ?, ?, ?)', [iid, member[1], member[2], member[3], member[4], member[5], newpost.id])
				sql.commit()
				print('\tDone!')
			except Exception as e:
				print(e)

while True:
	runtime()
	print('Sleeping ' + WAITS + ' seconds\n')
	time.sleep(WAIT)
