#/u/GoldenSights
import praw
import time
import traceback
import sqlite3

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

MESSAGE_INITIAL_SUBJECT = 'Welcome to /r/subreddit, _author_!'
MESSAGE_INITIAL_BODY = '''
Hey _author_,

This is the first time we've seen you post in /r/subreddit, welcome!

Your [first submission](_permalink_) has been added to your new bio page
at /r/subreddit/wiki/_author_.
'''

MESSAGE_UPDATE_SUBJECT = 'Your /r/subreddit bio has been updated'
MESSAGE_UPDATE_BODY = '''
Hey _author_,

Your [submission](_permalink_) to /r/subreddit has been added
to the bottom of your bio at /r/subreddit/wiki/_author_.
'''
# The subject and body of the messages you will to send to users.
# If you put _author_ in either one of these texts, it will be automatically
# replaced with their usename.
# Feel free to send me a message if you want more injectors

WIKI_PAGE_INITIAL_TEXT = '''

This is the bio page for /u/_author_

'''
# When creating a user's wiki page, put this text at the top.

WIKI_POST_FORMAT = '''

---

**[_title_](_permalink_)**

_text_
'''
# The format used when putting the submission text into user's wiki page
# If it's a linkpost, then _text_ will be the link they submitted.
# This one puts a horizontal line above each post to separate them
# Available injectors are _title_, _permalink_, _text_

MAX_WIKI_SIZE = 499 * 1024
# The apparent character limit for wiki pages
# Going over 499 kb seems to cause http 500 errors

WIKI_PERMLEVEL = 1
# Who can edit this page?
# 0 - Use global wiki settings
# 1 - Use a whitelist of names
# 2 - Only mods can read and see this page

MAXPOSTS = 100
# How many submissions / how many comments to get on each run
# PRAW can get up to 100 in a single call
# I recommend leaving it at 100

MAX_MAILTRIES = 15
# The maximum number of times to attempt sending mail
# in the event of server outage etc.

WAIT = 30
# How many seconds to wait between runs.
# The bot is completely inactive during this time.

''' All done! '''

try:
	import bot
	USERNAME = bot.uG
	PASSWORD = bot.pG
	USERAGENT = bot.aG
except ImportError:
	pass

sql = sqlite3.connect('biowiki.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users(name TEXT, submissions TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS userindex on users(name)')
sql.commit()

print('Logging in %s' % USERNAME)
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD, disable_warning=True)


def get_page_content(pagename):
	subreddit = r.get_subreddit(SUBREDDIT)
	try:
		page = subreddit.get_wiki_page(pagename)
		page = page.content_md
	except praw.errors.NotFound:
		page = ''

	return page

def send_message(recipient, subject, body):
	for x in range(MAX_MAILTRIES):
		try:
			print('\tSending mail')
			return r.send_message(recipient, subject, body)
			return
		except praw.errors.HTTPException as e:
			if isinstance(e, praw.errors.NotFound):
				return
			if isinstance(e, praw.errors.Forbidden):
				return
			time.sleep(20)

def update_wikipage(author, submission, newuser=False):
	'''
	Given a username and Submission object, publish a wiki page
	under their name containing the selftext of the post.
	If the wikipage already exists just put the text underneath
	the current content.
	'''

	print('\tChecking current page')
	content = get_page_content(author)
	if content == '':
		content = WIKI_PAGE_INITIAL_TEXT.replace('_author_', author)
	newtext = WIKI_POST_FORMAT
	newtext = newtext.replace('_title_', submission.title)
	shortlink = 'http://redd.it/%s' % submission.id
	newtext = newtext.replace('_permalink_', shortlink)
	if submission.is_self:
		newtext = newtext.replace('_text_', submission.selftext)
	else:
		newtext = newtext.replace('_text_', submission.url)

	if newtext not in content:
		complete = content + newtext
		if len(complete) > MAX_WIKI_SIZE:
			print('!! Page %s contains too many characters: %d / %d' % (
				   len(complete), MAX_WIKI_SIZE))
			return
	else:
		complete = content

	print('\tUpdating page text')
	subreddit = r.get_subreddit(SUBREDDIT)
	subreddit.edit_wiki_page(author, complete)
	if newuser is True:
		print('\tAssigning permission')
		page = subreddit.get_wiki_page(author)
		page.edit_settings(permlevel=WIKI_PERMLEVEL, listed=True)
		page.add_editor(author)
	return True

def biowikibot():
	'''
	- watch /new queue
	- If a new user is found:
	    - Create his wiki page
	    - Add the Submission's text as the page text
	    - Set permissions for him to edit
	    - PM him with a link to the page
	- If an existing user is found:
	    - Add permalink to the Submission at the bottom of his wiki page.
	    - PM him to notify of the update.
	'''

	print('Checking /r/%s/new' % SUBREDDIT)
	subreddit = r.get_subreddit(SUBREDDIT)
	new = list(subreddit.get_new(limit=MAXPOSTS))
	new.sort(key=lambda x: x.created_utc)

	for submission in new:
		if submission.author is None:
			# Post is deleted. Ignore
			continue

		author = submission.author.name
		cur.execute('SELECT * FROM users WHERE name=?', [author])
		fetch = cur.fetchone()
		
		if fetch is None:
			print('New user: %s' % author)
			posts = submission.fullname
			cur.execute('INSERT INTO users VALUES(?, ?)', [author, posts])
			update_wikipage(author, submission, newuser=True)

			subject = MESSAGE_INITIAL_SUBJECT
			body = MESSAGE_INITIAL_BODY
		else:
			posts = fetch[1].split(',')
			if submission.fullname in posts:
				# Already processed this post. Ignore
				continue
			print('Returning user: %s' % author)
			posts.append(submission.fullname)
			posts = ','.join(posts)
			cur.execute('UPDATE users SET submissions=? WHERE name=?',
						[posts, author])
			update_wikipage(author, submission, newuser=False)

			subject = MESSAGE_UPDATE_SUBJECT
			body = MESSAGE_UPDATE_BODY

		subject = subject.replace('_author_', author)
		body = body.replace('_author_', author)
		shortlink = 'http://redd.it/%s' % submission.id
		body = body.replace('_permalink_', shortlink)
		send_message(author, subject, body)

		sql.commit()


while True:
	try:
		biowikibot()
	except:
		traceback.print_exc()
	
	print('Running again in %d seconds' % WAIT)
	time.sleep(WAIT)