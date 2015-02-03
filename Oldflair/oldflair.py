#/u/GoldenSights
import traceback
import praw
import time
import datetime

''' USER CONFIGURATION '''

USERNAME = ""
# This is the bot's username. Must be a moderator of the subreddit
PASSWORD = ""
# This is the bot's password. See github.com/voussoir/reddit to see
# alternative options than putting the pw in this file
USERASGENT = ""
# This is a description of what your bot is doing. Include your username
# and be complete

SUBREDDIT = "randomactsofcards"
# The subreddit on which to operate

MINIMUM_AGE = 30 * 24 * 60 * 60
# The number of SECONDS in age for the post to receive oldflair
# The above multiplication is 30 days.
OLDFLAIR_TEXT = "Fulfilled"
OLDFLAIR_CSS_CLASS = "fulfilled"
# The text and css class for the flair which you will assign

OLDFLAIR_COMMENT = """
Your post is 30 days old, was it ever fulfilled?

Line 2,

Line 3, etc etc.
"""
# This comment will be left on the post when it is oldflaired
# Make the quotes empty "" if you don't want to leave a comment

BLACKLIST = ["[Thank You]", "Fulfilled", "thanks"]
# This is a list of phrases that, if they are found in the flair
# OR THE TITLE will cause the post to be skipped from the process
# Letter casing does not matter

WAIT = 120
# The number of seconds between cycles.
# The bot is completely inactive during this time

''' All done! '''



try:
	import bot
	# A file in my library with a password so it's not in this file
	USERNAME = bot.uG
	PASSWORD = bot.pG
	USERAGENT = bot.aG
except ImportError:
	pass

print('Logging in to reddit')
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)
del PASSWORD



def oldflair():
	print('Getting submissions for %s' % SUBREDDIT)
	subreddit = r.get_subreddit(SUBREDDIT)
	submissions = subreddit.get_new(limit=1000)
	nowstamp = datetime.datetime.now(datetime.timezone.utc)
	nowstamp = nowstamp.timestamp()

	for submission in submissions:
		sid = submission.id
		timedif = nowstamp - submission.created_utc
		print('Checking %s: ' % sid, end="")
		if timedif > MINIMUM_AGE:
			sflair_text = submission.link_flair_text
			sflair_text = sflair_text.lower() if sflair_text else ''
			sflair_css = submission.link_flair_css_class
			sflair_css = sflair_css.lower() if sflair_css else ''
			stitle = submission.title.lower()
			checks = [sflair_text, sflair_css, stitle]
			if sflair_text != OLDFLAIR_TEXT.lower() and sflair_css != OLDFLAIR_CSS_CLASS.lower():
				if not any(blacklist.lower() in checks for blacklist in BLACKLIST):
					print()
					print('\tAssigning oldflair')
					#submission.set_flair(flair_text=OLDFLAIR_TEXT, flair_css_class=OLDFLAIR_CSS_CLASS)
					if OLDFLAIR_COMMENT:
						print('\tWriting comment')
						#oldcomment = submission.add_comment(OLDFLAIR_COMMENT)
						print('\tDistinguishing comment')
						#oldcomment.distinguish()
				else:
					print('Contains blacklisted phrase')
			else:
				print('All good')
		else:
			remaining = MINIMUM_AGE - timedif
			print('Too young. %s remain' % format_seconds_to_hhmmss(remaining))

def format_seconds_to_hhmmss(seconds):
	'''
	Thank you Glenn Maynard of Stack Overflow 
	http://stackoverflow.com/a/1384506
	'''
	hours = seconds // (60*60)
	seconds %= (60*60)
	minutes = seconds // 60
	seconds %= 60
	return "%02i:%02i:%02i" % (hours, minutes, seconds)

while True:
	try:
		oldflair()
	except Exception:
		traceback.print_exc()
		print('Sleeping 20 additional seconds')
		time.sleep(20)
	print('Sleeping %d seconds' % WAIT)
	time.sleep(WAIT)