#/u/GoldenSights
from dateutil.parser import parse as dateparse
import string
import datetime
import time
import praw
import sqlite3
import re

""" USER CONFIG """

USERAGENT = ""
#Describe the bot and what it does. Include your username
USERNAME = "GoldenSights"
#This is the bot's username
PASSWORD = ""
#This is the bot's password
SUBREDDIT = "Goldtesting"
#This is the subreddit where the bot finds the schedules
#It should be private with only the team of moderators
TITLESEPARATOR = "||"
#This is what demarcates the timestamp from the sub from the title
#This should not be a naturally occuring part of any title
#Example: "15 December 2014 ||| GoldTesting ||| Welcome to the subreddit"
#          ^Time to post        ^Sub to post    ^Title of post
POSTEDFLAIR = "Post made!"
#This flair will be assigned to the source when the post is made
MAXPOSTS = 1
#The number of items you want to get from /new. Recommended 100
ALLOWOTHEREDITS = False
#Are users allowed to edit other peoples' post schedules?

POSTEDCOMMENT = "Your post to %s has been created. %s"
#Made in the source when the post is made

FOOTER = """

_____

If any information is incorrect, reply to this comment with the incorrect key,
a colon, and new value. See the
[Bot code](https://github.com/voussoir/reddit/tree/master/Schedulizer-ModTeam)
page for examples. Only make 1 edit per line.


A foolproof time format is 
"DD Monthname YYYY HH:MM". All times are in UTC
([Timezone map](http://www.timeanddate.com/time/map/))

Deleting your post will cause it to be removed from the schedule.

If you think the bot is down, send it
[this message](http://www.reddit.com/message/compose?to=%s&subject=Ping&message=Ping).

"""%USERNAME

SCHEDULECOMMENT = """

Your post has been scheduled. Please check that this information is correct:

"""
#Made in the source when the source is made

ERRORCOMMENT = """

Encountered the following errors:

%s

The post will use placeholder values until you correct the information

"""

DISTINGUISHFAIL = "Attempted to distinguish post and failed."
""" All done! """

try:
	import bot
	#USERNAME = bot.uG
	PASSWORD = bot.pG
	USERAGENT = bot.aG
except ImportError:
	pass

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)

sql = sqlite3.connect('sql.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS schedules(ID TEXT, TIME INT, REDDIT TEXT, TITLE TEXT, DIST INT, STICKY INT, FLAIR TEXT, FLCSS TEXT, POST TEXT)')
#                                                   0         1          2            3          4         5           6           7           *
sql.commit()

def getTime(bool):
	timeNow = datetime.datetime.now(datetime.timezone.utc)
	timeUnix = timeNow.timestamp()
	if bool == False:
		return timeNow
	else:
		return timeUnix

