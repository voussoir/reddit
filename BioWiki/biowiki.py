#/u/GoldenSights
import praw
import time
import traceback
import sqlite3

''' USER CONFIG '''

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
# This is a short description of what the bot does. 
# For example "/u/GoldenSights' Newsletter bot to notify of new posts"
SUBREDDIT = "GoldTesting"
# This is the sub or list of subs to scan for new posts. For a single sub, use "sub1".
# For multiple subs, use "sub1+sub2+sub3+...". For all use "all"

MESSAGE_INITIAL_SUBJECT = 'Welcome to /r/_subreddit_, _author_!'
MESSAGE_INITIAL_BODY = '''
Hey _author_,

This is the first time we've seen you post in /r/_subreddit_, welcome!

Your [first submission](_permalink_) has been added to your new bio page
at /r/_subreddit_/wiki/_author_.
'''

MESSAGE_UPDATE_SUBJECT = 'Your /r/_subreddit_ bio has been updated'
MESSAGE_UPDATE_BODY = '''
Hey _author_,

Your [submission](_permalink_) to /r/_subreddit_ has been added
to the bottom of your bio at /r/_subreddit_/wiki/_author_.
'''

MESSAGE_FULL_SUBJECT = 'Your /r/_subreddit_ bio is full!'
MESSAGE_FULL_BODY = '''
Hey _author_,

I attempted to update your bio page at /r/_subreddit_/wiki/_author_,
but found that it was too full for me to add more text!
'''
# The subject and body of the messages you will to send to users.
# If you put _author_ in either one of these texts, it will be automatically
# replaced with their username.
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

WIKI_PERMLEVEL = 1
# Who can edit this page?
# 0 - Use global wiki settings
# 1 - Use a whitelist of names
# 2 - Only mods can read and see this page

MAXPOSTS = 10
# How many submissions / how many comments to get on each run
# PRAW can get up to 100 in a single call

MAX_MAILTRIES = 15
# The maximum number of times to attempt sending mail
# in the event of server outage etc.

WAIT = 30
# How many seconds to wait between runs.
# The bot is completely inactive during this time.

''' All done! '''

try:
	import bot
	USERAGENT = bot.aG
except ImportError:
	pass

sql = sqlite3.connect('biowiki.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users(name TEXT, submissions TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS userindex on users(name)')
sql.commit()

print('Logging in')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)
START_TIME = time.time()

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
	newtext = newtext.replace('_permalink_', submission.short_link)
	if submission.is_self:
		newtext = newtext.replace('_text_', submission.selftext)
	else:
		newtext = newtext.replace('_text_', submission.url)

	if newtext not in content:
		complete = content + newtext
	else:
		complete = content

	print('\tUpdating page text')
	subreddit = r.get_subreddit(SUBREDDIT)
	try:
		subreddit.edit_wiki_page(author, complete)
	except praw.errors.PRAWException as e:
		if e._raw.status_code in [500, 413]:
			print('\tThe bio page for %s is too full!')
			return 'full'
		else:
			raise e
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
		if submission.created_utc < START_TIME:
			# Post made before the bot started. Ignore
			continue
		author = submission.author.name
		cur.execute('SELECT * FROM users WHERE name=?', [author])
		fetch = cur.fetchone()
		
		if fetch is None:
			print('New user: %s' % author)
			posts = submission.fullname
			cur.execute('INSERT INTO users VALUES(?, ?)', [author, posts])
			result = update_wikipage(author, submission, newuser=True)

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
			result = update_wikipage(author, submission, newuser=False)

			subject = MESSAGE_UPDATE_SUBJECT
			body = MESSAGE_UPDATE_BODY

		if result == 'full':
			subject = MESSAGE_FULL_SUBJECT
			body = MESSAGE_FULL_BODY

		subject = subject.replace('_author_', author)
		subject = subject.replace('_subreddit_', SUBREDDIT)
		body = body.replace('_author_', author)
		body = body.replace('_permalink_', submission.short_link)
		body = body.replace('_subreddit_', SUBREDDIT)
		if result is not None:
			send_message(author, subject, body)

		sql.commit()


while True:
	try:
		biowikibot()
	except:
		traceback.print_exc()
	
	print('Running again in %d seconds' % WAIT)
	time.sleep(WAIT)