#/u/GoldenSights
import traceback
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
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
SEARCHTITLE = True
SEARCHTEXT = False
#Should the bot check within the title?
#Should the bot check within the selftext?
KEYWORDS = ["phrase 1", "phrase 2", "phrase 3", "phrase 4"]
#These are the words you are looking for.
#Make empty to reply to ANY post that also matches keyauthor
KEYAUTHORS = ["GoldenSights"]
#These are the names of the authors you are looking for
#Any authors not on this list will not be replied to.
#Make empty to allow anybody
REPLYSTRING = "Hi hungry, I'm dad"
#This is the word you want to put in reply
MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

try:
	import bot
	USERAGENT = bot.getaG()
except ImportError:
	pass

sql = sqlite3.connect('replyposts.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded Completed table')

sql.commit()

r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)


def scansub():
	print('Searching '+ SUBREDDIT + '.')
	subreddit = r.get_subreddit(SUBREDDIT)
	posts = subreddit.get_new(limit=MAXPOSTS)
	for post in posts:
		# Anything that needs to happen every loop goes here.
		pid = post.id

		try:
			pauthor = post.author.name.lower()
		except AttributeError:
			# Author is deleted and we don't care about this post
			continue

		cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
		if cur.fetchone():
			# This post is already marked in the database
			continue
		cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
		sql.commit()
		
		if KEYAUTHORS != [] and all(auth.lower() != pauthor for auth in KEYAUTHORS):
			# This post was not made by a keyauthor
			continue

		pbody = ''
		if SEARCHTITLE:
			pbody += post.title + '\n'
		if SEARCHTEXT:
			pbody += post.selftext
		if KEYWORDS == [] or any(key.lower() in pbody.lower() for key in KEYWORDS):
			print('Replying to ' + pid + ' by ' + pauthor)
			post.add_comment(REPLYSTRING)


while True:
	try:
		scansub()
	except Exception as e:
		traceback.print_exc()
	print('Running again in %d seconds \n' % WAIT)
	sql.commit()
	time.sleep(WAIT)