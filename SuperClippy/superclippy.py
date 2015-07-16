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
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = "/r/Excel Clippy Office Assistant all-in-one moderator."
# This is a short description of what the bot does.
# For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "Goldtesting"
# This is the sub or list of subs to scan for new posts.
# For a single sub, use "sub1".
# For multiple subreddits, use "sub1+sub2+sub3+..."
PLAY_BOOT_SOUND = True
#Play boot.wav

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

POINT_FLAIR_CSS = "points"
# The CSS class associated with point flair
# Set to "" for none

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
# How many points can be distributed in a single thread?

POINT_DO_EXPLAIN = True
# If the max-per-thread is reached and someone tries to give a point, reply to
# them saying that the max has already been reached

POINT_EXPLAIN = """
Sorry, but %d point(s) have already been distributed in this thread.
This is the maximum allowed at this time.
"""%POINT_PER_THREAD
# If EXPLAINMAX is True, this will be said to someone who tries to give a
# point after max is reached

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

FLAIR_IGNORE_MODS = False
# Do you want the bot to ignore posts made by moderators?
# Use True or False (With capitals! No quotations!)

FLAIR_IGNORE_SELF = False
#Do you want the bot to ignore selfposts?

FLAIR_SOLVED = "solved"

FLAIR_UNSOLVED = "unsolved"

FLAIR_CHAL = "challenge"

FLAIR_MANN = "Mod Announcement"

FLAIR_MNEWS = "Mod News"

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


"""******************"""
"""FUNCTION REFERENCE"""
"""******************"""

DICT_TRIGGER = "clippy: "
# The trigger phrase for perfoming a lookup

DICT_FILE = 'reference.txt'
# The file with the Keys/Values

DICT_RESULT_FORM = "_value_"
# This is the form that the result will take
# You may use _key_ and _value_ to inject the key/value from the dict.
# You may delete one or both of these injectors.

DICT_LEVENSHTEIN = False
# If this is True it will use a function that is slow but can find
# misspelled keys
# If this is False it will use a simple function that is very fast but can
# only find keys which are spelled exactly

DICT_FAIL = """
Hi!  It looks like you're looking for help with an Excel function!
Unfortunately I have not learned that function yet. If you'd like to
change that, [message the
moderators](http://www.reddit.com/message/compose?to=%2Fr%2Fexcel)!
"""
# The comment which is created when a function is requested
# but not in the file


"""***************"""
"""WELCOME MESSAGE"""
"""***************"""

WELCOME_SUBJECT = """Welcome to /r/Excel, I am here to help!"""

WELCOME_MESSAGE = """
Hi %s!

It looks like you are new to posting in /r/Excel.
Did you know we have a few ways to help you receive better help?

How can I help you?

[How to Share Your Questions](/r/excel/wiki/sharingquestions)

[Changing Link Flair](/r/excel/wiki/flair)

[ClippyPoints^TM](/r/excel/wiki/clippy)

^This ^message ^is ^auto-generated ^and ^is ^not ^monitored ^on ^a
^regular ^basis, ^replies ^to ^this ^message ^may ^not ^go ^answered.
^Remember ^to [^contact ^the
^moderators](http://www.reddit.com/message/compose?to=%2Fr%2Fexcel)
^to ^guarantee ^a ^response
"""
# Sent to the user if he has created his first post in the subreddit

'''All done!'''


