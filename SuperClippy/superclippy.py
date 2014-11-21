#/u/GoldenSights
import traceback
import time
import datetime
import sqlite3
import json
import praw

'''USER CONFIGURATION'''

"""GENERAL"""
USERNAME  = "Clippy_Office_Asst"
# This is the bot's Username. In order to send mail, he must have some amount
# of Karma.
PASSWORD  = ""
# This is the bot's Password. 
# Replace the quotes with `input("Password: ")` to be prompted at startup.
USERAGENT = "/r/Excel Clippy Office Assistant all-in-one moderator."
# This is a short description of what the bot does.
# For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "Excel"
# This is the sub or list of subs to scan for new posts.
# For a single sub, use "sub1".
# For multiple subreddits, use "sub1+sub2+sub3+..."

MAXPOSTS = 100
# How many posts to get from the /new queue at once
WAIT = 30
# The number of seconds between cycles. The bot is completely inactive during
# this time


"""**************"""
"""CLIPPYPOINTS™ """
"""**************"""
POINT_STRING_USR = ["Solution Verified"]
# OP can use this string to award points in his thread.

POINT_STRING_MOD = ["+1 Point"]
# Moderators can use this to give points at any time.

POINT_REPLY = "You have awarded one point to _parent_"
# This is the phrase that User will receive
# _parent_ will be replaced by the username of the Parent.

POINT_EXEMPT = []
# Any usernames in this list will not receive points.
# Perhaps they have special flair.

POINT_OP_ONLY = True
# Is OP the only person who can give points?
# I recommend setting this to False. Other users might have the same question
# and would like to reward a good answer.

POINT_PER_THREAD = 200
#How many points can be distributed in a single thread?

POINT_DO_EXPLAIN = True
# If the max-per-thread is reached and someone tries to give a point, reply to
# them saying that the max has already been reached

POINT_EXPLAIN = """
Sorry, but %d point(s) have already been distributed in this thread.
This is the maximum allowed at this time.
"""%POINT_PER_THREAD
#If EXPLAINMAX is True, this will be said to someone who tries to give a point after max is reached

POINT_EXPLAIN_OP_ONLY = """
Hi!

It looks like you are trying to award a point and you are not the OP!
I am here to assist you!

What would you like help with?

[ClippyPoints^(TM)?](/r/excel/wiki/clippy)

[Flair Descriptions](http://www.reddit.com/r/excel/wiki/index)

"""

"""**************"""
"""FLAIR REMINDER"""
"""**************"""
FLAIR_WARN_DELAY = 86400
# This is the time, IN SECONDS, the user has to reply to the first comment.
# If he does not respond by this time, post is removed

NCDELAY = 172800

FLAIR_WARN_MESSAGE = """
Hi!

It looks like you are trying to ask a question!
Since you have not responded in the last 24 hours, I am here to assist you!

If your questions has been solved, please be sure to update the flair.

Would you like help?

[Help Changing Your
Flair?](https://www.reddit.com/r/excel/wiki/flair)

[Asking Question and Sharing
Data](https://www.reddit.com/r/excel/wiki/sharingquestions)

"""
# This is what the bot tells you when you dont meet the DELAY. Uses reddit's
# usual Markdown formatting

FLAIR_WARN_IGNORE_MODS = False
# Do you want the bot to ignore posts made by moderators?
# Use True or False (With capitals! No quotations!)

FLAIR_WARN_IGNORE_SELF = False
#Do you want the bot to ignore selfposts?

FLAIR_SOLVED = "solved"

FLAIR_UNSOLVED = "unsolved"

FLAIR_WAITING = "Waiting on OP"

FLAIR_DISCUSS = "discussion"

FLAIR_ADVERTISEMENT = "advertisement"

FLAIR_TEMPLATE = "User Template"

FLAIR_PROTIP = "pro tip"

FLAIR_TRIGGERS = ["that works", "perfect", "thank you so much", "huge help",
				  "figured it out", "got it", "thanks for your help"]
#These encourage OP to change flair / award point

FLAIR_REMINDER = """
Hi!

It looks like you received an answer to your question!  Since the top is
still marked as unsolved, I am here to assist you!

If your questions has been solved, please be sure to update the flair.

Would you like help?

[Help Changing Your Flair?](http://www.reddit.com/r/excel/wiki/index)

[Flair Descriptions](http://www.reddit.com/r/excel/wiki/index)

"""


"""***************"""
"""WELCOME MESSAGE"""
"""***************"""
WELCOME_SUBJECT = """Welcome to /r/Excel, I am here to help!"""

