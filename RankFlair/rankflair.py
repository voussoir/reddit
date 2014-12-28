#/u/GoldenSights
import praw
import time
import traceback

''' USER CONFIGURATION ''' 

USERNAME  = ""
#This is the bot's Username. In order to send mail,
#it must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does.
#For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "Goldtesting"
#This is the sub or list of subs to scan for new posts.
#For a single sub, use "sub1".
#For multiple subreddits, use "sub1+sub2+sub3"
WAIT = 30
#The number of seconds between cycles. Bot is completely inactive during
#this time.

MULTI_SUBREDDIT_RANK = False
#If you entered a single subreddit in SUBREDDIT, you can ignore this.
#If you entered multiple:
#	True = Posts are ranked relative to all the subreddits combined
#	False = Each subreddit is managed individually

IGNORE_UNKNOWN = True
#If a post has a flair that is not part of the rank system, should
# we just ignore it?
#If False, that post's flair will be overwritten with a rank!

RANKINGS = {1: "#1 Top poster!",
			5: "Top 5 poster",
			10: "Top 10 poster",
			25: "Top 25 poster",
			50: "Top 50 poster",
			100: "Top 100 poster"}
#Flair text

RANKINGCSS = {1: "toprank",
			  5: "fiverank",
			  10: "tenrank",
			  25: "twfiverank",
			  50: "fiftyrank",
			  100: "hundredrank"}
#Flair CSS class. Use empty quotes if you don't have any.

SEND_MODMAIL = True
#Send subreddit modmail when a post achieves a rank
MODMAIL_SUBJECT = "Automated post ranking system"
#The subjectline for the sent modmail
MODMAIL_BODY = """
_username_ has just earned rank _ranktext_ on their
post ["_posttitle_"](_postlink_)
"""
#This is the modmail message
#Post information can be insterted into the message with these injectors
# _posttitle_ : Post title
# _postid_    : Post ID number
# _postlink_  : Post permalink
# _ranktext_  : Rank text
# _rankvalue_ : Rank value
# _username_  : Post author
#If you would like more injectors, please message me.

''' All done! '''

# Automatic preparation
RANKINGS_REVERSE = {}
for key in RANKINGS:
	val = RANKINGS[key].lower()
	RANKINGS_REVERSE[val] = key

RANKKEYS = sorted(list(RANKINGS.keys()))
MAXRANK = RANKKEYS[-1]

if MULTI_SUBREDDIT_RANK or '+' not in SUBREDDIT:
	SUBREDDIT_L = [SUBREDDIT]
else:
	SUBREDDIT_L = SUBREDDIT.split('+')

try:
	import bot
	USERNAME = bot.uG
	PASSWORD = bot.pG
	USERAGENT = bot.aG
except ImportError:
    pass
# /Automatic preparation

print('Logging in')
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)
del PASSWORD

def manageranks():
	''' Do it. Do it now. '''
	for subreddit in SUBREDDIT_L:
		print('Getting posts from ' + subreddit)
		subreddit = r.get_subreddit(subreddit)
		topall = subreddit.get_top_from_all(limit=MAXRANK)
		topall = list(topall)
		for position in range(len(topall)):
			post = topall[position]
			position += 1
			# Add 1 because indices start at 0
			print(post.id)
			
			actual_flair = post.link_flair_text
			suggested = get_rank_from_pos(position)
			suggested_rank = suggested[0]
			suggested_flair = suggested[1]
			suggested_css = RANKINGCSS[suggested_rank]

			if flair_is_better(new=suggested_flair, old=actual_flair):
				print('\tSetting flair: %s' % suggested_flair)
				post.set_flair(flair_text=suggested_flair,
							   flair_css_class=suggested_css)
				if SEND_MODMAIL:
					compose_modmail(post, suggested_flair, suggested_rank)
					pass

def get_rank_from_pos(position):
	''' Given a position in a listing, return the appropriate rank '''
	for rankkey in RANKKEYS:
		if rankkey >= position:
			return [rankkey, RANKINGS[rankkey]]

def flair_is_better(new, old):
	''' compare whether the newer flair is better than the older flair '''
	if old == "" or old is None:
		#Post has no flair yet. Anything is better
		return True

	newrank = RANKINGS_REVERSE[new.lower()]
	try:
		oldrank = RANKINGS_REVERSE[old.lower()]
	except KeyError:
		if IGNORE_UNKNOWN:
			print('\t"%s" is not a recognized rank. Ignoring' % old)
			return False
		print('\t"%s" is not a recognized rank. Overwriting' % old)
		return True

	print('\tN:%d, O:%d' % (newrank, oldrank))
	if newrank < oldrank:
		print('\tBetter')
		return True
	print('\tNot better')
	return False

def compose_modmail(post, new, newrank):
	print('\tWriting modmail')
	subreddit = '/r/' + post.subreddit.display_name
	try:
		author = post.author.name
	except AttributeError:
		author = "[deleted]"

	message = MODMAIL_BODY
	message = message.replace('_posttitle_', post.title)
	message = message.replace('_postid_', post.id)
	message = message.replace('_postlink_', post.short_link)
	message = message.replace('_ranktext_', new)
	message = message.replace('_rankvalue_', str(newrank))
	message = message.replace('_username_', author)

	r.send_message(subreddit, MODMAIL_SUBJECT, message)


while True:
	try:
		manageranks()
	except Exception:
		traceback.print_exc()
	print('Sleeping %d seconds\n' % WAIT)
	time.sleep(WAIT)