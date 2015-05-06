#/u/GoldenSights

import praw
import time
import os
import sys
import sqlite3
import traceback

'''USER CONFIGURATION'''
USERNAME = ""
PASSWORD = ""
USERAGENT = ""

MAXPOSTS = 100
WAIT = 30
ADMIN = "GoldenSights"

MAX_PER_MESSAGE = 20
# Only this many posts may be compiled into a newsletter
# to avoid massive walls of text

MESSAGE_SUBJECT = "Newsletterly"
MESSAGE_SUBSCRIBE = "You have subscribed to /r/%s"
MESSAGE_SUBSCRIBE_ALREADY = "You are already subscribed to /r/%s"
MESSAGE_SUBSCRIBE_FORCE = "You have forcefully added /u/%s to /r/%s"
MESSAGE_SUBREDDIT_FAIL = """
Could not find /r/%s. Make sure it's spelled correctly and is a
public subreddit (Or add /u/Newsletterly as a contributor).
"""
MESSAGE_UNSUBSCRIBE = "You have unsubscribed from /r/%s"
MESSAGE_UNSUBSCRIBE_ALREADY = "You are not currently subscribed to /r/%s"
MESSAGE_UNSUBSCRIBE_FORCE = "You have forcefully removed /u/%s from /r/%s"
MESSAGE_HEADER = "Your subscribed subreddits have had some new posts:"
MESSAGE_POSTFORMAT = "/r/_reddit_ /u/_author_: _title_"
MESSAGE_FOOTER = "\n\n_____\n\n[In operating Newsletterly](http://redd.it/26xset)"
MESSAGE_REPORT_REQUEST = "You have requested a list of your subscriptions:"
MESSAGE_REPORT_ALL = "All Newsletterly subscriptions:"
MESSAGE_REPORT_USER = "Newsletterly subscriptions for /u/%s:"
MESSAGE_TOOLONG = """
Your message was too long. This measure is in place to prevent abuse.

When subscribing to multiple subreddits, use the comma syntax instead of
making new lines.


"""
MESSAGE_MESSAGE_LONG = "This message ended up being too long!"

'''ALL DONE'''

NOSEND = "nosend" in sys.argv
if NOSEND:
	print("NOSEND active!")

try:
	import bot
	USERNAME = bot.uN
	PASSWORD = bot.pN
	USERAGENT = bot.aN
except ImportError:
	pass

WAITS = str(WAIT)

sql = sqlite3.connect('newsletterly.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS oldpostindex ON oldposts(ID)')
cur.execute('CREATE TABLE IF NOT EXISTS subscribers(name TEXT, reddit TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS spool(name TEXT, message TEXT)')
print('Loaded SQL Database')

sql.commit()

print('Logging in')
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 
del PASSWORD

def fetchgenerator():
	while True:
		fetch = cur.fetchone()
		if fetch is None:
			break
		yield fetch

def get_subscription_reddits(user=None, join=True):
	# Get a multi-subreddit ("a+b+c") for user or all users
	if user:
		user = user.lower()
		cur.execute('SELECT * FROM subscribers WHERE LOWER(name)=?', [user])
	else:
		cur.execute('SELECT * FROM subscribers')
	fetch = cur.fetchall()
	fetch = [f[1] for f in fetch]
	fetch = list(set(fetch))
	if not join:
		return fetch
	return "+".join(fetch)

def add_subscription(user, subreddit):
	user = user.lower()
	subreddit = subreddit.lower()
	try:
		subreddit = r.get_subreddit(subreddit, fetch=True).display_name
		cur.execute('SELECT * FROM subscribers WHERE LOWER(name)=? AND LOWER(reddit)=?', 
					[user, subreddit])
		fetch = cur.fetchall()
		if len(fetch) > 0:
			print('\t%s is already subscribed to %s' % (user, subreddit))
			return (MESSAGE_SUBSCRIBE_ALREADY % subreddit)
		else:
			cur.execute('INSERT INTO subscribers VALUES(?, ?)', [user, subreddit])
			sql.commit()
			print('\t%s has subscribed to %s' % (user, subreddit))
			return (MESSAGE_SUBSCRIBE % subreddit)
	except:
		print('\tSubreddit does not exist')
		return (MESSAGE_SUBREDDIT_FAIL % subreddit)

