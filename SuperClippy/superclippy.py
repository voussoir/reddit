#/u/GoldenSights
import sys
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

DICT_FILE = 'reference.txt'
#The file with the Keys/Values

DICT_RESULT_FORM = "_value_"
#This is the form that the result will take
#You may use _key_ and _value_ to inject the key/value from the dict.
#You may delete one or both of these injectors.

DICT_LEVENSHTEIN = True
#If this is True it will use a function that is slow but can find misspelled keys
#If this is False it will use a simple function that is very fast but can only find keys which are spelled exactly

DICT_FAIL = """
"Hi!  It looks like you looking for help with an Excel function!
Unfortunately I have not learned that function yet, but will get right on it!"
"""

'''All done!'''


def getTime(bool):
	timeNow = datetime.datetime.now(datetime.timezone.utc)
	timeUnix = timeNow.timestamp()
	if bool == False:
		return timeNow
	else:
		return timeUnix

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()
sql.commit()

class ClippyManager:
	def clippy_manager(self):
		subreddit = r.get_subreddit(SUBREDDIT)
		print('Getting new comments')
		newcomments = subreddit.get_comments()
	def begin(self):
		print('Starting Points...', end="")
		clippypoints = ClippyPoints()
		print('done.')
		print('Starting Welcome...', end="")
		clippywelcome = ClippyWelcome()
		print('done.')
		print('Starting Flair...', end="")
		clippyflair = ClippyFlairReminder()
		print('done.')
		print('Starting Reference...', end="")
		clippyreference = ClippyReference()
		print('done.')

		try:
			import bot
			USERNAME = bot.uG
			PASSWORD = bot.pG
			USERAGENT = bot.aG
		except ImportError:
			pass
		print('Logging in...', end="")
		sys.stdout.flush()
		r = praw.Reddit(USERAGENT)
		r.login(USERNAME, PASSWORD)
		del PASSWORD
		print('Done.')


class ClippyPoints(ClippyManager):
	def incrementflair(subreddit, username):
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


class ClippyFlairReminder(ClippyManager):
	def scan():
		now = datetime.datetime.now()
		print('Scanning ' + SUBREDDIT + ' at ' + str(now))
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
			
			cur.execute('SELECT * FROM flair WHERE id="%s"' % pid)
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
								post.set_flair(flair_text=FLAIRWAITING, flair_css_class="waitingonop")
								
						elif flair == FLAIRWAITING.lower():
							print(pid + ': Waiting')
							for comment in comments:
								try:
									cauthor = comment.author.name
								except AttributeError:
									cauthor = '[deleted]'
								if cauthor == pauthor:
									found = True
									pbody = comment.body.lower()
								else:
									ctimes.append(comment.created_utc)
							if found == True:
								print('\tFound comment by OP. All clear, chaning flair back to unsolved.')
								post.set_flair(flair_text=FLAIRUNSOLVED, flair_css_class="notsolvedcase")
								print('\tUpvoting comment..')
								post.upvote()
								cur.execute('INSERT INTO flair VALUES("%s")' % pid)
								if any(key.lower() in pbody for key in PARENTSTRING):
									print('Replying to ' + pid + ' by ' + pauthor)
									comment.reply(REPLYSTRING)
									newcomment.distinguish()
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
	#                               print('\tRemoving Post')
	#                               post.remove()
									cur.execute('INSERT INTO flair VALUES("%s")' % pid)
								else:
									differences = str('%.0f' % (DELAY - difference))
									print('\tStill has ' + differences + 's.')
							elif found == False and len(ctimes) == 0:
								print('\tNo comments by OP, but no other comments are available.')
	
						else:
							print(pid + ': Neither flair')
							if flair == FLAIRDIS.lower():
								print(pid + ': is a discussion post, adding to ignore list...')
								cur.execute('INSERT INTO flair VALUES("%s")' % pid)
							if flair == FLAIRAD.lower():
								print(pid + ': is an advertisement post, adding to ignore list...')
								cur.execute('INSERT INTO flair VALUES("%s")' % pid)
							if flair == FLAIRUT.lower():
								print(pid + ': is a User Template post, adding to ignore list...')
								cur.execute('INSERT INTO flair VALUES("%s")' % pid)
							if flair == FLAIRPT.lower():
								print(pid + ': is a ProTip post, adding to ignore list...')
								cur.execute('INSERT INTO flair VALUES("%s")' % pid)
							else:
								cur.execute('SELECT * FROM flair WHERE id="%s"' % pid)
								if not cur.fetchone():
									print('\tAssigning Flair')
									post.set_flair(flair_text=FLAIRNULL, flair_css_class="notsolvedcase")
								else:
									#cur.execute('INSERT INTO flair VALUES("%s")' % pid)
	
									if pauthor in mods and IGNOREMODS == True:
										print(pid + ', ' + pauthor + ': Ignoring Moderator')
										cur.execute('INSERT INTO flair VALUES("%s")' % pid)
	
			if post.is_self == True and IGNORESELFPOST == True:
				print(pid + ', ' + pauthor + ': Ignoring Selfpost')
				cur.execute('INSERT INTO flair VALUES("%s")' % pid)
	
			sql.commit()