class ClippyPoints:
	def incrementflair(self, subreddit, username):
		#Returns True if the operation was successful
		if isinstance(subreddit, str):
			subreddit = r.get_subreddit(subreddit)
		success = False
		print('\t\tChecking flair for ' + username)
		flairs = subreddit.get_flair(username)
		flairs = flairs['flair_text']
		if flairs != None and flairs != '':
			print('\t\t:' + flairs)
			try:
				flairs = int(flairs)
				flairs += 1
				flairs = str(flairs)
				success = True
			except ValueError:
				print('\t\tCould not convert flair to a number.')
		else:
			print('\t\tNo current flair. 1 point')
			flairs = '1'
			success = True
		if success:
			print('\t\tAssigning Flair: ' + flairs)
			subreddit.set_flair(username, flair_text=flairs,
								flair_css_class=POINT_FLAIR_CSS)
		return success

	def receive(self, comments):
		print('\tClippyPoints received comments.')
		subreddit = r.get_subreddit(SUBREDDIT)
		for comment in comments:
			cid = comment.id
			cur.execute('SELECT * FROM clippy_points WHERE ID=?', [cid])
			if not cur.fetchone():
				print(cid)
				cbody = comment.body.lower()
				try:
					if not comment.is_root:
						cauthor = comment.author.name
						print('\tChecking subreddit moderators')
						moderators = [user.name for user in subreddit.get_moderators()]
						byuser = False
						if cauthor not in moderators and any(flag.lower() in cbody for flag in POINT_STRING_USR):
							byuser = True
						if byuser or (
						(cauthor in moderators and any(flag.lower() in cbody for flag in POINT_STRING_MOD))):
							print('\tFlagged %s.' % cid)
							print('\t\tFetching parent and Submission data.')
							parentcom = r.get_info(thing_id=comment.parent_id)
							pauthor = parentcom.author.name
							op = comment.submission.author.name
							opid = comment.submission.id
							if pauthor != cauthor:
								if not any(exempt.lower() == pauthor.lower() for exempt in POINT_EXEMPT):
									if POINT_OP_ONLY == False or cauthor == op or cauthor in moderators:
										cur.execute('SELECT * FROM clippy_points_s WHERE ID=?', [opid])
										fetched = cur.fetchone()
										if not fetched:
											cur.execute('INSERT INTO clippy_points_s VALUES(?, ?)', [opid, 0])
											fetched = 0
										else:
											fetched = fetched[1]
	
										if fetched < POINT_PER_THREAD:
											if self.incrementflair(subreddit, pauthor):
												print('\t\tWriting reply')
												comment_confirm = comment.reply(POINT_REPLY.replace('_parent_', pauthor))
												comment_confirm.distinguish()
												cur.execute('UPDATE clippy_points_s SET count=? WHERE ID=?', [fetched+1, opid])
											if byuser:
												comment.submission.set_flair(flair_text=FLAIR_SOLVED, flair_css_class="solvedcase")
										else:
											print('\t\tMaxPerThread has been reached')
											if EXPLAINMAX == True:
												print('\t\tWriting reply')
												comment.reply(POINT_EXPLAIN)
									else:
										print('\tOther users cannot give points.')
										#comment_confirm = comment.reply(EXPLAINOPONLY)
										#comment_confirm.distinguish()
								else:
									print('\t\tParent is on the exempt list.')
							else:
								print('\t\tCannot give points to self.')
					else:
						print('\t\tRoot comment. Ignoring.')
				except AttributeError:
					print('\t\tCould not fetch usernames. Cannot proceed.')
				cur.execute('INSERT INTO clippy_points VALUES(?)', [cid])
			sql.commit()
		print('\tClippyPoints finished')


