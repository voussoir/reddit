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
MAXPOSTS = 30
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 30
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
DELAY = 300
#This is the time, IN SECONDS, the user has to make his comment. If he does not have a source by this time, post is removed.
MESSAGE = "You have not responded to the other users within the time limit. Your post has been removed.\n\n*This is automated. Contact the moderators if you believe this was done in error, or the [author](http://reddit.com/u/Goldensights) if something is broken.*"
#This is what the bot tells you when your post gets removed. Uses reddit's usual Markdown formatting
IGNOREMODS = False
#Do you want the bot to ignore posts made by moderators? Use True or False (With capitals! No quotations!)
IGNORESELFPOST = False
#Do you want the bot to ignore selfposts?
FLAIRUNSOLVED = "unsolved"
CSSUNSOLVED = "unsolved"
#The flair text and css class assigned to unsolved posts.
FLAIRWAITING = "Waiting on OP"
CSSWAITING = "waiting"
#The flair text and css class assigned to waiting posts.
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
		found = False
		ctimes = []
		pid = post.id
		try:
			pauthor = post.author.name
		except AttributeError:
			pauthor = '[deleted]'
		ptime = post.created_utc
		curtime = getTime(True)		
		ctime = curtime
		
		cur.execute('SELECT * FROM oldposts WHERE id="%s"' % pid)
		if not cur.fetchone():
			if post.is_self == False or IGNORESELFPOST == False:
				if pauthor not in mods or IGNOREMODS == False:
					comments = praw.helpers.flatten_tree(post.comments)

					try:
						flair = post.link_flair_text.lower()
					except AttributeError:
						flair = ''

					if flair == FLAIRUNSOLVED.lower():
						print(pid + ': Unsolved')
						for comment in comments:
							try:
								cauthor = comment.author.name
							except AttributeError:
								cauthor = '[deleted]'
							if cauthor != pauthor:
								found = True
								break
						if found == False:
							print('\tNo comments by another user. No action taken.')
						else:
							print('\tFound comment by other user. Marking as Waiting.')
							post.set_flair(flair_text=FLAIRWAITING, flair_css_class=CSSWAITING)



					elif flair == FLAIRWAITING.lower():
						print(pid + ': Waiting')
						for comment in comments:
							try:
								cauthor = comment.author.name
							except AttributeError:
								cauthor = '[deleted]'
							if cauthor == pauthor:
								found = True
							else:
								ctimes.append(comment.created_utc)
						if found == True:
							print('\tFound comment by OP. All clear.')
							post.set_flair(flair_text=FLAIRUNSOLVED, flair_css_class=CSSUNSOLVED)
							cur.execute('INSERT INTO oldposts VALUES("%s")' % pid)
						elif found == False and len(ctimes) > 0:
							print('\tNo comments by OP. Checking time limit.')
							ctime = min(ctimes)
							difference = curtime - ctime
							if difference > DELAY:
								print('\tTime is up.')
								print('\tLeaving Comment')
								newcomment = post.add_comment(MESSAGE)
								print('\tDistinguishing Comment')
								newcomment.distinguish()
								print('\tRemoving Post')
								post.remove()
								cur.execute('INSERT INTO oldposts VALUES("%s")' % pid)
							else:
								differences = str('%.0f' % (DELAY - difference))
								print('\tStill has ' + differences + 's.')
						elif found == False and len(ctimes) == 0:
							print('\tNo comments by OP, but no other comments are available.')

					else:
						print(pid + ': Neither flair')
						cur.execute('INSERT INTO oldposts VALUES("%s")' % pid)

				if pauthor in mods and IGNOREMODS == True:
					print(pid + ', ' + pauthor + ': Ignoring Moderator')
					cur.execute('INSERT INTO oldposts VALUES("%s")' % pid)

			if post.is_self == True and IGNORESELFPOST == True:
				print(pid + ', ' + pauthor + ': Ignoring Selfpost')
				cur.execute('INSERT INTO oldposts VALUES("%s")' % pid)

		sql.commit()



while True:
	try:
		scan()
	except Exception as e:
		print('An error has occured:', str(e))
	print('Running again in ' + WAITS + ' seconds.\n')
	time.sleep(WAIT)