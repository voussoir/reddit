#/u/GoldenSights
import praw
import time
import traceback
import sqlite3
import sys

''' USER CONFIG '''

USERNAME  = ""
# This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
# This is the bot's Password. 
USERAGENT = ""
# This is a short description of what the bot does. 
# For example "/u/GoldenSights' Newsletter bot to notify of new posts"
SUBREDDIT = "GoldTesting"
# This is the sub or list of subs to scan for new posts. For a single sub, use "sub1".
# For multiple subs, use "sub1+sub2+sub3+...". For all use "all"

CHECK_SUBMISSIONS = True
CHECK_COMMENTS = True
# Should the bot check first-time posts / comments

MESSAGE_SUBJECT = "Welcome to /r/subreddit, _author_!"
MESSAGE_BODY = """
Hey _author_,

This is the first time we've seen you post in /r/subreddit, welcome! Here
are some things you need to know

- one
- two

Thanks,

/r/subreddit mod team
"""
# The subject and body of the message you will to send to new users.
# If you put _author_ in either one of these texts, it will be automatically
# replaced with their usename.
# Feel free to send me a message if you want more injectors

MAXPOSTS = 100
# How many submissions / how many comments to get on each run
# PRAW can get up to 100 in a single call
# Submissions and comments will EACH get this many
# I recommend leaving it at 100

WAIT = 30
# How many seconds to wait between runs.
# The bot is completely inactive during this time.
ERROR_WAIT = 20
# An additional waiting period, used when the bot hits an error.
# Can help prevent unecessary timeouts by waiting for the servers

''' All done! '''

try:
	import bot
	USERNAME = bot.uG
	PASSWORD = bot.pG
	USERAGENT = bot.aG
except ImportError:
	pass

sql = sqlite3.connect('sql.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users(name TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS userindex on users(name)')
sql.commit()

print('Logging in %s' % USERNAME)
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)
del PASSWORD

def welcomebot():
	print('Scanning /r/%s' % SUBREDDIT)
	posts = []
	subreddit = r.get_subreddit(SUBREDDIT)
	if CHECK_SUBMISSIONS:
		print('Getting submissions')
		posts += list(subreddit.get_new(limit=MAXPOSTS))
	if CHECK_COMMENTS:
		print('Getting comments')
		posts += list(subreddit.get_comments(limit=MAXPOSTS))

	for post in posts:
		try:
			pauthor = post.author.name
			cur.execute('SELECT * FROM users WHERE name=?', [pauthor])
			fetch = cur.fetchone()
			if fetch is None:
				cur.execute('INSERT INTO users VALUES(?)', [pauthor])
				sql.commit()
				message_subject = MESSAGE_SUBJECT.replace('_author_', pauthor)
				message_body = MESSAGE_BODY.replace('_author_', pauthor)
				print('%s, %s ... ' % (post.fullname, pauthor), end="")
				sys.stdout.flush()
				r.send_message(pauthor, message_subject, message_body, captcha=None)
				print('Message sent!')
		except AttributeError:
			#Post is deleted so we don't care about it
			pass

while True:
	try:
		welcomebot()
	except:
		traceback.print_exc()
		print('Waiting %d grace period' % ERROR_WAIT)
		time.sleep(ERROR_WAIT)
	print('Sleeping %d seconds\n' % WAIT)
	time.sleep(WAIT)