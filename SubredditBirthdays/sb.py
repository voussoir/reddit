#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import datetime

'''USER CONFIGURATION'''

USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"

WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

'''All done!'''

WAITS = str(WAIT)

try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERAGENT = bot.aG
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS subreddits(ID TEXT, CREATED INT, HUMAN TEXT, NAME TEXT)')
print('Loaded SQL Database')
sql.commit()

r = praw.Reddit(USERAGENT)
print('Connected to reddit.')

olds = 0
d = {
	"Jan":"01",
	"Feb":"02",
	"Mar":"03",
	"Apr":"04",
	"May":"05",
	"Jun":"06",
	"Jul":"07",
	"Aug":"08",
	"Sep":"09",
	"Oct":"10",
	"Nov":"11",
	"Dec":"12"
}

def human(timestamp):
	day = datetime.datetime.utcfromtimestamp(timestamp)
	human = datetime.datetime.strftime(day, "%b %d %Y %H:%M:%S UTC")
	return human

def process(sr):
	global olds
	subs = []

	if type(sr) == str:
		for splitted in sr.split(','):
			splitted = splitted.replace(' ', '')
			splitted = r.get_subreddit(splitted)
			subs.append(splitted)

	else:
		subs.append(sr)

	for sub in subs:
		cur.execute('SELECT * FROM subreddits WHERE NAME=?', [sub.display_name])
		f = cur.fetchone()
		if not f:
			h = human(sub.created_utc)
			print('New: ' + sub.id + ' : ' + h + ' : ' + sub.display_name)
			cur.execute('INSERT INTO subreddits VALUES(?, ?, ?, ?)', [sub.id, sub.created_utc, h, sub.display_name])
			sql.commit()
		else:
			olds += 1

def news():
	global olds
	subreddit = r.get_subreddit('all')
	listed = []
	print('Getting new')
	new = list(subreddit.get_new(limit=20))
	print('Getting comments')
	coms = list(subreddit.get_comments(limit=20))
	listed += new + coms
	olds = 0
	for item in listed:
		sub = item.subreddit
		process(sub)
		sql.commit()
	print('Rejected', olds)

def show():
	filea = open('showt.txt', 'w')
	fileb = open('showd.txt', 'w')
	cur.execute('SELECT * FROM subreddits')
	f = cur.fetchall()

	f.sort(key=lambda x: x[1])
	print('Sorted by true time', file=filea)
	for member in f:
		print(member, file=filea)

	l = list(f)
	for m in range(len(l)):
		l[m] = list(l[m])
		#This is disgusting.
		l[m][2] = l[m][2].replace(l[m][2][:3], d[l[m][2][:3]])

	l.sort(key=lambda x: x[2])
	print('Sorted by day of month', file=fileb)
	for member in l:
		print(member, file=fileb)
	filea.close()
	fileb.close()


def nearby(ranged=7):
	#finds entries within range days of a birthday
	cur.execute('SELECT * FROM subreddits')
	fetched = cur.fetchall()
	fetched.sort(key=lambda x: x[2])

	results = []
	now = datetime.datetime.utcnow()
	for member in fetched:
		member = list(member)
		then = datetime.datetime.strptime(member[2], "%b %d %Y %H:%M:%S UTC")

		diff = abs((then-now).days)

		#There's probably a better way to do this
		while diff > 365:
			diff -= 365
		#There's definitely a better way to do this
		rd = 365 - ranged
		while diff > rd:
			diff -= rd

		if diff <= ranged:
			results.append(member)
	return results

