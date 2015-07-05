#/u/GoldenSights
import bot
import praw
import time
import sqlite3
import datetime
import random

r = praw.Reddit(bot.aG)
#r.login(bot.uG, bot.pG)
print('Connected to reddit.')

sql = sqlite3.connect('D:/T3/t3.db')
cur = sql.cursor()
cur.execute((''
	'CREATE TABLE IF NOT EXISTS posts('
	'idint INT, '
	'idstr TEXT, '
	'created INT, '
	'author TEXT, '
	'subreddit TEXT, '
	'self INT, '
	'nsfw INT, '
	'title TEXT, '
	'url TEXT, '
	'selftext TEXT, '
	'score INT, '
	'distinguished INT, '
	'textlen INT, '
	'num_comments INT)'))
cur.execute('CREATE INDEX IF NOT EXISTS idintindex on posts(idint)')
SQL_COLUMNCOUNT = 14
SQL_IDINT = 0
SQL_IDSTR = 1
SQL_CREATED = 2
SQL_AUTHOR = 3
SQL_SUBREDDIT = 4
SQL_SELF = 5
SQL_NSFW = 6
SQL_TITLE = 7
SQL_URL = 8
SQL_SELFTEXT = 9
SQL_SCORE = 10
SQL_DISTINGUISHED = 11
SQL_TEXTLEN = 12
SQL_NUM_COMMENTS = 13

DISTINGUISHMAP   = {0:'user', 1:'moderator', 2:'admin'}
DISTINGUISHMAP_R = {'user':0, 'moderator':1, 'admin':2, None:0}

LOWERBOUND = 9999000
#            5yba0
UPPERBOUND = 164790958
#            2q41im

#    1,679,616 = 10000
#    9,999,000 = 5yba0
#   60,466,176 = 100000
#  120,932,352 = 200000
#  164,790,958 = 2q41im


class Post:
	''' Generic class to map the indices of DB entries to names '''
	def __init__(self, data):
		self.idint = data[SQL_IDINT]
		self.idstr = data[SQL_IDSTR]
		self.created_utc = data[SQL_CREATED]
		self.is_self = True if data[SQL_SELF] == 1 else False
		self.over_18 = True if data[SQL_NSFW] == 1 else False
		self.author = data[SQL_AUTHOR]
		self.title = data[SQL_TITLE]
		self.url = data[SQL_URL]
		self.selftext = data[SQL_SELFTEXT]
		self.score = data[SQL_SCORE]
		self.subreddit = data[SQL_SUBREDDIT]
		self.distinguished = DISTINGUISHMAP[data[SQL_DISTINGUISHED]]
		self.distinguished_int = data[SQL_DISTINGUISHED]
		self.textlen = data[SQL_TEXTLEN]
		self.num_comments = data[SQL_NUM_COMMENTS]

def process(idstr, ranger=0):
	'''
	Given a string or a set of strings that represent thread IDs,
	get those Submissions and put them into the database
	'''

	if isinstance(idstr, str):
		idstr = [idstr]
	last = b36(idstr[-1])
	for x in range(ranger):
		# Take the last item in the list and get its ID in decimal
		# Then add the next `ranger` IDs into the list
		idstr.append(b36(last+x+1))
	idstr = remove_existing(idstr)
	idstr = verify_t3(idstr)
	while len(idstr) > 0:
		hundred = idstr[:100]
		print('(%d) %s > %s' % (len(idstr), hundred[0], hundred[-1]))
		try:
			items = list(r.get_submissions(hundred))
		except praw.errors.HTTPException as e:
			# 404 error means no posts exist for that ID.
			# So we know there's no posts here, and continue on
			# Anything other than 404, we need to hear about please
			if e._raw.status_code != 404:
				raise e
			items = []
			pass
		idstr = idstr[100:]
		for item in items:
			print(' %s, %s' % (item.fullname, item.subreddit._fast_name))
			item = dataformat(item)
			# Preverification happens via remove_existing
			smartinsert(item, preverified=True)
		sql.commit()
p = process

def remove_existing(idstr):
	'''
	Given a list of IDs, remove any which are already
	in the database

	This serves as preverification for process() so we don't
	do a SELECT for the same item twice.
	'''
	outset = []
	for i in idstr:
		if i in outset:
			continue
		check = i.replace('t3_', '')
		check = b36(check)
		cur.execute('SELECT * FROM posts WHERE idint==?', [check])
		if not cur.fetchone():
			outset.append(i)
		else:
			print(' %s preverify' % i)
	return outset

