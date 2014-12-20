#/u/GoldenSights
import praw
import time

''' USER CONFIGURATION ''' 

USERNAME  = ""
#This is the bot's Username. In order to send mail,
#it must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does.
#For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts.
#For a single sub, use "sub1".
#For multiple subreddits, use "sub1+sub2+sub3"

MULTI_SUBREDDIT_RANK = True
#If you entered a single subreddit in SUBREDDIT, you can ignore this.
#If you entered multiple:
#	True = Posts are ranked relative to all the subreddits combined
#	False = Each subreddit is managed individually

IGNORE_UNKNOWN = True
#If a post has a flair that is not part of the rank system, should
# we just ignore it?
#If False, that post's flair will be overwritten with a rank.

RANKINGS = {1: "#1 Top poster!",
			5: "Top 5 poster",
			10: "Top 10 poster",
			25: "Top 25 poster",
			50: "Top 50 poster",
			100: "Top 100 poster"}

SEND_MODMAIL = True
#Send subreddit modmail when a post achieves a rank
MODMAIL_SUBJECT = "Automated post ranking"
#The subjectline for the sent modmail
MODMAIL_BODY = """
_username_ has just earned rank _ranktext_ on their
post ["_posttitle_"](_postlink_)
"""

''' All done! '''

# Automatic preparation
RANKINGS_REVERSE = dict(zip(RANKINGS.values(), RANKINGS.keys()))
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

def manageranks():
	for subreddit in SUBREDDIT_L:
		subreddit = r.get_subreddit(subreddit)
		topall = subreddit.get_top_from_all(limit=MAXRANK)
		topall = list(topall)
		for position in range(len(topall)):
			post = topall[position]
			post_flair = post.link_flair_text

def get_rank_from_pos(position):
	''' Given a position in a listing, return the appropriate rank '''
	for rankkey in RANKKEYS:
		if rankkey >= position:
			return RANKINGS[rankkey]