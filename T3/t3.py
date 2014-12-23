#/u/GoldenSights
import praw
import time
import sqlite3
import datetime


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
	'created INT, human TEXT, self INT, nsfw INT, author TEXT, title TEXT, '
	'url TEXT, selftext TEXT, score INT, subreddit TEXT, distinguish INT, '
	'textlen INT)'))

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
# 11 - distinguishment
# 12 - textlen
class Post:
	''' Used to map the indices of DB entries to names '''
	def __init__(self, data):
		distinguishmap = {0:"user", 1:"moderator", 2:"admin"}
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
		self.distinguishment = distinguishmap[data[11]]


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

def process(itemid):
	print(itemid)