def dataformat(item):
	'''
	Given a Subission, return a list
	where the indices contain the data that corresponds
	to the the SQL column with the same indice
	'''

	data = [None] * SQL_COLUMNCOUNT
	data[SQL_IDINT] = b36(item.id)
	data[SQL_IDSTR] = item.id
	data[SQL_CREATED] = item.created_utc

	author = item.author
	if author is not None:
		author = author.name
	data[SQL_AUTHOR] = author
	data[SQL_SUBREDDIT] = item.subreddit._fast_name
	data[SQL_SELF] = 1 if item.is_self else 0
	data[SQL_NSFW] = 1 if item.over_18 else 0
	data[SQL_TITLE] = item.title

	url = item.url
	if ('/comments/%s/' % item.id) in url:
		# Don't waste your bytes saving the URL for selfposts
		url = None
	data[SQL_URL] = url
	selftext = item.selftext

	if selftext == '':
		selftext = None
	data[SQL_SELFTEXT] = selftext
	data[SQL_SCORE] = item.score

	distinguished = item.distinguished

	data[SQL_DISTINGUISHED] = DISTINGUISHMAP_R[item.distinguished]
	data[SQL_TEXTLEN] = len(item.selftext)
	data[SQL_NUM_COMMENTS] = item.num_comments
	return data

