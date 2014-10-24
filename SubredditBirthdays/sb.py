#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import datetime
import urllib
import json
import sys
import random
import os

'''USER CONFIGURATION'''

USERAGENT = "/u/GoldenSights SubredditBirthdays data collection: Gathering the creation dates of subreddits in the interest of information.\
 More at https://github.com/voussoir/reddit/tree/master/SubredditBirthdays"
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"

WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

'''All done!'''

WAITS = str(WAIT)


sql = sqlite3.connect('sql.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS subreddits(ID TEXT, CREATED INT, HUMAN TEXT, NSFW TEXT, NAME TEXT)')
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
			cur.execute('SELECT * FROM subreddits WHERE LOWER(NAME)=?', [splitted.lower()])
			if not cur.fetchone():
				sr = r.get_subreddit(splitted)
				subs.append(sr)
			else:
				olds += 1
				pass

	elif type(sr) == praw.objects.Submission or type(sr) == praw.objects.Comment:
		sr = sr.subreddit
		subs.append(sr)

	else:
		subs.append(sr)

	for sub in subs:
		try:
			cur.execute('SELECT * FROM subreddits WHERE ID=?', [sub.id])
			f = cur.fetchone()
			if not f:
				h = human(sub.created_utc)
				isnsfw = '1' if sub.over18 else '0'
				print('New: ' + sub.id + ' : ' + h + ' : ' + isnsfw + ' : '+ sub.display_name)
				isnsfw = 'NSFW:' + isnsfw
				cur.execute('INSERT INTO subreddits VALUES(?, ?, ?, ?, ?)', [sub.id, sub.created_utc, h, isnsfw, sub.display_name])
				sql.commit()
			else:
				olds += 1
		except praw.requests.exceptions.HTTPError:
			print('HTTPError:', sub)