def processpost(inputpost):
	if isinstance(inputpost, str):
		if 't3_' not in inputpost:
			inputpost = 't3_' + inputpost
		inputpost = r.get_info(thing_id=inputpost)
	sourceid = inputpost.id
	print('Schedulizing post ' + sourceid)
	sourcetitle = inputpost.title
	sourcesplit = sourcetitle.split(TITLESEPARATOR)
	errors = []
	critical = False
	dosticky = 0
	dodist = 0
	try:
		posttime = "?"
		postsub = "?"
		posttitle = "?"
		postflair = ""
		postflcss = ""
		posttime = sourcesplit[0]
		postsub = sourcesplit[1]
		postsub = postsub.replace('/r/', '')
		if '[d]' in postsub:
			dodist = 1
		if '[s]' in postsub:
			dosticky = 1
		regex = re.search("\[f:.*\]", postsub)
		if regex:
			regex = regex.group(0)
			postflair = regex
			postflair = postflair[3:-1]
		regex = re.search("\[fc:.*\]", postsub)
		if regex:
			regex = regex.group(0)
			postflcss = regex
			postflcss = postflcss[3:-1]
		elif postflair != "":
			postflcss = removespecial(postflair)

		postsubsplit = postsub.split(' ')
		while '' in postsubsplit:
			postsubsplit.remove('')
		postsub = postsubsplit[0]
		posttitle = sourcesplit[2]
	except IndexError:
		errors.append('! Title: Title expected 3 attributes separated by ' + TITLESEPARATOR)
		critical = True

	try:
		posttimerender = dateparse(posttime)
		posttimerender = posttimerender.replace(tzinfo=datetime.timezone.utc)
		posttimestamp = posttimerender.timestamp()
	except:
		#December 31, 2500
		posttimestamp = 16756704000
		errors.append('! DateTime: Could not understand time format, or date is invalid. You entered: `' + posttime + '`')
		critical = True

	try:
		r.get_subreddit(postsub, fetch=True)
	except:
		errors.append('! Reddit: Subbreddit /r/' + postsub + ' could not be found')
		critical = True

	#ID TEXT, TIME INT, REDDIT TEXT, TITLE TEXT, DIST INT, STICKY INT, FLAIR TEXT, FLCSS TEXT, POST TEXT
	#  0         1          2            3          4         5           6           7           8

	datalist = [sourceid, posttimestamp, postsub, posttitle, dodist, dosticky, postflair, postflcss, "None"]
	cur.execute('SELECT * FROM schedules WHERE ID=?', [sourceid])
	fetch = cur.fetchone()
	if not fetch:
		cur.execute('INSERT INTO schedules VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)', datalist)
		sql.commit()

		schedulecomment = SCHEDULECOMMENT
		if len(errors) > 0:
			errors = "\n\n".join(errors)
			schedulecomment = ERRORCOMMENT % errors
		schedulecomment += buildtable(datalist)
		schedulecomment += FOOTER
		print('Writing comment')
		inputpost.add_comment(schedulecomment)

def updatepost(inputcomment):
	sourceid = comment.link_id
	print('Updating schedule for ' + sourceid + 'via comment ' + comment.id)
	source = r.get_info(thing_id=sourcide)
	pauthor = source.author.name
	cauthor = comment.author.name
	if ALLOWOTHEREDITS or (pauthor == cauthor):
		cur.execute('SELECT * FROM schedules WHERE ID=?', [sourceid])
		data=cur.fetchone()
		if data:
			data= list(data)
			errors = []
			commentsplit = comment.body.split('\n')
			for line in commentsplit:
				line = line.split(':')
				line[0] = line[0].replace(' ', '')

	else:
		print(cauthor + ' may not edit ' + pauthor + "'s post")

def buildtable(inputdata):
	timeobj = datetime.datetime.utcfromtimestamp(inputdata[1])
	inputdata[1] = datetime.datetime.strftime(timeobj, "%B %d %Y %H:%M UTC")
	inputdata[2] = '/r/' + inputdata[2]
	inputdata[3] = '`' + inputdata[3] + '`'
	inputdata[4] = "True" if inputdata[4] == 1 else "False"
	inputdata[5] = "True" if inputdata[5] == 1 else "False"
	inputdata = inputdata[1:-1]
	table = """
	Key | Value
	:- | :-
	Time | {0}
	Subreddit | {1}
	Title | {2}
	Distinguish | {3}
	Sticky | {4}
	Flair-text | {5}
	Flair-CSS | {6}
	""".format(*inputdata)
	return table

def removespecial(inputstr):
	ok = string.ascii_letters + ascii_digits
	outstr = "".join([x for x in inputstr if x in ok])

def manage_new():
	print('Managing ' + SUBREDDIT + '/new')
	subreddit = r.get_subreddit(SUBREDDIT)
	new = list(subreddit.get_new(limit=MAXPOSTS))
	now = getTime(True)
	for post in new:
		pid = post.id
		cur.execute('SELECT * FROM schedules WHERE ID=?', [pid])
		if not cur.fetchone():
			processpost(post)

def manage_unread():
	print('Managing inbox')
	inbox = list(r.get_unread(limit=None))
	for message in inbox:
		if isinstance(message, praw.objects.Message):
			if message.subject.lower() == "ping":
				message.reply("Pong")
		elif isinstance(message, praw.bojects.Comment):
			commentsub = comment.subreddit.display_name
			if commentsub.lower() == SUBREDDIT.lower():
				updatepost(comment)

		message.mark_as_read()
manage_new()