#/u/GoldenSights
import praw
import time
import datetime
import sqlite3

'''USER CONFIGURATION'''

USERNAME = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter Bot".
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
MAXPOSTS = 60
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 30
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
DELAY = 86400
#This is the time, IN SECONDS, which the post will hold the active flair
IGNOREMODS = False
#Do you want the bot to ignore posts made by moderators? Use True or False (With capitals! No quotations!)
IGNORESELFPOST = False
#Do you want the bot to ignore selfposts?
IGNORELINK = True
#Do you want the bot to ignore linkposts?
FLAIRACTIVE = "Active"
CSSACTIVE = "active"
#The flair text and css class assigned to unsolved posts.

TITLEREQS = ['[',']']
#Every part of this list must be included in the title
'''All done!'''






WAITS = str(WAIT)
try:
	import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
	USERNAME = bot.getuG()
	PASSWORD = bot.getpG()
	USERAGENT = bot.getaG()
except ImportError:
	pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')
print('Loaded Oldposts')
sql.commit()


r = praw.Reddit(USERAGENT)

Trying = True
while Trying:
	try:
		r.login(USERNAME, PASSWORD)
		print('Successfully logged in\n')
		Trying = False
	except praw.errors.InvalidUserPass:
		print('Wrong Username or Password')
		quit()
	except Exception as e:
		print("%s" % e)
		time.sleep(5)

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
	moderators = subreddit.get_moderators()
	mods = []
	for moderator in moderators:
		mods.append(moderator.name)
	posts = subreddit.get_new(limit=MAXPOSTS)
	for post in posts:
		ctimes = []
		pid = post.id
		ptitle = post.title.lower()
		try:
			pauthor = post.author.name
		except AttributeError:
			pauthor = '[deleted]'
		ptime = post.created_utc
		cur.execute('SELECT * FROM oldposts WHERE id=?', [pid])
		if not cur.fetchone():
			if (post.is_self == True and IGNORESELFPOST == False) or (post.is_self == False and IGNORELINK == False):
				if pauthor not in mods or IGNOREMODS == False:
					if all(char.lower() in ptitle for char in TITLEREQS):
						try:
							flair = post.link_flair_text.lower()
						except AttributeError:
							flair = ''
						if flair == '':
							print(pid + ': No Flair')
							now = getTime(True)
							if (now - ptime) > DELAY:
								print('\tOld. Ignoring')
								cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
							else:
								print('\tAssigning Active Flair')
								post.set_flair(flair_text=FLAIRACTIVE,flair_css_class=CSSACTIVE)	
						elif flair == FLAIRACTIVE.lower():
							print(pid + ': Active')
							now = getTime(True)
							if (now-ptime) > DELAY:
								print('\tOld. Removing Flair')
								post.set_flair(flair_text="",flair_css_class="")
								cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
							else:
								print('\tActive for ' + ('%.0f' % (DELAY-(now-ptime))) + ' more seconds')
	
					else:
						print(pid + ': Does not contain titlereq')
						cur.execute('INSERT INTO oldposts VALUES(?)', [pid])

				if pauthor in mods and IGNOREMODS == True:
					print(pid + ', ' + pauthor + ': Ignoring Moderator')
					cur.execute('INSERT INTO oldposts VALUES(?)', [pid])

			else:
				print(pid + ', ' + pauthor + ': Ignoring post')
				cur.execute('INSERT INTO oldposts VALUES(?)', [pid])

		sql.commit()



while True:
	try:
		scan()
	except Exception as e:
		print('An error has occured:', str(e))
	sql.commit()
	print('Running again in ' + WAITS + ' seconds.\n')
	time.sleep(WAIT)