def get(limit=20):
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
	filea = open('show\\all-time.txt', 'w')
	fileb = open('show\\all-dom.txt', 'w')
	filec = open('show\\all-name.txt', 'w')
	#filed = open('show\\allx-name.txt', 'w')
	#filee = open('show\\allx-time.txt', 'w')
	filef = open('show\\clean-time.txt', 'w')
	fileg = open('show\\clean-name.txt', 'w')
	fileh = open('show\\dirty-time.txt', 'w')
	filei = open('show\\dirty-name.txt', 'w')
	#filej = open('show\\allx-dom.txt', 'w')
	filek = open('show\\clean-dom.txt', 'w')
	filel = open('show\\dirty-dom.txt', 'w')
	filem = open('show\\statistics.txt', 'w')
	filen = open('show\\missing.txt', 'w')
	fileo = open('show\\all-marked.txt', 'w')
	filep = open('README.md', 'r')
	cur.execute('SELECT * FROM subreddits WHERE CREATED !=?', [0])
	fetch = cur.fetchall()
	itemcount = len(fetch)
	print(str(itemcount) + ' items.')

	fetch.sort(key=lambda x: x[1])
	print('Writing time files')
	print(str(itemcount) + ' subreddits sorted by true time', file=filea)
	for member in fetch:
		print(str(member).replace("'", ''), file=filea)
	filea.close()
	#shown(fetch, 'Sorted by nsfw by true time', filee)
	#filee.close()
	shown(fetch, 'Clean only sorted by true time', filef, nsfwmode=0)
	filef.close()
	shown(fetch, 'Nsfw only sorted by true time', fileh, nsfwmode=1)
	fileh.close()


	fetch.sort(key=lambda x: b36(x[0]))
	previd = fetch[0][0]
	print('Writing marked file')
	print('Sorted by ID number gaps marked', file=fileo)
	for member in fetch:
		curid = member[0]
		iddiff = b36(curid) - b36(previd)
		if iddiff != 1 and iddiff != 0:
			print('#' + str(iddiff-1), file=fileo)
		print(str(member).replace("'", ''), file=fileo)
		previd = curid
	fileo.close()


	print('Writing statistics')
	totalpossible = b36(fetch[-1][0]) - 4594411
	headliner= 'Collected '+'{0:,}'.format(itemcount)+' of '+'{0:,}'.format(totalpossible)+' subreddits ('+"%0.03f"%(100*itemcount/totalpossible)+'%)\n'
	#Call the PEP8 police on me, I don't care
	print(headliner, file=filem)
	statisticoutput = ""
	dowdict = {}
	moydict = {}
	hoddict = {}
	yerdict = {}
	for item in fetch:
		itemdate = datetime.datetime.utcfromtimestamp(item[1])
		dowdict = dictadding(dowdict, datetime.datetime.strftime(itemdate, "%A"))
		moydict = dictadding(moydict, datetime.datetime.strftime(itemdate, "%B"))
		hoddict = dictadding(hoddict, datetime.datetime.strftime(itemdate, "%H"))
		yerdict = dictadding(yerdict, datetime.datetime.strftime(itemdate, "%Y"))
	#print(yerdict)

	for d in [dowdict, moydict, hoddict, yerdict]:
		d = dict(zip(d.keys(), d.values()))
		dkeys = list(d.keys())
		dkeys.sort(key=d.get)
		for nk in dkeys:
			nks = str(d.get(nk))
			statisticoutput += nk + ': ' + ('.' * (10-len(nk))) + ('.' * (8-len(nks))) + nks
			statisticoutput += '\n'
		statisticoutput += '\n\n'

	print(statisticoutput, file=filem)
	filem.close()

	readmeread = filep.readlines()
	filep.close()
	readmeread[3] = '#####' + headliner
	filep = open('README.md', 'w')
	filep.write(''.join(readmeread))
	filep.close()


	fetch.sort(key=lambda x: x[4].lower())
	print('Writing name files')
	print('Sorted by name', file=filec)
	for member in fetch:
		print(str(member).replace("'", ''), file=filec)
	filec.close()
	#shown(fetch, 'Sorted by nsfw by name', filed)
	#filed.close()
	shown(fetch, 'Clean only sorted by name', fileg, nsfwmode=0)
	fileg.close()
	shown(fetch, 'Nsfw only sorted by name', filei, nsfwmode=1)
	filei.close()

	l = list(fetch)
	for m in range(len(l)):
		l[m] = list(l[m])
		#I cleaned it up, guys
		fulldate = l[m][2]
		monthname = fulldate[:3]
		l[m][2] = fulldate.replace(monthname, monthnumbers[monthname])

	l.sort(key=lambda x: x[2])
	print('Sorted by day of month', file=fileb)
	print('Writing day files')
	for member in l:
		print(str(member).replace("'", ''), file=fileb)
	fileb.close()
	#shown(l, 'Sorted by nsfw by day of month', filej)
	#filej.close()
	shown(l, 'Clean only sorted by day of month', filek, nsfwmode=0)
	filek.close()
	shown(l, 'Nsfw only sorted by day of month', filel, nsfwmode=1)
	filel.close()

	print('Writing missingnos')
	cur.execute('SELECT * FROM subreddits WHERE CREATED=?', [0])
	fetch = cur.fetchall()
	fetch.sort(key=lambda x: b36(x[0]))
	fetch = (f[0] for f in fetch)
	for member in fetch:
		print(member, file=filen)
	filen.close()


def dictadding(targetdict, item):
	if item not in targetdict:
		targetdict[item] = 1
	else:
		targetdict[item] = targetdict[item] + 1
	return targetdict


def shown(startinglist, header, fileobj, nsfwmode=2):
	"""
	Creating Show files with filters
	*lst startinglist= the unfiltered list
	*str header= the header at the top of the file
	*obj fileobj= the file object to write to
	*int nsfwmode=
	  0 - Clean only
	  1 - Dirty only
	  2 - All
	"""

	nsfwyes = []
	nsfwno = []
	nsfwq = []
	for item in startinglist:
		if item[3] == 'NSFW:1':
			nsfwyes.append(item)
		elif item[3] == 'NSFW:?':
			nsfwq.append(item)
		else:
			nsfwno.append(item)
	print(header, file=fileobj)
	if nsfwmode == 0 or nsfwmode == 2:
		for member in nsfwno:
			print(str(member).replace("'", ''), file=fileobj)
		print('\n' + ('#'*64 + '\n')*5, file=fileobj)

	if nsfwmode == 1 or nsfwmode == 2:
		for member in nsfwyes:
			print(str(member).replace("'", ''), file=fileobj)
		print('\n' + ('#'*64 + '\n')*5, file=fileobj)

	if nsfwmode == 2:
		for member in nsfwq:
			print(str(member).replace("'", ''), file=fileobj)