class ClippyReference(ClippyManager):
	def __init__(self):
		with open(DICT_FILE, 'r') as f:
			self.DICT = json.loads(f.read())
	def levenshtein(s1, s2):
		#Levenshtein algorithm to figure out how close two strings are two each other
		#Courtesy http://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
		if len(s1) < len(s2):
			return levenshtein(s2, s1)
		# len(s1) >= len(s2)
		if len(s2) == 0:
			return len(s1)
		previous_row = range(len(s2) + 1)
		for i, c1 in enumerate(s1):
			current_row = [i + 1]
			for j, c2 in enumerate(s2):
				insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
				deletions = current_row[j] + 1       # than s2
				substitutions = previous_row[j] + (c1 != c2)
				current_row.append(min(insertions, deletions, substitutions))
			previous_row = current_row
		return previous_row[-1]

	def findsuper(comment, tolerance= 1):
		results = []
		used = []
		for itemname in DICT:
			itemlength = len(itemname.split())
			pos = 0
			commentsplit = comment.split()
			#print(commentsplit)
			end = False
			while not end:
				try:
					gram = commentsplit[pos:pos+itemlength]
					gramjoin = ' '.join(gram)
					lev = levenshtein(itemname, gramjoin)
					#print(snakename, gramjoin)
					#print(lev)
					if lev <= tolerance:
						if itemname not in used:
							used.append(itemname)
							result = RESULTFORM
							result = result.replace('_key_', itemname)
							result = result.replace('_value_', DICT[itemname])
							results.append(result)
					pos += 1
					if pos > len(commentsplit):
						end = True
				except IndexError:
					end = True
		return results
	
	def findsimple(comment):
		results = []
		for itemname in DICT:
			if itemname.lower() in comment.lower():
				result = RESULTFORM
				result = result.replace('_key_', itemname)
				result = result.replace('_value_', DICT[itemname])
				results.append(result)
		return results

	def scanSub():
		print('Searching '+ SUBREDDIT + '.')
		subreddit = r.get_subreddit(SUBREDDIT)
		posts = subreddit.get_comments(limit=MAXPOSTS)
		for post in posts:
			results = []
			pid = post.id
			try:
				pauthor = post.author.name
			except AttributeError:
				pauthor = '[DELETED]'
			cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
			if not cur.fetchone():
				if pauthor.lower() != USERNAME.lower():
					pbody = post.body.lower()
				
					if LEVENMODE == True:
						results = findsuper(pbody)
					else:
						results = findsimple(pbody)
					if "clippy: " in pbody.lower() and len(results) == 0:
						#They must have made a request, but we didn't find anything
						results.append()
					
					if len(results) > 0:
							newcomment = COMMENTHEADER
							newcomment += '\n\n' + '\n\n'.join(results) + '\n\n'
							newcomment += COMMENTFOOTER
							print('Replying to ' + pid + ' by ' + pauthor + ' with ' + str(len(results)) + ' items')
							post.reply(newcomment)
				else:
					print('Will not reply to self')
				cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
		sql.commit()


class ClippyWelcome(ClippyManager):
	def scan():
		print('Scanning ' + SUBREDDIT)
		subreddit = r.get_subreddit(SUBREDDIT)
		posts = subreddit.get_new(limit=MAXPOSTS)
		for post in posts:
			try:
				pauthor = post.author.name
			except Exception:
				pauthor = '[deleted]'
			pid = post.id
			plink = post.short_link
			ptime = post.created_utc
			cur.execute('SELECT * FROM oldposts WHERE id=?', [pid])
			if not cur.fetchone():
				cur.execute('SELECT * FROM users WHERE name=?', [pauthor])
				if not cur.fetchone():
					print('Found new user: ' + pauthor)
					cur.execute('INSERT INTO users VALUES(?, ?)', (pauthor, pid))
					r.send_message(pauthor, 'Welcome to /r/Excel, I am here to help!','Hi! ' + pauthor + ',\n\n It looks like you are new to posting in /r/Excel.  Did you know we have a few ways to help you recieve better help?\n\n\n How can I help you?\n\n\n[How to Share Your Questions](/r/excel/wiki/sharingquestions)\n\n[Changing Link Flair](/r/excel/wiki/flair)\n\n[ClippyPoints^TM](/r/excel/wiki/clippy)\n\n\n ^This ^message ^is ^auto-generated ^and ^is ^not ^monitored ^on ^a ^regular ^basis, ^replies ^to ^this ^message ^may ^not ^go ^answered.' , captcha=None)
					sql.commit()
					print('\t' + pauthor + ' has been added to the database.')
					time.sleep(5)
					
			sql.commit()
c = ClippyManager()
c.begin()