class ClippyFlairReminder:
	def receive(self, posts):
		print('\tClippyFlair received submissions')
		now = datetime.datetime.now()
		subreddit = r.get_subreddit(SUBREDDIT)
		print('\tChecking subreddit moderators')
		moderators = [user.name for user in subreddit.get_moderators()]
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
			
			cur.execute('SELECT * FROM clippy_flair WHERE id=?', [pid])
			if not cur.fetchone():
				if post.is_self == False or FLAIR_IGNORE_SELF == False:
					if pauthor not in moderators or FLAIR_IGNORE_MODS == False:
						comments = praw.helpers.flatten_tree(post.comments)
	
						try:
							flair = post.link_flair_text.lower()
						except AttributeError:
							flair = ''
						
						if flair == FLAIR_UNSOLVED.lower():
							print(pid + ': Unsolved')
							for comment in comments:
								try:
									cauthor = comment.author.name
									
								except AttributeError:
									cauthor = '[deleted]'
								if cauthor != pauthor:
									found = True
									break
							if not found:
								print('\tNo comments by another user. No action taken.')
							else:
								print('\tFound comment by other user. Marking as Waiting.')
								post.set_flair(flair_text=FLAIR_WAITING, flair_css_class="waitingonop")
								
						elif flair == FLAIR_WAITING.lower():
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
								if not any(trigger in pbody for trigger in POINT_STRING_USR):
									print('\tFound comment by OP. All clear, changing flair back to unsolved.')
									post.set_flair(flair_text=FLAIR_UNSOLVED, flair_css_class="notsolvedcase")
									#print('\tUpvoting comment..')
									#post.upvote()
									cur.execute('INSERT INTO clippy_flair VALUES(?)', [pid])
									if any(key.lower() in pbody for key in FLAIR_TRIGGERS):
										print('Replying to ' + pid + ' by ' + pauthor)
										comment.reply(FLAIR_REMINDER)
										newcomment.distinguish()
							elif found == False and len(ctimes) > 0:
								print('\tNo comments by OP. Checking time limit.')
								ctime = min(ctimes)
								difference = curtime - ctime
								if difference > FLAIR_WARN_DELAY:
									print('\tTime is up.')
									print('\tLeaving Comment')
									newcomment = post.add_comment(FLAIR_WARN_MESSAGE)
									print('\tDistinguishing Comment')
									newcomment.distinguish()
									cur.execute('INSERT INTO clippy_flair VALUES(?)', [pid])
								else:
									differences = str('%.0f' % (FLAIR_WARN_DELAY - difference))
									print('\tStill has ' + differences + 's.')
							elif found == False and len(ctimes) == 0:
								print('\tNo comments by OP, but no other comments are available.')
	
						else:
							print(pid + ': Neither flair')
							if flair == FLAIR_DISCUSS.lower():
								print(pid + ': is a discussion post, adding to ignore list...')
								cur.execute('INSERT INTO clippy_flair VALUES(?)', [pid])
							if flair == FLAIR_ADVERTISEMENT.lower():
								print(pid + ': is an advertisement post, adding to ignore list...')
								cur.execute('INSERT INTO clippy_flair VALUES(?)', [pid])
							if flair == FLAIR_TEMPLATE.lower():
								print(pid + ': is a User Template post, adding to ignore list...')
								cur.execute('INSERT INTO clippy_flair VALUES(?)', [pid])
							if flair == FLAIR_PROTIP.lower():
								print(pid + ': is a ProTip post, adding to ignore list...')
								cur.execute('INSERT INTO clippy_flair VALUES(?)', [pid])
							if flair == FLAIR_SOLVED.lower():
								print(pid + ': is a SOLVED post, adding to ignore list...')
								cur.execute('INSERT INTO clippy_flair VALUES(?)', [pid])
							if flair == FLAIR_MANN.lower():
								print(pid + ': is a Mod Annoucement post, adding to ignore list...')
								cur.execute('INSERT INTO clippy_flair VALUES(?)', [pid])
							if flair == FLAIR_MNEWS.lower():
								print(pid + ': is a Mod News post, adding to ignore list...')
								cur.execute('INSERT INTO clippy_flair VALUES(?)', [pid])
							else:
								cur.execute('SELECT * FROM clippy_flair WHERE id=?', [pid])
								if not cur.fetchone():
									print('\tAssigning Flair')
									post.set_flair(flair_text=FLAIR_UNSOLVED, flair_css_class="notsolvedcase")
								else:
									#cur.execute('INSERT INTO flair VALUES("%s")' % pid)
	
									if pauthor in moderators and FLAIR_IGNORE_MODS == True:
										print(pid + ', ' + pauthor + ': Ignoring Moderator')
										cur.execute('INSERT INTO clippy_flair VALUES(?)', [pid])
	
			if post.is_self == True and FLAIR_IGNORE_SELF == True:
				print(pid + ', ' + pauthor + ': Ignoring Selfpost')
				cur.execute('INSERT INTO clippy_flair VALUES(?)', [pid])
	
			sql.commit()
		print('\tClippyFlair finished')