def nearby(ranged=16, nsfwmode=2, doreturn=False):
	"""
	Find subreddits whose birthdays are coming up
	int ranged= How many subs to attempt showing
	int nsfwmode=
	  0 - Clean only
	  1 - Dirty only
	  2 - All
     """
	#find upcoming birthdays
	cur.execute('SELECT * FROM subreddits WHERE NAME!=?', ['?'])
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
		
	nowentry = ['Today', int("%0.0f" % now.timestamp()), datetime.datetime.strftime(now, "%m %d %Y %H:%M:%S UTC"), 'NSFW:X', '##########']
	fetched.append(nowentry)
	fetched.sort(key=lambda x: (x[2][:6] + x[2][11:]))

	nowindex = fetched.index(nowentry)
	results.append(nowentry)
	results.append('')
	for item in fetched[nowindex+1:nowindex+ranged+1]:
		if (item[3] == 'NSFW:1' and nsfwmode==1) or (item[3] == 'NSFW:0' and nsfwmode==0) or nsfwmode == 2:
			results.append(item)


	if doreturn:
		return results
	else:
		for item in results:
			item = str(item)
			item = item.replace("'", '')
			print(item)
	

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

def processir(startingpoint, ranger, newmode=False):
	"""
	Process a range of values starting from a specified point
	*str startingpoint= The ID of the subreddit to start at
	**int startingpoint= The b36 value of the subreddit's ID
	*int ranger= The number of subs after startingpoint to collect
	"""
	#Take subreddit ID as starting point and grab the next ranger items
	global olds
	olds = 0
	if type(startingpoint) == str:
		startingpoint = b36(startingpoint)
	for pos in range(startingpoint, startingpoint+ranger):
		newpoint = b36(pos).lower()
		try:
			processi(newpoint)
		except (AttributeError, praw.requests.exceptions.HTTPError):
			if not newmode:
				print('Failure', newpoint)
				cur.execute('INSERT INTO subreddits VALUES(?, ?, ?, ?, ?)', [newpoint, 0, '', '', '?'])
				olds += 1
				sql.commit()
			else:
				break

	print("Rejected", olds)

def processmulti(user, multiname):
	"""
	Process a user's multireddit
	*str user= username
	*str multiname= the name of the multireddit
	"""
	multiurl = 'http://www.reddit.com/api/multi/user/' + user + '/m/' + multiname
	multipage = urllib.request.urlopen(multiurl)
	multijson = json.loads(multipage.read().decode('utf-8'))
	for key in multijson['data']['subreddits']:
		process(key['name'])

def processrand(count, doublecheck=False, sleepy=0):
	"""
	Gets random IDs between a known lower bound and the newest collection
	*int count= How many you want
	bool doublecheck= Should it reroll duplicates before running
	int sleepy= Used to sleep longer than the reqd 2 seconds
	"""
	global olds
	olds = 0
	lower = 4594411
	#4594300 = 2qgzg
	#4594411 = 2qh2j
	cur.execute('SELECT * FROM subreddits')
	fetched = cur.fetchall()
	fetched.sort(key=lambda x:x[1])
	upper = fetched[-1][0]
	print('<' + b36(lower).lower() + ',',  upper + '>', end=', ')
	upper = b36(upper)
	totalpossible = upper-lower
	print(totalpossible, 'possible')
	rands = []
	if doublecheck:
		allids = [x[0] for x in fetched]
	for x in range(count):
		rand = random.randint(lower, upper)
		rand = b36(rand).lower()
		if doublecheck:
			while rand in allids or rand in rands:
				if rand in allids:
					print('Old:', rand, 'Rerolling: in allid')
				else:
					print('Old:', rand, 'Rerolling: in rands')
				rand = random.randint(lower, upper)
				rand = b36(rand).lower()
				olds += 1
		rands.append(rand)

	for randid in rands:
		#print(randid)
		try:
			processi(randid)
			time.sleep(sleepy)
		except AttributeError:
			print(randid, 'Failed')
		except praw.requests.exceptions.HTTPError:
			print(randid, 'HTTPError')
	print('Rejected', olds)