def drop_subscription(user, subreddit):
	user = user.lower()
	subreddit = subreddit.lower()
	if subreddit == 'all':
		cur.execute('DELETE FROM subscribers WHERE LOWER(name)=?', [user])
		return (MESSAGE_UNSUBSCRIBE % subreddit)
	cur.execute('SELECT * FROM subscribers WHERE LOWER(name)=? AND LOWER(reddit)=?', 
				[user, subreddit])
	if cur.fetchone():
		cur.execute('DELETE FROM subscribers WHERE LOWER(reddit)=?', [subreddit])
		sql.commit()
		return (MESSAGE_UNSUBSCRIBE % subreddit)
	else:
		return (MESSAGE_UNSUBSCRIBE_ALREADY % subreddit)

def count_subscriptions():
	cur.execute('SELECT COUNT(*) FROM subscribers')
	count = cur.fetchone()[0]
	return count

def format_post(submission):
	template = MESSAGE_POSTFORMAT
	try:
		submission.xauthor = submission.author.name
	except:
		submission.xauthor = "-deleted-"
	template = template.replace("_reddit_", submission.subreddit.display_name)
	template = template.replace("_author_", submission.xauthor)
	template = template.replace("_title_", submission.title)
	template = template.replace(']', '\]')
	template = template.replace('[', '\[')
	link = 'http://redd.it/' + submission.id
	template = '[' + template + '](' + link + ')'
	return template

def add_to_spool(user, message, nosave=False):
	if isinstance(user, praw.objects.Redditor):
		user = user.name
	user = user.lower()
	cur.execute('SELECT * FROM spool WHERE name=? AND message=?', [user, message])
	if cur.fetchone():
		raise Exception("Message already exists in spool")
	cur.execute('INSERT INTO spool VALUES(?, ?)', [user, message])
	print('\tadded %s to spool' % user)
	if nosave is False:
		sql.commit()

def get_from_spool():
	cur.execute('SELECT ROWID, * FROM spool')
	return cur.fetchone()

def drop_from_spool(spool, nosave=False):
	cur.execute('DELETE FROM spool WHERE ROWID=?', [spool[0]])
	print('\tdropped %s from spool' % spool[1])
	if nosave is False:
		sql.commit()

def manage_spool():
	print('Managing spool')
	if NOSEND:
		return
	while True:
		spoolmessage = get_from_spool()
		if spoolmessage is None:
			break
		rowid = spoolmessage[0]
		user = spoolmessage[1]
		final = spoolmessage[2]
		print('Sending Newsletter to %s' % user)
		try:
			r.send_message(user, MESSAGE_SUBJECT, final, captcha=None)
		except praw.errors.InvalidUser:
			drop_subscription(user, 'all')
			r.send_message(ADMIN, 'invalid user', user, captcha=None)
		drop_from_spool(spoolmessage)
		sql.commit()

def manage_inbox():
	print('Checking Inbox')
	pms = list(r.get_unread(limit=None))
	# Remove unread from cache to guarantee every fetch is fresh.
	r.evict(r.config['unread'] + '.json')
	for pm in pms:
		pm.mark_as_read()
		interpretation = interpret_message(pm)
		if interpretation:
			print('\tReplying...')
			pm.reply(interpretation)

def manage_posts():
	print('Finding posts')
	usersubs = {}
	cur.execute('SELECT * FROM subscribers')
	for user in fetchgenerator():
		name = user[0].lower()
		sub = user[1]
		if name not in usersubs:
			usersubs[name] = set()
		usersubs[name].add(sub)

	postlist = set()
	for user in usersubs:
		# In this first block, go through each subscriber and get posts on their
		# subreddits. Reassign the results of this scan to the usersubs dict.
		# If a server timeout causes this portion to crash, nothing
		# of value is lost because we don't send mail or write to the db yet,
		# so no duplicate mail will be created.
		subreddits = '+'.join(usersubs[user])
		print('Finding posts for %s' % user)
		print('\t/r/' + subreddits)
		subreddit = r.get_subreddit(subreddits)
		posts = list(subreddit.get_new(limit=MAXPOSTS))
		results = []
		for post in posts:
			cur.execute('SELECT * FROM oldposts WHERE id=?', [post.id])
			if not cur.fetchone():
				postlist.add(post.id)
				if len(results) < MAX_PER_MESSAGE:
					print('\t' + post.id)
					results.append(post)
		results = [format_post(f) for f in results]
		usersubs[user] = results

	for postid in postlist:
		cur.execute('INSERT INTO oldposts VALUES(?)', [postid])
	sql.commit()
	print()
	for user in usersubs:
		# In this second block, use the subscription results to construct a PM
		# and insert the PM to the spool to be sent later. By spooling the messages,
		# we make sure that no api errors cause us to lose any results.
		if len(results) > 0:
			final = MESSAGE_HEADER + '\n\n'
			final += '\n\n'.join(results)
			final += '\n\n' + MESSAGE_FOOTER
			if NOSEND:
				print('%s NO SEND' % user)
			else:
				add_to_spool(user, final, nosave=True)
				sql.commit()
		else:
			print('%s None' % user)

