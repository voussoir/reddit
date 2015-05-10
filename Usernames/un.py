import praw
import random
import requests
import sqlite3
import bot
import datetime
import time
import string


sql = sqlite3.connect('un.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users(idint INT, idstr TEXT, created INT, human TEXT, name TEXT, link_karma INT, comment_karma INT, total_karma INT, available INT, lastscan INT)')
cur.execute('CREATE INDEX IF NOT EXISTS userindex ON users(idint)')
cur.execute('CREATE INDEX IF NOT EXISTS nameindex ON users(name)')
sql.commit()
#  0 - idint
#  1 - idstr
#  2 - created
#  3 - human
#  4 - name
#  5 - link karma
#  6 - comment karma
#  7 - total karma
#  8 - available
#  9 - lastscan
SQL_COLUMNCOUNT = 10
SQL_IDINT = 0
SQL_IDSTR = 1
SQL_CREATED = 2
SQL_HUMAN = 3
SQL_NAME = 4
SQL_LINK_KARMA = 5
SQL_COMMENT_KARMA = 6
SQL_TOTAL_KARMA = 7
SQL_AVAILABLE = 8
SQL_LASTSCAN = 9

print('Logging in.')
USERAGENT = "/u/GoldenSights Usernames data collection: Gathering the creation dates of user accounts in the interest of information.\
 More at https://github.com/voussoir/reddit/tree/master/Usernames"
r = praw.Reddit(USERAGENT)
r.login(bot.uG, bot.pG)


AVAILABILITY = {True:'available', False:'unavailable', 'available':1, 'unavailable':0}
HEADER_FULL = '  ID            CREATED                  NAME             LINK     COMMENT      TOTAL            LAST SCANNED'
HEADER_BRIEF = '      LAST SCANNED       |   NAME'

MEMBERFORMAT_FULL = '%s  %s  %s  %s  %s (%s) | %s'
MEMBERFORMAT_BRIEF = '%s | %s'

MIN_LASTSCAN_DIFF = 86400 * 70
# Don't rescan a name if we scanned it this many days ago

def human(timestamp):
	day = datetime.datetime.utcfromtimestamp(timestamp)
	human = datetime.datetime.strftime(day, "%b %d %Y %H:%M:%S UTC")
	return human

def getnow(timestamp=True):
	now = datetime.datetime.now(datetime.timezone.utc)
	if timestamp:
		return now.timestamp()
	return now

