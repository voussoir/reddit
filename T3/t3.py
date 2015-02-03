#/u/GoldenSights
import praw
import time
import sqlite3
import datetime
import random

USERAGENT = """
/u/GoldenSights T3 data collection: Gathering Submission data for
statistical analysis.
More info at https://github.com/voussoir/reddit/tree/master/T3
"""
r = praw.Reddit(USERAGENT)
print('Connected to reddit.')

sql = sqlite3.connect('D:/T3/t3.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS meta(label TEXT, data TEXT)')
cur.execute(('CREATE TABLE IF NOT EXISTS posts(idint INT, idstr TEXT, '
	'created INT, self INT, nsfw INT, author TEXT, title TEXT, '
	'url TEXT, selftext TEXT, score INT, subreddit TEXT, distinguish INT, '
	'textlen INT, num_comments INT)'))

DISTINGUISHMAP   = {0:"user", 1:"moderator", 2:"admin"}
DISTINGUISHMAP_R = {"user":0, "moderator":1, "admin":2}

LOWERBOUND = 9999000
#            5yba0
UPPERBOUND = 164790958
#            2q41im

#    1,679,616 = 10000
#    9,999,000 = 5yba0
#   60,466,176 = 100000
#  120,932,352 = 200000
#  164,790,958 = 2q41im

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
class Post:
	''' Used to map the indices of DB entries to names '''
	def __init__(self, data):
		self.idint = data[0]
		self.idstr = data[1]
		self.created_utc = data[2]
		self.is_self = True if data[3] == 1 else False
		self.over_18 = True if data[4] == 1 else False
		self.author = data[5]
		self.title = data[6]
		self.url = data[7]
		self.selftext = data[8]
		self.score = data[9]
		self.subreddit = data[10]
		self.distinguished = DISTINGUISHMAP[data[11]]
		self.distinguished_int = data[11]
		self.textlen = data[12]
		self.num_comments = data[13]


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

def human(timestamp):
	day = datetime.datetime.utcfromtimestamp(timestamp)
	human = datetime.datetime.strftime(day, "%b %d %Y %H:%M:%S UTC")
	return human

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
		item.sub = item.subreddit.display_name
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
			cur.execute('SELECT * FROM posts WHERE idint=?', [b36(item[3:])])
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

def lastitem():
	cur.execute('SELECT * FROM posts ORDER BY idint DESC LIMIT 1')
	return cur.fetchone()[1]

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