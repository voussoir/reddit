#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import datetime
import sys

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
monthnumbers = {
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

def processi(sr):
	global olds
	if 't5_' not in sr:
		sr = 't5_' + sr
	cur.execute('SELECT * FROM subreddits WHERE ID=?', [sr[3:]])
	if not cur.fetchone():
		sr = r.get_info(thing_id=sr)
		try:
			sr.id
			process(sr)
		except ValueError:
			print('Could not fetch subreddit')
	else:
		olds += 1

def process(sr):
	global olds
	subs = []

	if type(sr) == str:
		for splitted in sr.split(','):
			splitted = splitted.replace(' ', '')
			sr = r.get_subreddit(splitted)
			subs.append(sr)

	elif type(sr) == praw.objects.Submission or type(sr) == praw.objects.Comment:
		sr = sr.subreddit
		subs.append(sr)

	else:
		subs.append(sr)

	for sub in subs:
		cur.execute('SELECT * FROM subreddits WHERE ID=?', [sub.id])
		f = cur.fetchone()
		if not f:
			h = human(sub.created_utc)
			print('New: ' + sub.id + ' : ' + h + ' : ' + sub.display_name)
			cur.execute('INSERT INTO subreddits VALUES(?, ?, ?, ?)', [sub.id, sub.created_utc, h, sub.display_name])
			sql.commit()
		else:
			olds += 1

def news(limit=20):
	global olds
	subreddit = r.get_subreddit('all')
	listed = []
	print('Getting new')
	new = list(subreddit.get_new(limit=limit))
	print('Getting comments')
	coms = list(subreddit.get_comments(limit=limit))
	listed += new + coms
	olds = 0
	for item in listed:
		sub = item.subreddit_id
		processi(sub)
	sql.commit()
	print('Rejected', olds)

def show():
	filea = open('showt.txt', 'w')
	fileb = open('showd.txt', 'w')
	filec = open('shown.txt', 'w')
	cur.execute('SELECT * FROM subreddits')
	fetch = cur.fetchall()

	fetch.sort(key=lambda x: x[1])
	print('Sorted by true time', file=filea)
	for member in fetch:
		print(str(member).replace("'", ''), file=filea)

	fetch.sort(key=lambda x: x[3].lower())
	print('Sorted by name', file=filec)
	for member in fetch:
		print(str(member).replace("'", ''), file=filec)

	l = list(fetch)
	print(str(len(l)) + ' items.')
	for m in range(len(l)):
		l[m] = list(l[m])

		#I cleaned it up, guys
		fulldate = l[m][2]
		monthname = fulldate[:3]
		l[m][2] = fulldate.replace(monthname, monthnumbers[monthname])

	l.sort(key=lambda x: x[2])
	print('Sorted by day of month', file=fileb)
	for member in l:
		print(str(member).replace("'", ''), file=fileb)
	filea.close()
	fileb.close()
	filec.close()


def nearby(ranged=16):
	#find upcoming birthdays
	cur.execute('SELECT * FROM subreddits')
	fetched = cur.fetchall()

	results = []
	now = datetime.datetime.utcnow()

	for m in range(len(fetched)):
		member = list(fetched[m])

		membertime = member[2]
		membermonth = membertime[:3]
		membertime = membertime.replace(membermonth, monthnumbers[membermonth])

		member[2] = membertime

		fetched[m] = member
		
	nowentry = ['Today', int("%0.0f" % now.timestamp()), datetime.datetime.strftime(now, "%m %d %Y %H:%M:%S UTC"), '##########']
	fetched.append(nowentry)
	fetched.sort(key=lambda x: (x[2][:6] + x[2][11:]))

	nowindex = fetched.index(nowentry)
	results.append(nowentry)
	results.append('')
	for item in fetched[nowindex+1:nowindex+ranged+1]:
		results.append(item)


	#return results
	for item in results:
		print(item)