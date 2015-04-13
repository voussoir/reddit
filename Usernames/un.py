import praw
import requests
import sqlite3
import bot
import datetime
import time

sql = sqlite3.connect('un.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users(idint INT, idstr TEXT, created INT, human TEXT, name TEXT, link_karma INT, comment_karma INT, total_karma INT, available INT, lastscan INT)')
cur.execute('CREATE INDEX IF NOT EXISTS userindex ON users(idint)')
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

USERAGENT = "/u/GoldenSights Usernames data collection: Gathering the creation dates of user accounts in the interest of information.\
 More at https://github.com/voussoir/reddit/tree/master/Usernames"
r = praw.Reddit(USERAGENT)
r.login(bot.uG, bot.pG)


AVAILABILITY = {True:'available', False:'unavailable', 'available':1, 'unavailable':0}


def human(timestamp):
	day = datetime.datetime.utcfromtimestamp(timestamp)
	human = datetime.datetime.strftime(day, "%b %d %Y %H:%M:%S UTC")
	return human

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

def reducetonames(users):
	outlist = set()
	for name in users:
		if isinstance(name, str):
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
			user = r.get_redditor(username)
			yield user
		except requests.exceptions.HTTPError as he:
			if he.response.status_code != 404:
				raise he
			availability = r.is_username_available(username)
			availability = AVAILABILITY[availability]
			yield [username, availability]

def process(users):
	olds = 0
	users = userify_list(users)
	now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
	current = 0
	for user in users:
		current += 1
		data = [None] * 10
		data[SQL_LASTSCAN] = now
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

		x = smartinsert(data, '%04d' % current)
		if x is False:
			olds += 1
	print('%d old' % olds)

def smartinsert(data, printprefix=''):
	isnew = False
	if data[SQL_IDINT] is not None:
		print('%s %s : %s : %s : %d : %d' % (
				printprefix,
				data[SQL_IDSTR],
				data[SQL_HUMAN],
				data[SQL_NAME],
				data[SQL_LINK_KARMA],
				data[SQL_COMMENT_KARMA]))
	else:
		print('%s : %s' % (data[SQL_NAME], data[SQL_AVAILABLE]))
	cur.execute('SELECT * FROM users WHERE idint=?', [data[0]])
	if cur.fetchone():
		data = [
			data[SQL_LINK_KARMA],
			data[SQL_COMMENT_KARMA],
			data[SQL_TOTAL_KARMA],
			data[SQL_AVAILABLE],
			data[SQL_LASTSCAN],
			data[SQL_IDINT]]
		cur.execute('UPDATE users SET link_karma=?, comment_karma=?, total_karma=?, available=?, lastscan=? WHERE idint=?', data)
	else:
		isnew = True
		cur.execute('INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data)
	sql.commit()
	return isnew

def get_from_new(sr, limit, submissions=True, comments=True, returnnames=False):
	subreddit = r.get_subreddit(sr)
	if limit is None:
		limit = 1000
	items = []
	if submissions is True:
		print('/r/%s, %d submissions' % (sr, limit))
		items += list(subreddit.get_new(limit=limit))
	if comments is True:
		print('/r/%s, %d comments' % (sr, limit))
		items += list(subreddit.get_comments(limit=limit))

	items = [x.author for x in items]
	while None in items:
		items.remove(None)

	if returnnames is True:
		return items

	process(items)