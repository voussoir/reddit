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
MESSAGE_UNSUSBSCRIBE = "You have unsubscribed from /r/%s"
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

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded Completed table')
cur.execute('CREATE TABLE IF NOT EXISTS subscribers(name TEXT, reddit TEXT)')
print('Loaded Subscriber table')

sql.commit()

print('Logging in')
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 
del PASSWORD

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
	fetch = "+".join(fetch)
	return fetch

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
		return (MESSAGE_USUBSCRIBE % subreddit)
	cur.execute('SELECT * FROM subscribers WHERE LOWER(name)=? AND LOWER(reddit)=?', 
				[user, subreddit])
	if cur.fetchone():
		cur.execute('DELETE FROM subscribers WHERE LOWER(reddit)=?', [subreddit])
		sql.commit()
		return (MESSAGE_UNSUSBSCRIBE % subreddit)
	else:
		return (MESSAGE_UNSUBSCRIBE_ALREADY % subreddit)

def count_subscriptions():
	cur.execute('SELECT * FROM subscribers')
	fetch = cur.fetchall()
	return len(fetch)

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

def manage():
	print('Checking Inbox')
	pms = r.get_unread(unset_has_mail=True, update_user=True)
	for pm in pms:
		interpretation = interpret_message(pm)
		if interpretation:
			print('\tReplying...')
			pm.reply(interpretation)
		pm.mark_as_read()
	sql.commit()

	print('Finding posts')
	cur.execute('SELECT * FROM subscribers')
	userfetch = cur.fetchall()
	userfetch = [f[0].lower() for f in userfetch]
	userfetch = list(set(userfetch))

	cur.execute('SELECT * FROM oldposts')
	oldposts = cur.fetchall()
	oldposts = [f[0] for f in oldposts]

	postlist = set()

	for user in userfetch:
		print('Finding posts for %s' % user)
		usersubs = get_subscription_reddits(user)
		print('\t/r/' + usersubs)
		subreddit = r.get_subreddit(usersubs)
		posts = subreddit.get_new(limit=MAXPOSTS)
		results = []
		for post in posts:
			if post.id not in oldposts:
				print('\t' + post.id)
				results.append(post)
				postlist.add(post.id)
		results = [format_post(f) for f in results]

		if len(results) > 0:
			final = MESSAGE_HEADER + '\n\n'
			final += '\n\n'.join(results)
			final += '\n\n' + MESSAGE_FOOTER
			if NOSEND:
				print('NO SEND')
			else:
				try:
					r.send_message(user, MESSAGE_SUBJECT, final, captcha=None)
				except praw.errors.InvalidUser:
					drop_subscription(user, 'all')
					r.send_message(ADMIN, 'invalid user', user, captcha=None)
				except requests.exceptions.HTTPError:
					pass
		else:
			print('\tNone')

	for postid in postlist:
		cur.execute('INSERT INTO oldposts VALUES(?)', [postid])
	sql.commit()

def interpret_message(pm):
	results = []
	author = pm.author.name
	bodysplit = pm.body.lower()
	bodysplit = bodysplit.split('\n\n')
	if len(bodysplit) > 10:
		results = MESSAGE_TOOLONG + MESSAGE_FOOTER
		return results
	for line in bodysplit:
		linesplit = line.split()
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

			if command == 'subscribe':
				status = add_subscription(author, argument)
				results.append(status)

			elif command == 'unsubscribe':
				status = drop_subscription(author, argument)
				results.append(status)

			elif command == 'report':
				status = MESSAGE_REPORT_REQUEST + '\n\n'
				status += build_report(author)
				results.append(status)

			elif command == 'reportall' and author == ADMIN:
				status = MESSAGE_REPORT_ALL + '\n\n'
				status += build_report(None, supermode=True)
				results.append(status)

			elif command == 'reportuser' and author == ADMIN:
				status = (MESSAGE_REPORT_USER % argument) + '\n\n'
				status += build_report(argument)
				results.append(status)

			elif command == 'forcesubscribe' and author == ADMIN:
				argument = argument.split('.')
				user = argument[0]
				subreddit = argument[1]
				status = (MESSAGE_SUBSCRIBE_FORCE % (user, subreddit)) + '\n\n'
				status += add_subscription(user, subreddit)
				results.append(status)

			elif command == 'forceunsubscribe' and author == ADMIN:
				argument = argument.split('.')
				user = argument[0]
				subreddit = argument[1]
				status = (MESSAGE_UNSUBSCRIBE_FORCE % (user, subreddit)) + '\n\n'
				status += drop_subscription(user, subreddit)
				results.append(status)

			if command == 'kill' and author == ADMIN:
				pm.mark_as_read()
				r.send_message(ADMIN, "force kill", "bot is being turned off")
				quit()

	if len(results) > 0:
		results = '\n\n_____\n\n'.join(results)
		if len(results) > 9900:
			results = results[:9900]
			results += '\n\n' + MESSAGE_MESSAGE_LONG
		results += MESSAGE_FOOTER
		return results
	return None

def build_report(user, supermode=False):
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
		status.append(get_subscription_reddits(user, join=True))
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
		manage()
	except Exception:
		traceback.print_exc()
	print('%d active subscriptions' % count_subscriptions())
	print('Sleeping %s seconds\n\n\n' % WAITS)
	time.sleep(WAIT)