def base36encode(number, alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    """Converts an integer to a base36 string."""
    if not isinstance(number, (int)):
        raise TypeError('number must be an integer')
    base36 = ''
    sign = ''
    if number < 0:
        sign = '-'
        number = -number
    if 0 <= number < len(alphabet):
        return sign + alphabet[number]
    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36
    return sign + base36

def base36decode(number):
    return int(number, 36)

def b36(i):
	if type(i) == int:
		return base36encode(i)
	if type(i) == str:
		return base36decode(i)

def getentry(**kwargs):
	if len(kwargs) != 1:
		raise Exception("Only 1 argument please")
	kw = list(kwargs.keys())[0]
	if kw == 'idint':
		cur.execute('SELECT * FROM users WHERE idint=?', [kwargs[kw]])
	elif kw == 'idstr':
		cur.execute('SELECT * FROM users WHERE idstr=?', [kwargs[kw]])
	elif kw == 'name':
		cur.execute('SELECT * FROM users WHERE LOWER(name)=?', [kwargs[kw].lower()])
	else:
		return None
	return cur.fetchone()

def reducetonames(users):
	outlist = set()
	for name in users:
		if isinstance(name, str):
			if 2 < len(name) < 21:
				outlist.add(name.lower())
		elif isinstance(name, praw.objects.Redditor):
			outlist.add(name.name.lower())
	return outlist

def userify_list(users):
	outlist = []
	if isinstance(users, str):
		users = [users]
	users = list(reducetonames(users))
	for username in users:
		try:
			preverify = getentry(name=username)
			if preverify is not None:
				preverify = preverify[SQL_LASTSCAN]
				preverify = getnow() - preverify
				preverify = (preverify > MIN_LASTSCAN_DIFF)
				if not preverify:
					print('skipping ' + username)
					continue
			else:
				preverify = False
			user = r.get_redditor(username)
			user.preverify = preverify
			yield user
		except requests.exceptions.HTTPError as he:
			if he.response.status_code != 404:
				raise he
			availability = r.is_username_available(username)
			availability = AVAILABILITY[availability]
			yield [username, availability]

def process(users, quiet=False):
	olds = 0
	users = userify_list(users)
	now = int(getnow())
	current = 0
	for user in users:
		current += 1
		data = [None] * SQL_COLUMNCOUNT
		data[SQL_LASTSCAN] = now
		preverify=False
		if isinstance(user, list):
			data[SQL_NAME] = user[0]
			data[SQL_AVAILABLE] = AVAILABILITY[user[1]]
		else:
			h = human(user.created_utc)
			data[SQL_IDINT] = b36(user.id)
			data[SQL_IDSTR] = user.id
			data[SQL_CREATED] = user.created_utc
			data[SQL_HUMAN] = h
			data[SQL_NAME] = user.name
			data[SQL_LINK_KARMA] = user.link_karma
			data[SQL_COMMENT_KARMA] = user.comment_karma
			data[SQL_TOTAL_KARMA] = user.comment_karma + user.link_karma
			data[SQL_AVAILABLE] = 0
			preverify = user.preverify

		# preverification happens within userify_list
		x = smartinsert(data, '%04d' % current, preverified=preverify)

		if x is False:
			olds += 1
	if quiet is False:
		print('%d old' % olds)
p = process

def processid(idnum, ranger=1):
	idnum = idnum.split('_')[-1]
	base = b36(idnum)
	for x in range(ranger):
		idnum = x + base
		idnum = 't2_' + b36(idnum)
		search = list(r.search('author_fullname:%s' % idnum))
		if len(search) > 0:
			item = search[0].author.name
			process(item)
		else:
			print('Ain\'t found shit.')
pid = processid

def smartinsert(data, printprefix='', preverified=False):
	'''
	Originally, all queries were based on idint, but this caused problems
	when accounts were deleted / banned, because it wasn't possible to
	sql-update without knowing the ID.
	'''
	isnew = False
	
	print_message(data, printprefix)
	

	check = False
	if not preverified:
		cur.execute('SELECT * FROM users WHERE name=?', [data[SQL_NAME]])
		check = cur.fetchone()
		check = check is not None
	if preverified or check:
		data = [
			data[SQL_IDINT],
			data[SQL_IDSTR],
			data[SQL_CREATED],
			data[SQL_HUMAN],
			data[SQL_LINK_KARMA],
			data[SQL_COMMENT_KARMA],
			data[SQL_TOTAL_KARMA],
			data[SQL_AVAILABLE],
			data[SQL_LASTSCAN],
			data[SQL_NAME]]
		cur.execute('UPDATE users SET idint=?, idstr=?, created=?, human=?, link_karma=?, comment_karma=?, total_karma=?, available=?, lastscan=? WHERE name=?', data)
	else:
		isnew = True
		cur.execute('INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data)
	sql.commit()
	return isnew

def print_message(data, printprefix=''):
	if data[SQL_IDINT] is not None:
		print('%s %s : %s : %s : %d : %d' % (
				printprefix,
				data[SQL_IDSTR],
				data[SQL_HUMAN],
				data[SQL_NAME],
				data[SQL_LINK_KARMA],
				data[SQL_COMMENT_KARMA]))
	else:
		statement = 'available' if data[SQL_AVAILABLE] is 1 else 'unavailable'
		print('%s : %s' % (data[SQL_NAME], statement))

def get_from_listing(sr, limit, listfunction, submissions=True, comments=True, returnnames=False):
	subreddit = r.get_subreddit(sr)
	if limit is None:
		limit = 1000
	items = []
	if submissions is True:
		print('/r/%s, %d submissions' % (sr, limit))
		subreddit.lf = listfunction
		items += list(subreddit.lf(subreddit, limit=limit))
	if comments is True:
		print('/r/%s, %d comments' % (sr, limit))
		items += list(subreddit.get_comments(limit=limit))

	items = [x.author for x in items]
	while None in items:
		items.remove(None)

	if returnnames is True:
		return items

	process(items)

def get_from_new(sr, limit=None, submissions=True, comments=True, returnnames=False):
	listfunction = praw.objects.Subreddit.get_new
	return get_from_listing(sr, limit, listfunction, submissions, comments, returnnames)

def get_from_top(sr, limit=None, submissions=True, comments=True, returnnames=False):
	listfunction = praw.objects.Subreddit.get_top_from_all
	return get_from_listing(sr, limit, listfunction, submissions, comments, returnnames)

def get_from_hot(sr, limit=None, submissions=True, comments=True, returnnames=False):
	listfunction = praw.objects.Subreddit.get_hot
	return get_from_listing(sr, limit, listfunction, submissions, comments, returnnames)

def fetchgenerator():
	'''
	Create an generator from cur fetches so I don't
	have to use while loops for everything
	'''
	while True:
		fetch = cur.fetchone()
		if fetch is None:
			break
		yield fetch

def fetchwriter(outfile, spacer1=' ', spacer2=None, brief=False):
	'''
	Write items from the current sql query to the specified file

	If two spacers are provided, it will flip-flop between them
	on alternating lines
	'''
	flipflop = True
	for item in fetchgenerator():
		spacer = spacer1 if flipflop else spacer2
		if brief:
			item = memberformat_brief(item, spacer)
		else:
			item = memberformat_full(item, spacer)
		print(item, file=outfile)
		if spacer2 is not None:
			flipflop = not flipflop

def show():
	file_time = open('show\\time.txt', 'w')
	file_name = open('show\\name.txt', 'w')
	file_karma_total = open('show\\karma_total.txt', 'w')
	file_karma_link = open('show\\karma_link.txt', 'w')
	file_karma_comment = open('show\\karma_comment.txt', 'w')
	file_available = open('show\\available.txt', 'w')
	file_readme = open('README.md', 'r')

	cur.execute('SELECT COUNT(*) FROM users')
	totalitems = cur.fetchone()[0]
	cur.execute('SELECT COUNT(*) FROM users WHERE idint IS NOT NULL')
	validitems = cur.fetchone()[0]
	print(totalitems, validitems)

	print('Updating readme')
	readmelines = file_readme.readlines()
	file_readme.close()
	readmelines[3] = '#####{0:,} accounts\n'.format(validitems)
	readmelines = ''.join(readmelines)
	file_readme = open('README.md', 'w')
	file_readme.write(readmelines)
	file_readme.close()

	print('Writing time file.')
	print(HEADER_FULL, file=file_time)
	cur.execute('SELECT * FROM users WHERE idint IS NOT NULL ORDER BY created ASC')
	fetchwriter(file_time)
	file_time.close()

	print('Writing name file.')
	print(HEADER_FULL, file=file_name)
	cur.execute('SELECT * FROM users WHERE idint IS NOT NULL ORDER BY LOWER(name) ASC')
	fetchwriter(file_name)
	file_name.close()
	
	print('Writing karma total file.')
	print(HEADER_FULL, file=file_karma_total)
	cur.execute('SELECT * FROM users WHERE idint IS NOT NULL ORDER BY total_karma DESC, LOWER(name) ASC')
	fetchwriter(file_karma_total)
	file_karma_total.close()

	print('Writing karma link file.')
	print(HEADER_FULL, file=file_karma_link)
	cur.execute('SELECT * FROM users WHERE idint IS NOT NULL ORDER BY link_karma DESC, LOWER(name) ASC')
	fetchwriter(file_karma_link)
	file_karma_link.close()

	print('Writing karma comment file.')
	print(HEADER_FULL, file=file_karma_comment)
	cur.execute('SELECT * FROM users WHERE idint IS NOT NULL ORDER BY comment_karma DESC, LOWER(name) ASC')
	fetchwriter(file_karma_comment)
	file_karma_comment.close()

	print('Writing available')
	print(HEADER_BRIEF, file=file_available)
	cur.execute('SELECT * FROM users WHERE available == 1 AND LENGTH(name) > 3 ORDER BY LOWER(name) ASC')
	fetchwriter(file_available, spacer1=' ', brief=True)
	file_available.close()

def commapadding(s, spacer, spaced, left=True, forcestring=False):
	'''
	Given a number 's', make it comma-delimted and then
	pad it on the left or right using character 'spacer'
	so the whole string is of length 'spaced'

	Providing a non-numerical string will skip straight
	to padding
	'''
	if not forcestring:
		try:
			s = int(s)
			s = '{0:,}'.format(s)
		except:
			pass

	spacer = spacer * (spaced - len(s))
	if left:
		return spacer + s
	return s + spacer

def memberformat_full(data, spacer='.'):
	idstr = data[SQL_IDSTR]
	idstr = commapadding(idstr, spacer, 5, forcestring=True)

	# Usernames are maximum of 20 chars
	name = data[SQL_NAME]
	name += spacer*(20 - len(name))

	link_karma = data[SQL_LINK_KARMA]
	comment_karma = data[SQL_COMMENT_KARMA]
	total_karma = data[SQL_TOTAL_KARMA]
	if link_karma is None:
		link_karma = commapadding('None', spacer, 9)
		comment_karma = commapadding('None', spacer, 9)
		total_karma = commapadding('None', spacer, 10)
	else:
		link_karma = commapadding(link_karma, spacer, 9)
		comment_karma = commapadding(comment_karma, spacer, 9)
		total_karma = commapadding(total_karma, spacer, 10)

	lastscan = data[SQL_LASTSCAN]
	lastscan = human(lastscan)
	out = MEMBERFORMAT_FULL % (
		idstr,
		data[SQL_HUMAN],
		name,
		link_karma,
		comment_karma,
		total_karma,
		lastscan)
	return out

def memberformat_brief(data, spacer='.'):
	name = data[SQL_NAME]
	lastscan = data[SQL_LASTSCAN]
	lastscan = human(lastscan)

	out = MEMBERFORMAT_BRIEF % (lastscan, name)
	return out

def find(name):
	cur.execute('SELECT * FROM users WHERE LOWER(name)=?', [name])
	f = cur.fetchone()
	if f:
		print_message(f)
	else:
		print(f)