def interpret_message(pm):
	results = []
	author = pm.author.name
	bodysplit = pm.body.lower()
	bodysplit = bodysplit.split('\n\n')
	if len(bodysplit) > 10:
		results = MESSAGE_TOOLONG + MESSAGE_FOOTER
		return results
	for line in bodysplit:
		linesplit = line.replace(', ', ' ')
		linesplit = linesplit.replace(',', ' ')
		linesplit = linesplit.split(' ')
		try:
			command = linesplit[0]
			command = command.replace(',', '')
			command = command.replace(' ', '')
		except IndexError:
			continue
		args = linesplit[1:]
		if command in ['report', 'reportall', 'kill']:
			args = [""]

		for argument in args:
			argument = argument.replace(',', '')
			argument = argument.replace(' ', '')
			print("%s : %s - %s" % (author, command, argument))

			if command == 'report':
				status = MESSAGE_REPORT_REQUEST + '\n\n'
				status += build_report(author)
				results.append(status)

			elif command == 'reportall' and author == ADMIN:
				status = MESSAGE_REPORT_ALL + '\n\n'
				status += build_report(None, supermode=True)
				results.append(status)

			elif command == 'kill' and author == ADMIN:
				pm.mark_as_read()
				r.send_message(ADMIN, "force kill", "bot is being turned off")
				quit()

			if not argument:
				# If we've reached an argument-based function with
				# no argument, skip to the next arg.
				continue

			if command == 'subscribe':
				status = add_subscription(author, argument)
				results.append(status)

			elif command == 'unsubscribe':
				status = drop_subscription(author, argument)
				results.append(status)

			elif command == 'reportuser' and author == ADMIN:
				status = (MESSAGE_REPORT_USER % argument) + '\n\n'
				status += build_report(argument)
				results.append(status)

			elif command == 'forcesubscribe' and author == ADMIN:
				argument = argument.split('.')
				user = argument[0]
				subreddit = argument[1]
				add_subscription(user, subreddit)
				status = (MESSAGE_SUBSCRIBE_FORCE % (user, subreddit)) + '\n\n'
				results.append(status)

			elif command == 'forceunsubscribe' and author == ADMIN:
				argument = argument.split('.')
				user = argument[0]
				subreddit = argument[1]
				drop_subscription(user, subreddit)
				status = (MESSAGE_UNSUBSCRIBE_FORCE % (user, subreddit)) + '\n\n'
				results.append(status)

	if len(results) > 0:
		results = '\n\n_____\n\n'.join(results)
		if len(results) > 9900:
			results = results[:9900]
			results += '\n\n' + MESSAGE_MESSAGE_LONG
		results += MESSAGE_FOOTER
		return results
	return None

def build_report(user, supermode=False):
	if isinstance(user, str):
		userlist = [user]
	results = []
	if supermode:
		cur.execute('SELECT * FROM subscribers')
		fetch = cur.fetchall()
		fetch = [f[0].lower() for f in fetch]
		userlist = list(set(fetch))
		status = get_subscription_reddits(None, join=True)
		status = "ALL REDDITS: /r/" + status + '\n\n'
		results.append(status)
	for user in userlist:
		status = get_subscription_reddits(user, join=False)
		status.append('+'.join(status))
		status = ['/r/' + f for f in status]
		status[-1] = "All: " + status[-1]
		status = '\n\n'.join(status)
		if supermode:
			status = '/u/' + user + '\n\n' + status + '\n\n&nbsp;\n\n'
		results.append(status)
	results = '\n\n'.join(results)
	return results

while True:
	try:
		manage_inbox()
		print('--')
		manage_posts()
		print('--')
		manage_spool()
		print('--')
	except Exception:
		traceback.print_exc()
	print('%d active subscriptions' % count_subscriptions())
	print('Sleeping %s seconds\n\n\n' % WAITS)
	time.sleep(WAIT)