WELCOME_MESSAGE = """
Hi %s!

It looks like you are new to posting in /r/Excel.
Did you know we have a few ways to help you recieve better help?

How can I help you?

[How to Share Your Questions](/r/excel/wiki/sharingquestions)

[Changing Link Flair](/r/excel/wiki/flair)

[ClippyPoints^TM](/r/excel/wiki/clippy)

^This ^message ^is ^auto-generated ^and ^is ^not ^monitored ^on ^a
^regular ^basis, ^replies ^to ^this ^message ^may ^not ^go ^answered.
"""


"""****************"""
"""FUNCTION VLOOKUP"""
"""****************"""

DICT_FILE = 'excel.txt'
#The file with the Keys/Values

DICT_RESULT_FORM = "_value_"
#This is the form that the result will take
#You may use _key_ and _value_ to inject the key/value from the dict.
#You may delete one or both of these injectors.

DICT_LEVENSHTEIN = True
#If this is True it will use a function that is slow but can find misspelled keys
#If this is False it will use a simple function that is very fast but can only find keys which are spelled exactly


'''All done!'''


WAITS = str(WAIT)

try:
	import bot
	USERNAME = bot.uG
	PASSWORD = bot.pG
	USERAGENT = bot.aG
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)
del PASSWORD


def flair(subreddit, username):
	#Subreddit must be the sub object, not a string
	#Returns True if the operation was successful
	success = False
	print('\tChecking flair for ' + username)
	flairs = subreddit.get_flair(username)
	flairs = flairs['flair_text']
	if flairs != None and flairs != '':
		print('\t :' + flairs)
		try:
			flairs = int(flairs)
			flairs += 1
			flairs = str(flairs)
			success = True
		except ValueError:
			print('\tCould not convert flair to a number.')
	else:
		print('\tNo current flair. 1 point')
		flairs = '1'
		success = True
	print('\tAssigning Flair: ' + flairs)
	subreddit.set_flair(username, flair_text=flairs, flair_css_class='points')

	return success


def scan():
	print("Scanning " + SUBREDDIT)
	subreddit = r.get_subreddit(SUBREDDIT)
	comments = subreddit.get_comments(limit=MAXPOSTS)
	for comment in comments:
		cid = comment.id
		cur.execute('SELECT * FROM oldposts WHERE ID=?', [cid])
		if not cur.fetchone():
			print(cid)
			cbody = comment.body.lower()
			try:
				if not comment.is_root:
					cauthor = comment.author.name
					
					if (cauthor not in MODERATORS and any(flag.lower() in cbody for flag in PARENTSTRING)) or\
					   (cauthor in MODERATORS and any(flag.lower() in cbody for flag in MODSTRING)):
						print('\tFlagged.')
						print('\tFetching parent and Submission data.')
						parentcom = r.get_info(thing_id=comment.parent_id)
						pauthor = parentcom.author.name
						op = comment.submission.author.name
						opid = comment.submission.id

						if pauthor != cauthor:
							if not any(exempt.laower() == pauthor.lower() for exempt in EXEMPT):
								if OPONLY == False or cauthor == op or cauthor in MODERATORS:
									cur.execute('SELECT * FROM submissions WHERE ID=?', [opid])
									fetched = cur.fetchone()
									if not fetched:
										cur.execute('INSERT INTO submissions VALUES(?, ?)', [opid, 0])
										fetched = 0
									else:
										fetched = fetched[1]

									if fetched < MAXPERTHREAD:
										if flair(subreddit, pauthor):
											print('\tWriting reply')
											comment_confirm = comment.reply(REPLYSTRING.replace('_parent_', pauthor))
											comment_confirm.distinguish()
											cur.execute('UPDATE submissions SET count=? WHERE ID=?', [fetched+1, opid])
									else:
										print('\tMaxPerThread has been reached')
										if EXPLAINMAX == True:
											print('\tWriting reply')
											comment.reply(EXPLAINREPLY)
								else:
									print('\tOther users cannot give points.')
									#comment_confirm = comment.reply(EXPLAINOPONLY)
									#comment_confirm.distinguish()
							else:
								print('\tParent is on the exempt list.')
						else:
							print('\tCannot give points to self.')
				else:
					print('\tRoot comment. Ignoring.')

			except AttributeError:
				print('\tCould not fetch usernames. Cannot proceed.')


			cur.execute('INSERT INTO oldposts VALUES(?)', [cid])
		sql.commit()