def smartinsert(data, preverified=False):
	'''
	Given a list, into the database if the item does not already exist
	Preverification means that it will not perform a SELECT to see
	if the item exists, because you have already guaranteed this.
	'''

	if not preverified:
		cur.execute('SELECT * FROM posts WHERE idint==?', [data[SQL_IDINT]])
	if (preverified) or (cur.fetchone() is None):
		cur.execute('INSERT INTO posts VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data)

def base36encode(number, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
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

def verify_t3(items):
	for index in range(len(items)):
		i = items[index]
		if 't3_' not in i:
			items[index] = 't3_' + i
	return items

def human(timestamp):
	day = datetime.datetime.utcfromtimestamp(timestamp)
	human = datetime.datetime.strftime(day, "%b %d %Y %H:%M:%S UTC")
	return human

def lastitem():
	cur.execute('SELECT * FROM posts ORDER BY idint DESC LIMIT 1')
	return cur.fetchone()[SQL_IDSTR]

'''
def process(itemid, log=True, kill=True, updates=False):
	if isinstance(itemid, str):
		itemid = [itemid]
	if isinstance(itemid, list):
		if isinstance(itemid[0], str):
			itemid = verify_t3(itemid)
			try:
				if not updates:
					itemid = remove_existing(itemid)
				temp = itemid[:]
			except Exception:
				return
			itemid = r.get_info(thing_id=itemid)
	try:
		len(itemid)
	except:
		print(temp, "DEAD")
		if kill:
			for item in temp:
				logdead(item)
		return
	for index in range(len(itemid)):
		item = itemid[index]
		item.idint = b36(item.id)
		item.idstr = item.id
		if item.distinguished is None:
			item.distinguished = 0
		else:
			item.distinguished = DISTINGUISHMAP_R[item.distinguished]

		item.url = "self" if item.is_self else item.url
		item.created_utc = int(item.created_utc)
		item.is_self = 1 if item.is_self else 0
		item.over_18 = 1 if item.over_18 else 0
		item.sub = item.subreddit._fast_name
		item.textlen = len(item.selftext)
		try:
			item.auth = item.author.name
		except AttributeError:
			item.auth = "[deleted]"

		item = [item.idint, item.idstr, item.created_utc,
		item.is_self, item.over_18, item.auth, item.title,
		item.url, item.selftext, item.score, item.sub,
		item.distinguished, item.textlen, item.num_comments]

		itemid[index] = item

	if log:
		logdb(itemid)
	else:
		return itemid
	if len(itemid) < len(temp):
		process(temp)
#  0 - idint
#  1 - idstr
#  2 - created
#  3 - self
#  4 - nsfw
#  5 - author
#  6 - title
#  7 - url
#  8 - selftext
#  9 - score
# 10 - subreddit
# 11 - distinguished
# 12 - textlen
# 13 - num_comments
def logdb(items):
	for item in items:
		cur.execute('SELECT * FROM posts WHERE idint=?', [item[0]])
		if cur.fetchone():
			cur.execute('DELETE FROM posts WHERE idint=?', [item[0]])
		cur.execute('INSERT INTO posts VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', item)
		print(item[1], item[10])
	sql.commit()

def logdead(i):
	#If an ID is dead, let's at least add it to the db.
	i = i.replace('t3_', '')
	data = [b36(i), i, 0, 0, 0, '?', '?', '?', '?', 0, '?', 0, 0, -1]
	logdb([data])

def verify_t3(items):
	for index in range(len(items)):
		i = items[index]
		if 't3_' not in i:
			items[index] = 't3_' + i
	return items

def remove_existing(items):
	done = False
	items = verify_t3(items)
	while not done:
		done = True
		for item in items:
			cur.execute('SELECT * FROM posts WHERE idint=? AND created != 0', [b36(item[3:])])
			f = cur.fetchone()
			if f:
				items.remove(item)
				done = False
				break
	if len(items) == 0:
		raise Exception("Nothing new")
	return items

def processrange(lower, upper, kill=True, updates=False):
	if isinstance(lower, str):
		lower = b36(lower)
		if isinstance(upper, int):
			upper = lower + upper
	if isinstance(upper, str):
		upper = b36(upper)
	if upper <= lower:
		print("Upper must be higher than lower")
		return
	ids = [b36(x) for x in range(lower, upper)]
	processchunks(ids, kill, updates)

def processchunks(ids, kill=True, updates=False):
	while len(ids) > 0:
		p = ids[:100]
		print("%s >>> %s (%d)" % (p[0], p[-1], len(ids)))
		ids = ids[100:]
		process(p, kill=kill, updates=updates)

def show():
	filea = open('show/missing.txt', 'w')
	fileb = open('show/stats.txt', 'w')

	totalcount = 0
	totaltitle = 0
	totalselftext = 0
	totalscore = 0
	deadcount = 0
	selfcount = 0
	nsfwcount = 0
	distinguishcount_m = 0
	distinguishcount_a = 0
	commentcount = 0
	subredditcounts = {}
	dead = []
	
	cur.execute('SELECT * FROM posts')
	post = cur.fetchone()
	while post:
		post = Post(post)
		totalcount += 1
		if post.created_utc == 0:
			deadcount += 1
			dead.append(post.idstr)
			post = cur.fetchone()
			continue
		if post.is_self:
			selfcount += 1
			totalselftext += post.textlen
		if post.over_18:
			nsfwcount += 1
		if post.distinguished_int == 1:
			distinguishcount_m += 1
		elif post.distinguished_int == 2:
			distinguishcount_a += 1
		totalscore += post.score
		totaltitle += len(post.title)
		if post.num_comments > 0:
			commentcount += 1

		try:
			subredditcounts[post.subreddit] += 1
		except KeyError:
			subredditcounts[post.subreddit] = 1

		post = cur.fetchone()

	for deaditem in dead:
		print(deaditem, file=filea)
	filea.close()


	currenttime = datetime.datetime.now()
	currenttime = datetime.datetime.strftime(currenttime, "%B %d %Y %H:%M:%S")
	currenttimes = "Updated %s\n" % currenttime

	counts = '{0:,}'.format(totalcount)
	mainstats = '%s posts collected; ' % counts
	mainstats += '%s dead.\n' % '{0:,}'.format(deadcount)

	linkcount = (totalcount - deadcount) - selfcount
	selfs = '{0:,}'.format(selfcount)
	links = '{0:,}'.format(linkcount)
	selfstats = '%s linkposts; %s selfposts\n' % (links, selfs)

	readmefile = open('README.md', 'r')
	readmelines = readmefile.readlines()
	readmefile.close()
	readmelines[3] = currenttimes
	readmelines[4] = mainstats
	readmelines[5] = selfstats

	readmefile = open('README.md', 'w')
	readmefile.write(''.join(readmelines))
	readmefile.close()


	subkeys = list(subredditcounts.keys())
	subkeys.sort(key=subredditcounts.get, reverse=True)
	print('Total: %s' % '{0:,}'.format(totalcount), file=fileb)
	print('Dead: %s' % '{0:,}'.format(deadcount), file=fileb)
	print('Self: %s' % '{0:,}'.format(selfcount), file=fileb)
	print('Link: %s' % '{0:,}'.format(linkcount), file=fileb)
	print('NSFW: %s' % '{0:,}'.format(nsfwcount), file=fileb)
	print('Distinguished by mods: %s' % '{0:,}'.format(distinguishcount_m), file=fileb)
	print('Distinguished by admins: %s' % '{0:,}'.format(distinguishcount_a), file=fileb)
	print('Total upvotes: %s' % '{0:,}'.format(totalscore), file=fileb)
	print('Total characters in titles: %s' % '{0:,}'.format(totaltitle), file=fileb)
	print('Total characters in selftext: %s' % '{0:,}'.format(totalselftext), file=fileb)
	print('Total (supposed) comments on posts: %s' % '{0:,}'.format(commentcount), file=fileb)
	print('\n\n', file=fileb)
	for key in subkeys:
		out = key
		out += '.'*(25-len(key))
		num = '{0:,}'.format(subredditcounts[key])
		out += '.'*(14-len(num))
		out += num
		print(out, file=fileb)
	fileb.close()
'''