class ClippyReference:
	def __init__(self):
		with open(DICT_FILE, 'r') as f:
			self.DICT = json.loads(f.read())
	def levenshtein(self, s1, s2):
		#Levenshtein algorithm to figure out how close two strings are two each other
		#Courtesy http://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
		if len(s1) < len(s2):
			return self.levenshtein(s2, s1)
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

	def findsuper(self, comment, tolerance= 1):
		results = []
		used = []
		for itemname in self.DICT:
			itemlength = len(itemname.split())
			pos = 0
			commentsplit = comment.split()
			end = False
			while not end:
				try:
					gram = commentsplit[pos:pos+itemlength]
					gramjoin = ' '.join(gram)
					lev = self.levenshtein(itemname, gramjoin)
					if lev <= tolerance:
						if itemname not in used:
							used.append(itemname)
							result = DICT_RESULT_FORM
							result = result.replace('_key_', itemname)
							result = result.replace('_value_', self.DICT[itemname])
							results.append(result)
					pos += 1
					if pos > len(commentsplit):
						end = True
				except IndexError:
					end = True
		return results
	
	def findsimple(self, comment):
		results = []
		for itemname in self.DICT:
			if itemname.lower() in comment.lower():
				result = DICT_RESULT_FORM
				result = result.replace('_key_', itemname)
				result = result.replace('_value_', self.DICT[itemname])
				results.append(result)
		return results

	def receive(self, comments):
		lev = "True" if DICT_LEVENSHTEIN else "False"
		print('\tClippyReference received comments (Lev: %s)'%lev)
		for comment in comments:
			results = []
			cid = comment.id
			try:
				cauthor = comment.author.name
				cur.execute('SELECT * FROM clippy_reference WHERE ID=?',[cid])
				if not cur.fetchone():
					print('\t' + cid)
					if cauthor.lower() != r.user.name.lower():
						cbody = comment.body.lower()
					
						if DICT_LEVENSHTEIN == True:
							results = self.findsuper(cbody)
						else:
							results = self.findsimple(cbody)
						if DICT_TRIGGER.lower() in cbody.lower() and (
							len(results) == 0):
							#They made a request, but we didn't find anything
							results.append(DICT_FAIL)
						
						if len(results) > 0:
								newcomment = '\n\n'.join(results)
								print('\t\tReplying to %s with %d items...'%
									(cauthor, len(results)), end="")
								sys.stdout.flush()
								comment.reply(newcomment)
								print('done.')
					else:
						#Will not reply to self
						pass
					cur.execute('INSERT INTO clippy_reference VALUES(?)',[cid])
				sql.commit()
			except AttributeError:
				# Comment Author is deleted
				pass
		print('\tClippyReference finished')


class ClippyWelcome:
	def receive(self, posts):
		print('\tClippyWelcome received submissions')
		for post in posts:
			try:
				pauthor = post.author.name
				pid = post.id
				cur.execute('SELECT * FROM clippy_welcome WHERE NAME=?', [pauthor])
				if not cur.fetchone():
					print('\t' + pid)
					print('\t\tFound new user: ' + pauthor)
					print('\t\tSending message...', end="")
					sys.stdout.flush()
					#r.send_message(pauthor, WELCOME_SUBJECT, WELCOME_MESSAGE%pauthor, captcha=None)
					cur.execute('INSERT INTO clippy_welcome VALUES(?, ?)', (pauthor, pid))
					print('done.')
				sql.commit()
			except AttributeError:
				#Post author is deleted
				pass
		print('\tClippyWelcome finished')



def getTime(bool):
	timeNow = datetime.datetime.now(datetime.timezone.utc)
	timeUnix = timeNow.timestamp()
	if bool == False:
		return timeNow
	else:
		return timeUnix

def clippy_manager():
	try:
		subreddit = r.get_subreddit(SUBREDDIT)
		print('Getting new comments')
		newcomments =list( subreddit.get_comments(limit=MAXPOSTS))
		clippyreference.receive(newcomments)
		clippypoints.receive(newcomments)
		print('Getting new submissions')
		newposts = list(subreddit.get_new(limit=MAXPOSTS))
		clippywelcome.receive(newposts)
		clippyflair.receive(newposts)
	except Exception:
		traceback.print_exc()

if __name__ == "__main__":
	sql = sqlite3.connect('superclippy.db')
	cur = sql.cursor()
	cur.execute('CREATE TABLE IF NOT EXISTS clippy_welcome(NAME TEXT, ID TEXT)')
	cur.execute('CREATE TABLE IF NOT EXISTS clippy_reference(ID TEXT)')
	cur.execute('CREATE TABLE IF NOT EXISTS clippy_points(ID TEXT)')
	cur.execute('CREATE TABLE IF NOT EXISTS clippy_points_s(ID TEXT, count INT)')
	cur.execute('CREATE TABLE IF NOT EXISTS clippy_flair(id TEXT)')
	print('Loaded SQL Database')
	sql.commit()
	
	if PLAY_BOOT_SOUND:
		try:
			import winsound
			import threading
			def bootsound():
				winsound.PlaySound('boot.wav', winsound.SND_FILENAME)
			soundthread = threading.Thread(target=bootsound)
			soundthread.daemon = True
			soundthread.start()
		except Exception:
			pass
	print('Logging in...', end="")
	try:
		import bot
		USERAGENT = bot.aG
	except ImportError:
		pass
	sys.stdout.flush()
	r = praw.Reddit(USERAGENT)
	r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
	r.refresh_access_information(APP_REFRESH)
	print('done.')
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
	while True:
		clippy_manager()
		print('Sleeping %d seconds.\n\n'%WAIT)
		time.sleep(WAIT)
