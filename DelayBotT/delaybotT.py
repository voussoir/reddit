#/u/GoldenSights
import praw
import time
import datetime
import sqlite3

'''USER CONFIGURATION'''

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter Bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
MAXPOSTS = 30
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
TSTRING = "[request]"
#This is the part of the title that you want to look for
DELAY = 172800
#This is the time limit between a user's posts, IN SECONDS. 1h = 3600 || 12h = 43200 || 24h = 86400 || 144h = 518400

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
cur.execute('CREATE TABLE IF NOT EXISTS users(name TEXT, lastpost TEXT)')
print('Loaded Users')
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')
print('Loaded Oldposts')
sql.commit()

r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def getTime(bool):
	timeNow = datetime.datetime.now(datetime.timezone.utc)
	timeUnix = timeNow.timestamp()
	if bool == False:
		return timeNow
	else:
		return timeUnix

def scan():
	print('Scanning ' + SUBREDDIT)
	subreddit = r.get_subreddit(SUBREDDIT)
	posts = subreddit.get_new(limit=MAXPOSTS)
	for post in posts:
		try:
			pauthor = post.author.name
		except Exception:
			pauthor = '[deleted]'
		pid = post.id
		plink = post.short_link
		ptime = post.created_utc
		ptitle = post.title.lower()
		if TSTRING.lower() in ptitle:
			cur.execute('SELECT * FROM oldposts WHERE id=?', [pid])
			if not cur.fetchone():
				cur.execute('SELECT * FROM users WHERE name=?', [pauthor])
				if not cur.fetchone():
					print('Found new user: ' + pauthor)
					cur.execute('INSERT INTO users VALUES(?, ?)', (pauthor, pid))
					r.send_message(pauthor, 'Welcome to /r/pkmntcgtrades!','Dear ' + pauthor + ',\n\n Our bot has determined that this is your first time posting in /r/pkmntcgtrades. Please take the time to read [the guidelines](http://www.reddit.com/r/pkmntcgtrades/wiki/guidelines) to understand how the subreddit works.\n\nIf you have any questions, feel free to [message the moderators.](http://www.reddit.com/message/compose?to=%2Fr%2Fpkmntcgtrades) Thanks, and happy trading!', captcha=None)
					sql.commit()
					print('\t' + pauthor + ' has been added to the database.')
					time.sleep(5)
				else:
					cur.execute('SELECT * FROM users WHERE name=?', [pauthor])
					fetch = cur.fetchone()
					print('Found post by known user: ' + pauthor)
					previousid = fetch[1]
					previous = r.get_info(thing_id='t3_'+previousid)
					previoustime = previous.created_utc
					if ptime > previoustime:
						curtime = getTime(True)
						difference = curtime - previoustime
						if difference >= DELAY:
							print('\tPost complies with timelimit guidelines. Permitting')
							cur.execute('DELETE FROM users WHERE name=?', [pauthor])
							cur.execute('INSERT INTO users VALUES(?, ?)', (pauthor, pid))
							sql.commit()
							print('\t' + pauthor + "'s database info has been reset.")
						else:
							differences = '%.0f' % (DELAY - difference)
							print('\tPost does not comply with timelimit guidelines. Author must wait ' + differences)
							print('\t' + pauthor + "'s database info remains unchanged")
							response = post.add_comment('You are posting here too frequently, so your post has been deleted. You may post again in ' + str(datetime.timedelta(seconds=float(differences))))
							response.distinguish()
							post.remove(spam=False)
							time.sleep(5)
				cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
		sql.commit()




while True:
	try:
		scan()
	except Exception as e:
		print('An error has occured:', e)
	print('Running again in ' + WAITS + ' seconds.\n')
	time.sleep(WAIT)
