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
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter Bot".
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
MAXPOSTS = 1
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
DELAY = 300
#This is the time, IN SECONDS, the user has to make his comment. If he does not have a source by this time, post is removed.
MESSAGE = "You have not made a comment within the timelimit. Your post has been removed. Contact the moderators if you believe this was done in error"
#This is what the bot tells you when your post gets removed. Uses reddit's usual Markdown formatting
MINLENGTH = 50
#The minimum length of a Source comment to count as valid. You can set this to 0 for any comment to be valid.
TOOSHORT = "You have added a source comment, but it is under the character requirement. Try to add some more info.\n\nYour post has not been removed."
#This is what gets replied when MINLENGTH is not met.
IGNOREMODS = False
#Do you want the bot to ignore posts made by moderators? Use True or False (With capitals! No quotations!)
IGNORESELFPOST = False
#Do you want the bot to ignore selfposts?
'''All done!'''






WAITS = str(WAIT)
try:
	import bot
	USERAGENT = bot.getaG()
except ImportError:
	pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS oldpost_index ON oldposts(id)')
print('Loaded Oldposts')
sql.commit()

r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def getTime(bool):
	timeNow = datetime.datetime.now(datetime.timezone.utc)
	timeUnix = timeNow.timestamp()
	if bool is False:
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
		found = False
		short = False
		opc = []
		pid = post.id
		try:
			pauthor = post.author.name
		except AttributeError:
			pauthor = '[deleted]'
		ptime = post.created_utc
		curtime = getTime(True)		
		
		cur.execute('SELECT * FROM oldposts WHERE id=?', [pid])
		if not cur.fetchone():
			if post.is_self is False or IGNORESELFPOST is False:
				if pauthor not in mods or IGNOREMODS is False:
					difference = curtime - ptime
					
					print(pid + ', ' + pauthor + ': Finding comments')
					comments = praw.helpers.flatten_tree(post.comments)
					for comment in comments:
						cid = 't3_' + comment.id
						try:
							cauthor = comment.author.name
						except AttributeError:
							cauthor = '[deleted]'
						if cauthor == pauthor and found is False:
							print('\tFound comment by OP')
							found = True
							cbody = comment.body
							clength = len(cbody)
							opc.append(clength)

					if found is True:
						if all(num < MINLENGTH for num in opc):
							print('\tAll OP comments too short')
							short = True

									
					
					if difference > DELAY:		 
						if found is False:
							print('\tComments were empty, or OP was not found. Post will be removed.')
							response = post.add_comment(MESSAGE)
							response.distinguish()
							post.remove(spam=False)
							print('\tPost removed')
							time.sleep(5)
							
						if found is True and short is True:
							print('\tFound comment, but reporting for length')
							post.report()
							response = post.add_comment(TOOSHORT)
							response.distinguish()
						
						if found is True and short is False:
							print('\tComment is okay. Passing')

						cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
					else:
						differences = str('%.0f' % (DELAY - difference))
						print('\tStill has ' + differences + 's.')
				
				if pauthor in mods and IGNOREMODS is True:
					print(pid + ', ' + pauthor + ': Ignoring Moderator')
					cur.execute('INSERT INTO oldposts VALUES(?)', [pid])

			if post.is_self is True and IGNORESELFPOST is True:
				print(pid + ', ' + pauthor + ': Ignoring Selfpost')
				cur.execute('INSERT INTO oldposts VALUES(?)', [pid])

		sql.commit()



while True:
	try:
		scan()
	except Exception as e:
		print('An error has occured:', e)
	print('Running again in ' + WAITS + ' seconds.\n')
	time.sleep(WAIT)