def processnew():
	"""
	Take the newest subreddit available, and start searching for ones newer
	"""
	cur.execute('SELECT * FROM subreddits')
	fetched = cur.fetchall()
	fetched.sort(key=lambda x:x[1])
	upper = fetched[-1][0]
	try:
		processir(upper, 100000, newmode=True)
	except AttributeError:
		print('Break')

def processnewest():
	brandnewest = list(r.get_new_subreddits(limit=1))[0]
	processi(brandnewest.id)

def search(query="", casesense=False, filterout=[], nsfwmode=2, idd=""):
	"""
	Search for a subreddit by name
	*str query= The search query
	    "query"    = results where "query" is in the name
	    ":query"   = results where "query" is at the end of the name
	    "query:"   = results where "query" is at the beginning of the name
	    ":querry:" = results where "query" is in the middle of the name
	bool casesense = is the search case sensitive
	list filterout = [list, of, words] to omit from search. Follows casesense
	int nsfwmode=
	  0 - Clean only
	  1 - Dirty only
	  2 - All
	"""

	if idd == "":
		cur.execute('SELECT * FROM subreddits WHERE NAME !=?', ['?'])
		fetched = cur.fetchall()
		fetched.sort(key=lambda x: x[4].lower())

		results = []
		if not casesense:
			query = query.lower()
			for x in range(len(filterout)):
				filterout[x] = filterout[x].lower()

		#print(len(fetched))
		for subreddit in fetched:
			item = subreddit[4]
			if nsfwmode==2 or (subreddit[3] == "NSFW:1" and nsfwmode == 1) or (subreddit[3] == "NSFW:0" and nsfwmode == 0):
				if not casesense:
					item = item.lower()
				querl = query.replace(':', '')
				if querl in item:
					#print(item)
					if all(filters not in item for filters in filterout):
						itemsplit = item.split(querl)
						if ':' in query:
							if (query[-1] == ':' and query[0] != ':') and itemsplit[0] == '':
								results.append(subreddit)
				
							if (query[0] == ':' and query[-1] != ':') and itemsplit[-1] == '':
								results.append(subreddit)
				
							if (query[-1] == ':' and query[0] == ':') and (itemsplit[0] != '' and itemsplit[-1] != ''):
								results.append(subreddit)
			
						else:
							results.append(subreddit)
					else:
						#print('Filtered', item)
						pass

		for item in results:
			item = str(item)
			item = item.replace("'", '')
			print(item)
		print()

	else:
		cur.execute('SELECT * FROM subreddits WHERE ID=?', [idd])
		f = cur.fetchone()
		print(f)

def cls():
	os.system('cls')

def count():
	cur.execute('SELECT * FROM subreddits WHERE NAME!=?', ['?'])
	print(len(cur.fetchall()))

def findwrong():
	cur.execute('SELECT * FROM subreddits WHERE NAME!=?', ['?'])
	fetch = cur.fetchall()
	fetch.sort(key=lambda x: b36(x[0]))
	#sorted by ID
	fetch = fetch[25:]
	
	pos = 0
	l = []

	while pos < len(fetch)-5:
		if fetch[pos][1] > fetch[pos+1][1]:
			l.append(str(fetch[pos-1]))
			l.append(str(fetch[pos]))
			l.append(str(fetch[pos+1]) + "\n")
		pos += 1

	for x in l:
		print(x)

def findholes(count, doreturn=False):
	cur.execute('SELECT * FROM subreddits WHERE NAME!=?', ['?'])
	fetch = cur.fetchall()
	fetch.sort(key=lambda x: b36(x[0]))
	#sorted by ID
	fetch = fetch[25:]
	fetch = [f[0] for f in fetch]

	current = 0
	holes = []
	pos = b36(fetch[0])
	while pos < b36(fetch[-1]):
		i = b36(pos).lower()
		if i not in fetch:
			current += 1
			holes.append(i)
		pos += 1

		if current >= count:
			break
	if doreturn:
		return holes
	else:
		for h in holes:
			print(h)

def fillholes(count):
	"""
	Used to fill ID gaps instead of relying on processrand or processir
	Fills holes sequentially by ID
	*int count = How many holes to fill
	"""
	holes = findholes(count, True)
	for hole in holes:
		processi(hole)
		time.sleep(2.2)