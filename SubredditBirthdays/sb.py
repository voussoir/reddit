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
import tkinter
import subprocess

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
cur.execute('CREATE TABLE IF NOT EXISTS subreddits(ID TEXT, CREATED INT, HUMAN TEXT, NSFW TEXT, NAME TEXT, SUBSCRIBERS INT, JUMBLE INT, IDINT INT, SUBREDDIT_TYPE INT, SUBMISSION_TYPE INT, IS_SPAM INT)')
cur.execute('CREATE TABLE IF NOT EXISTS jumble(ID TEXT, CREATED INT, HUMAN TEXT, NSFW TEXT, NAME TEXT, SUBSCRIBERS INT)')
cur.execute('CREATE TABLE IF NOT EXISTS etc(LABEL TEXT, DATA TEXT, DATB TEXT, DATC TEXT)')
print('Loaded SQL Database')
sql.commit()

r = praw.Reddit(USERAGENT)
print('Connected to reddit.')

olds = 0
noinfolist = []
errormess = None
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

SUBREDDIT_TYPE = {
	'public':0,
	'restricted':1,
	'private':2,
	'archived':3,
	None:4,
	'employees_only':5,
	'gold_restricted':6,
	'gold_only':6
}
SUBMISSION_TYPE = {
	'any':0,
	'link':1,
	'self':2,
	None:3
}

def human(timestamp):
	day = datetime.datetime.utcfromtimestamp(timestamp)
	human = datetime.datetime.strftime(day, "%b %d %Y %H:%M:%S UTC")
	return human

def processi(sr, doupdates=True, enablekilling=False):
	global olds
	if 't5_' not in sr:
		sr = 't5_' + sr
	cur.execute('SELECT * FROM subreddits WHERE IDINT=?', [b36(sr[3:])])
	if not cur.fetchone() or doupdates==True:
		sro = r.get_info(thing_id=sr)
		try:
			sro.id
			process(sro)
		except AttributeError:
			print('Could not fetch subreddit')
			if enablekilling:
				i = input('Kill?\n> ')
				if i.lower() == 'y':
					kill(sr[3:])
	else:
		olds += 1

def process(sr, database="subreddits", delaysaving=False, doupdates=True, isjumbled=False):
	global olds
	subs = []

	if type(sr) == str:
		for splitted in sr.split(','):
			splitted = splitted.replace(' ', '')
			if doupdates==False:
				cur.execute('SELECT * FROM subreddits WHERE LOWER(NAME)=?', [splitted.lower()])
				if not cur.fetchone():
					sr = r.get_subreddit(splitted)
					subs.append(sr)
				else:
					olds += 1
					pass
			else:
				sr = r.get_subreddit(splitted)
				subs.append(sr)

	elif type(sr) == praw.objects.Submission or type(sr) == praw.objects.Comment:
		sr = sr.subreddit
		subs.append(sr)

	else:
		subs.append(sr)

	for sub in subs:
		try:
			idint = b36(sub.id)
			cur.execute('SELECT * FROM subreddits WHERE IDINT=?', [idint])
			f = cur.fetchone()
			if not f:
				h = human(sub.created_utc)
				isnsfw = '1' if sub.over18 else '0'
				subscribers = sub.subscribers if sub.subscribers else 0
				isjumbled = '1' if isjumbled else '0'
				print('New: %s : %s : %s : %s : %d' % (sub.id, h, isnsfw, sub.display_name, subscribers))
				subreddit_type = SUBREDDIT_TYPE[sub.subreddit_type]
				submission_type = SUBMISSION_TYPE[sub.submission_type]
				cur.execute('INSERT INTO subreddits VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
					[sub.id, sub.created_utc, h, isnsfw, sub.display_name, subscribers, isjumbled, idint, subreddit_type, submission_type, -1])
			elif doupdates:
				if sub.subscribers != None:
					subscribers = sub.subscribers
				else:
					subscribers = 0
				h = human(sub.created_utc)
				isnsfw = '1' if sub.over18 else '0'
				isjumbled = '1' if isjumbled else '0'
				subreddit_type = SUBREDDIT_TYPE[sub.subreddit_type]
				submission_type = SUBMISSION_TYPE[sub.submission_type]
				oldsubs = f[5]
				subscriberdiff = subscribers - oldsubs
				print('Upd: %s : %s : %s : %s : %d (%d)' % (sub.id, h, isnsfw, sub.display_name, subscribers, subscriberdiff))
				cur.execute('UPDATE subreddits SET SUBSCRIBERS=?, JUMBLE=?, SUBREDDIT_TYPE=?, SUBMISSION_TYPE=? WHERE IDINT=?',
					[subscribers, isjumbled, subreddit_type, submission_type, idint])
				olds += 1
			else:
				olds += 1
			if not delaysaving:
				sql.commit()
		except praw.requests.exceptions.HTTPError:
			print('HTTPError:', sub)
	sql.commit()


def chunklist(inputlist, chunksize):
	if len(inputlist) < chunksize:
		return [inputlist]
	else:
		outputlist = []
		while len(inputlist) > 0:
			outputlist.append(inputlist[:chunksize])
			inputlist = inputlist[chunksize:]
		return outputlist

def processmega(srinput, isrealname=False, chunksize=100, docrash=False, delaysaving=False, doupdates=True):
	global olds
	global noinfolist
	#This is the new standard in sr processing
	#Other methods will be deprecated
	#Heil
	if type(srinput) == str:
		srinput = srinput.replace(' ', '')
		srinput = srinput.split(',')

	if isrealname == False:
		remaining = len(srinput)
		for x in range(len(srinput)):
			if 't5_' not in srinput[x]:
				srinput[x] = 't5_' + srinput[x]
		srinput = chunklist(srinput, chunksize)
		for subset in srinput:
			try:
				print(subset[0] + ' - ' + subset[-1], remaining)
				subreddits = r.get_info(thing_id=subset)
				try:
					for sub in subreddits:
						process(sub, delaysaving=delaysaving, doupdates=doupdates)
				except TypeError:
					print('Received no info. See variable `noinfolist`')
					noinfolist = subset[:]
				remaining -= len(subset)
			except praw.requests.exceptions.HTTPError as e:
				print(e)
				print(vars(e))
				if docrash:
					raise Exception("I've been commanded to crash")
	else:
		for subname in srinput:
			process(subname)


def processrand(count, doublecheck=False, sleepy=0, delaysaving=False, doupdates=True):
	"""
	Gets random IDs between a known lower bound and the newest collection
	*int count= How many you want
	bool doublecheck= Should it reroll duplicates before running
	int sleepy= Used to sleep longer than the reqd 2 seconds
	"""
	global olds
	olds = 0
	cur.execute('SELECT * FROM etc WHERE LABEL=?', ['lowerbound'])
	lower = cur.fetchone()
	lower = int(lower[2])

	cur.execute('SELECT * FROM subreddits ORDER BY IDINT DESC LIMIT 1')
	upper = cur.fetchone()[0]
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

	rands.sort()
	processmega(rands, delaysaving=delaysaving, doupdates=doupdates)

	print('Rejected', olds)

def processir(startingpoint, ranger, chunksize=100, slowmode=False, enablekilling=False, doupdates=False):
	"""
	Process a range of values starting from a specified point
	*str startingpoint= The ID of the subreddit to start at
	**int startingpoint= The b36 value of the subreddit's ID
	*int ranger= The number of subs after startingpoint to collect
	"""
	#Take subreddit ID as starting point and grab the next ranger items
	global olds
	startingdigit = b36(startingpoint)
	if isinstance(ranger, str):
		ranger = b36(ranger)
		ranger -= startingdigit
		print('Created range', ranger)
	olds = 0
	ranged = list(range(startingdigit, startingdigit+ranger))
	for x in range(len(ranged)):
		ranged[x] = b36(ranged[x]).lower()
	cur.execute('SELECT * FROM subreddits')
	fetch = cur.fetchall()
	if not doupdates:
		for item in fetch:
			if item[0] in ranged:
				ranged.remove(item[0])
				print("dropped", item[0])
	#print(ranged)
	if len(ranged) > 0:
		if slowmode == False:
			processmega(ranged, chunksize=chunksize, doupdates=doupdates)
		else:
			for slowsub in ranged:
				try:
					processi(slowsub, doupdates=True)
				except praw.requests.exceptions.HTTPError as e:
					response = str(e.response)
					if '[500]>' in response:
						print('500 error:', slowsub)
						if enablekilling:
							kill(slowsub)
		print("Rejected", olds)

def kill(sr):
	cur.execute('INSERT INTO subreddits VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [sr, 0, '', '', '?', 0, '0', b36(sr), 0, 0, -1])
	sql.commit()


def get(limit=20, doupdates=False):
	global olds
	subreddit = r.get_subreddit('all')
	listed = []
	print('Getting new')
	new = list(subreddit.get_new(limit=limit))
	print('Getting comments')
	coms = list(subreddit.get_comments(limit=limit))
	listed += new + coms
	olds = 0
	listed = [l.subreddit_id for l in listed]
	processmega(listed)
	sql.commit()
	print('Rejected', olds)

def show():
	filea = open('show\\all-time.txt', 'w')
	fileb = open('show\\all-dom.txt', 'w')
	filec = open('show\\all-name.txt', 'w')
	#filed = open('show\\allx-name.txt', 'w')
	#filee = open('show\\allx-time.txt', 'w')
	#filef = open('show\\clean-time.txt', 'w')
	#fileg = open('show\\clean-name.txt', 'w')
	fileh = open('show\\dirty-time.txt', 'w')
	filei = open('show\\dirty-name.txt', 'w')
	#filej = open('show\\allx-dom.txt', 'w')
	#filek = open('show\\clean-dom.txt', 'w')
	filel = open('show\\dirty-dom.txt', 'w')
	filem = open('show\\statistics.txt', 'w')
	filen = open('show\\missing.txt', 'w')
	fileo = open('show\\all-marked.txt', 'w')
	filep = open('README.md', 'r')
	fileq = open('show\\duplicates.txt', 'w')
	filer = open('show\\jumble.txt', 'w')
	files = open('show\\all-subscribers.txt', 'w')
	filet = open('show\\dirty-subscribers.txt', 'w')
	fileu = open('show\\jumble-nsfw.txt', 'w')
	cur.execute('SELECT * FROM subreddits WHERE CREATED !=?', [0])
	fetch = cur.fetchall()
	itemcount = len(fetch)
	print(str(itemcount) + ' items.')

	fetch.sort(key=lambda x: x[1])
	print('Writing time files')
	print(str(itemcount) + ' subreddits sorted by true time', file=filea)
	for member in fetch:
		print(memberformat(member), file=filea)
	filea.close()
	#shown(fetch, 'Sorted by nsfw by true time', filee)
	#filee.close()
	#shown(fetch, 'Clean only sorted by true time', filef, nsfwmode=0)
	#filef.close()
	shown(fetch, 'Nsfw only sorted by true time', fileh, nsfwmode=1)
	fileh.close()

	cur.execute('SELECT * FROM subreddits')
	allfetch = cur.fetchall()
	allfetch.sort(key=lambda x: b36(x[0]))

	last20k = allfetch[-20000:]

	previd = allfetch[0][0]
	print('Writing marked file')
	print('Sorted by ID number gaps marked', file=fileo)
	print('#= Unknown subreddit.   $= Verified missing', file=fileo)
	c=0
	totalc = 0
	for member in allfetch:
		curid = member[0]
		iddiff = b36(curid) - b36(previd)
		if iddiff > 1:
			print('#' + str(iddiff-1), file=fileo)
		if member[1] != 0:
			if c > 0:
				print('$' + str(c), file=fileo)
			print(memberformat(member), file=fileo)
			c=0
		else:
			if b36(member[0]) > 4594300:
				c+=1
				totalc += 1
		previd = curid
	fileo.close()
	del allfetch
	itemcount += totalc

	print('Writing statistics')
	totalpossible = b36(fetch[-1][0]) - 4594260
	headliner = 'Collected '+'{0:,}'.format(itemcount)+' of '+'{0:,}'.format(totalpossible)+' subreddits ('+"%0.03f"%(100*itemcount/totalpossible)+'%)'
	headliner+= ' ({0:,} remain)'.format(totalpossible-itemcount) + '\n'
	#Call the PEP8 police on me, I don't care
	print(headliner, file=filem)
	cur.execute('SELECT * FROM subreddits WHERE NSFW=?', ['1'])
	nsfwyes = cur.fetchall()
	nsfwyes = len(nsfwyes)
	statisticoutput = []

	timedicts = generatetdicts(fetch)
	dowdict = timedicts[0]
	moydict = timedicts[1]
	hoddict = timedicts[2]
	yerdict = timedicts[3]
	myrdict = timedicts[4]
	domdict = timedicts[5]

	for d in [dowdict, moydict, hoddict, yerdict, myrdict, domdict]:
		#d = dict(zip(d.keys(), d.values()))
		dkeys = list(d.keys())
		dkeys.sort(key=d.get)
		for nk in dkeys:
			nks = str('{0:,}'.format(d.get(nk)))
			statisticoutput.append(nk + ': ' + ('.' * (14-len(nk))) + ('.' * (10-len(nks))) + nks)
		statisticoutput.append('\n')

	#print(statisticoutput)
	pos = 0
	for d in [dowdict, moydict, hoddict, yerdict, myrdict, domdict]:
		d = dict(zip(d.keys(), d.values()))
		dkeys = list(d.keys())
		dkeys = specialsort(dkeys)
		#print(dkeys)
		for nk in dkeys:
			nks = str('{0:,}'.format(d.get(nk)))
			statisticoutput[pos] = statisticoutput[pos] + ' '*8 + nk + ': ' + ('.' * (10-len(nk))) + ('.' * (12-len(nks))) + nks
			pos += 1
		pos += 1

	#See line 329 for the source of `last20k`
	statisticoutput.append('Based on the last 20,000 subreddits, ' + last20k[0][0] + '-' + last20k[-1][0])
	now = datetime.datetime.now(datetime.timezone.utc).timestamp()
	then = last20k[0][1]
	timediff = now-then
	subsperhour = "%.2f" % (20000 / (timediff/3600))
	subsperday = "%.2f" % (20000 / (timediff/86400))
	statisticoutput.append(subsperhour + ' subs are created each hour')
	statisticoutput.append(subsperday + ' subs are created each day\n')

	statisticoutput.append('NSFW 0: ' + str('{0:,}'.format(itemcount-nsfwyes)))
	statisticoutput.append('NSFW 1: ' + str('{0:,}'.format(nsfwyes)))

	#print(statisticoutput)
	statisticoutput = '\n'.join(statisticoutput)

	print(statisticoutput, file=filem)
	filem.close()
	plotnum = 0
	for d in [dowdict, moydict, hoddict, yerdict, myrdict, domdict]:
		dkeys = list(d.keys())
		dkeys = specialsort(dkeys)
		dvals = [d[x] for x in dkeys]
		#e0e6c3
		plotbars(str(plotnum), [dkeys, dvals], colorbg="#272822", colorfg="#000", colormid="#43443a", forcezero=True)
		plotnum += 1
		if d is myrdict:
			plotbars(str(plotnum), [dkeys[-15:], dvals[-15:]], colorbg="#272822", colorfg="#000", colormid="#43443a", forcezero=True)
			plotnum += 1
	subprocess.Popen('PNGCREATOR.bat', shell=True, cwd='spooky')

	if random.randint(0, 20) == 5:
		print('Reticulating splines')

	sys.stdout.flush()
	print('Writing Readme')
	readmeread = filep.readlines()
	filep.close()
	readmeread[3] = '#####' + headliner
	readmeread[5] = '#####' + "[Today's jumble](http://reddit.com/r/" + jumble(doreturn=True)[0] + ")\n"
	filep = open('README.md', 'w')
	filep.write(''.join(readmeread))
	filep.close()


	fetch.sort(key=lambda x: x[4].lower())
	print('Writing name files')
	print('Sorted by name', file=filec)
	for member in fetch:
		print(memberformat(member), file=filec)
	filec.close()
	#shown(fetch, 'Sorted by nsfw by name', filed)
	#filed.close()
	#shown(fetch, 'Clean only sorted by name', fileg, nsfwmode=0)
	#fileg.close()
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
		print(memberformat(member), file=fileb)
	fileb.close()
	#shown(l, 'Sorted by nsfw by day of month', filej)
	#filej.close()
	#shown(l, 'Clean only sorted by day of month', filek, nsfwmode=0)
	#filek.close()
	shown(l, 'Nsfw only sorted by day of month', filel, nsfwmode=1)
	filel.close()

	l.sort(key=lambda x:x[5])
	l.reverse()
	print('Writing subscriber files')
	print('Sorted by subscriber count', file=files)
	for member in l:
		print(memberformat(member), file=files)
	files.close()
	shown(l, 'Nsfw only sorted by subscriber count', filet, nsfwmode=1)
	filet.close()

	print('Writing missingnos')
	cur.execute('SELECT * FROM subreddits WHERE CREATED=?', [0])
	fetch = cur.fetchall()
	fetch.sort(key=lambda x: b36(x[0]))
	fetch = (f[0] for f in fetch)
	for member in fetch:
		stopchecking = False
		if stopchecking == True or b36(member) >= 4594339:
			print(member, file=filen)
			stopchecking = True
	filen.close()

	print('Writing duplicates')
	dupes = finddupes(True)
	for member in dupes:
		print(memberformat(member), file=fileq)
	fileq.close()

	print('Writing jumble')
	print('These are the subreddits that can be found from /r/random', file=filer)
	print('These are the subreddits that can be found from /r/randnsfw', file=fileu)
	cur.execute('SELECT * FROM subreddits WHERE JUMBLE=?', ['1'])
	fetch = cur.fetchall()
	fetch.sort(key= lambda x:x[5])
	fetch.reverse()
	for member in fetch:
		if member[3] == '0':
			print(memberformat(member), file=filer)
		else:
			print(memberformat(member), file=fileu)
	filer.close()
	fileu.close()

def generatetdicts(fetch):
	dowdict = {}
	moydict = {}
	hoddict = {}
	yerdict = {}
	myrdict = {}
	domdict = {}

	for item in fetch:
		itemdate = datetime.datetime.utcfromtimestamp(item[1])
		dowdict = dictadding(dowdict, datetime.datetime.strftime(itemdate, "%A"))
		moydict = dictadding(moydict, datetime.datetime.strftime(itemdate, "%B"))
		hoddict = dictadding(hoddict, datetime.datetime.strftime(itemdate, "%H"))
		yerdict = dictadding(yerdict, datetime.datetime.strftime(itemdate, "%Y"))
		myrdict = dictadding(myrdict, datetime.datetime.strftime(itemdate, "%b%Y"))
		domdict = dictadding(domdict, datetime.datetime.strftime(itemdate, "%d"))
	return [dowdict, moydict, hoddict, yerdict, myrdict, domdict]

def memberformat(member, spacer='.'):
	subscribers = '{0:,}'.format(member[5])
	name = member[4]
	member = str(member[:4])[1:-1]
	member += ', '
	member += name
	member += spacer* (78 - len(member))
	if '\n' in member:
		member = member[:-1]
	member += spacer* (10 - len(subscribers))
	member += subscribers
	member = member.replace("'", '')
	member = repr(member)
	member = member[1:-1]
	return member


def dictadding(targetdict, item):
	if item not in targetdict:
		targetdict[item] = 1
	else:
		targetdict[item] = targetdict[item] + 1
	return targetdict

def specialsort(inlist):
	if 'December' in inlist:
		return ['January', 'February', 'March', \
				'April', 'May', 'June', 'July', \
				'August', 'September', 'October', \
				'November', 'December']
	if 'Monday' in inlist:
		return ['Sunday', 'Monday', 'Tuesday', \
				'Wednesday', 'Thursday', 'Friday', \
				'Saturday']
	if 'Oct2014' in inlist:
		td = {}
		for item in inlist:
			nitem = item
			nitem = item.replace(item[:3], monthnumbers[item[:3]])
			nitem = nitem[3:] + nitem[:3]
			td[item] = nitem
		tdkeys = list(td.keys())
		#print(td)
		tdkeys.sort(key=td.get)
		#print(tdkeys)
		return tdkeys
	else:
		return sorted(inlist)


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
		if item[3] == '1':
			nsfwyes.append(item)
		elif item[3] == '?':
			nsfwq.append(item)
		else:
			nsfwno.append(item)
	print(header, file=fileobj)
	if nsfwmode == 0 or nsfwmode == 2:
		for member in nsfwno:
			print(memberformat(member), file=fileobj)
		print('\n' + ('#'*64 + '\n')*5, file=fileobj)

	if nsfwmode == 1 or nsfwmode == 2:
		for member in nsfwyes:
			print(memberformat(member), file=fileobj)
		print('\n' + ('#'*64 + '\n')*5, file=fileobj)

	if nsfwmode == 2:
		for member in nsfwq:
			print(memberformat(member), file=fileobj)


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
		
	nowentry = ['Today', int("%0.0f" % now.timestamp()), datetime.datetime.strftime(now, "%m %d %Y %H:%M:%S UTC"), 'X', '##########']
	fetched.append(nowentry)
	fetched.sort(key=lambda x: (x[2][:6] + x[2][11:]))

	nowindex = fetched.index(nowentry)
	results.append(nowentry)
	results.append('')
	for item in fetched[nowindex+1:nowindex+ranged+1]:
		if (item[3] == '1' and nsfwmode==1) or (item[3] == '0' and nsfwmode==0) or nsfwmode == 2:
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

def processmulti(user, multiname):
	"""
	Process a user's multireddit
	*str user= username
	*str multiname= the name of the multireddit
	"""
	multiurl = 'http://www.reddit.com/api/multi/user/' + user + '/m/' + multiname
	multipage = urllib.request.urlopen(multiurl)
	multijson = json.loads(multipage.read().decode('utf-8'))
	l = []
	for key in multijson['data']['subreddits']:
		l.append(key['id'])
		#process(key['name'])
	processmega(l)


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
	return brandnewest.id

def search(query="", casesense=False, filterout=[], subscribers=0, nsfwmode=2, idd="", doreturn=False):
	"""
	Search for a subreddit by name
	*str query= The search query
	    "query"    = results where "query" is in the name
	    "*query"   = results where "query" is at the end of the name
	    "query*"   = results where "query" is at the beginning of the name
	    "*querry*" = results where "query" is in the middle of the name
	bool casesense = is the search case sensitive
	list filterout = [list, of, words] to omit from search. Follows casesense
	int subscribers = minimum number of subscribers
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
			if nsfwmode==2 or (subreddit[3] == "1" and nsfwmode == 1) or (subreddit[3] == "0" and nsfwmode == 0):
				if not casesense:
					item = item.lower()
				querl = query.replace('*', '')
				if querl in item:
					#print(item)
					if all(filters not in item for filters in filterout):
						itemsplit = item.split(querl)
						if ':' in query:
							if (query[-1] == '*' and query[0] != '*') and itemsplit[0] == '':
								results.append(subreddit)
				
							if (query[0] == '*' and query[-1] != '*') and itemsplit[-1] == '':
								results.append(subreddit)
				
							if (query[-1] == '*' and query[0] == '*') and (itemsplit[0] != '' and itemsplit[-1] != ''):
								results.append(subreddit)
			
						else:
							results.append(subreddit)
					else:
						#print('Filtered', item)
						pass

		if not doreturn:
			for item in results:
				item = str(item)
				item = item.replace("'", '')
				print(item)
			print()
		else:
			return results

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

def finddupes(doreturn=False):
	cur.execute('SELECT * FROM subreddits WHERE NAME!=?', ['?'])
	fetch = cur.fetchall()
	fetch.sort(key=lambda x: x[4])
	pos = 0
	l = []

	while pos < len(fetch)-5:
		if fetch[pos][4].lower() == fetch[pos+1][4].lower():
			l.append(fetch[pos])
		elif fetch[pos][4].lower() == fetch[pos-1][4].lower():
			l.append(fetch[pos])
		pos += 1


	if doreturn:
		return l
	for x in l:
		print(x)

def findholes(count, doreturn=False):
	cur.execute('SELECT * FROM subreddits')
	fetch = cur.fetchall()
	fetch = [f[0] for f in fetch]
	fetch.sort(key=lambda x: b36(x))
	cur.execute('SELECT * FROM etc WHERE LABEL=?', ['lowerbound'])
	f = cur.fetchone()
	lower = fetch.index(f[1])
	print("lower: ", f[1])
	fetch = fetch[lower:]
	#sorted by ID

	current = 0
	holes = []
	pos = b36(fetch[0])
	while pos < b36(fetch[-1]):
		i = b36(pos).lower()
		if i not in fetch:
			print(i, '\r', end='')
			current += 1
			holes.append(i)
		pos += 1

		if current >= count:
			break
	print()
	if doreturn:
		return holes
	else:
		for h in holes:
			print(h)

def fillholes(count, chunksize=100):
	"""
	Used to fill ID gaps instead of relying on processrand or processir
	Fills holes sequentially by ID
	*int count = How many holes to fill
	"""
	remainder = count
	while remainder > 0:
		if remainder > chunksize:
			holes = findholes(chunksize, True)
			remainder -= chunksize
		else:
			holes = findholes(remainder, True)
			remainder = 0
		try:
			processmega(holes, docrash=True)
			fin = holes[-1]
			fin = fin[3:]
			print(fin)
			cur.execute('UPDATE etc SET DATA=?, DATB=? WHERE LABEL=?', [fin, b36(fin), 'lowerbound'])
			sql.commit()
		except:
			print('CRASH initiating slowmode')
			processir(holes[0][3:], chunksize, slowmode=True, enablekilling=True)
		print(remainder, "remaining")

def forcelowest(instring):
	cur.execute('UPDATE etc SET DATA=?, DATB=? WHERE LABEL=?', [instring, b36(instring), 'lowerbound'])
	sql.commit()

def processjumble(count, nsfw=False):
	for x in range(count):
		sub = r.get_random_subreddit(nsfw=nsfw)
		process(sub, isjumbled=True, doupdates=True)
		#else:
		#	print('Upd: ' + sub.id + ' '+ sub.display_name + ' : ' + str(sub.subscribers))
		#cur.execute('UPDATE subreddits SET JUMBLE=? WHERE ID=?', [sub.subscribers, '1', sub.id])
		sql.commit()


def jumble(count=20, doreturn=False, nsfw=False):
	nsfw = '1' if nsfw else '0'
	cur.execute('SELECT * FROM subreddits WHERE JUMBLE=? AND NSFW=?', ['1', nsfw])
	fetch = cur.fetchall()
	random.shuffle(fetch)
	fetch = fetch[:count]
	fetch = [f[:-1] for f in fetch]
	fetchstr = [i[4] for i in fetch]
	fetchstr = '+'.join(fetchstr)
	output = [fetchstr, fetch]
	if doreturn:
		return output
	print(output[0])
	for x in output[1]:
		print(str(x).replace("'", ''))

def modsfromid(subid):
	if 't5_' not in subid:
		subid = 't5_' + subid
	sub = r.get_info(thing_id=subid)
	mods = list(sub.get_moderators())
	for m in mods:
		print(m)
	return mods

def modernize():
	cur.execute('SELECT * FROM subreddits')
	f=cur.fetchall()
	f.sort(key=lambda x: x[1])
	finalitem = f[-1]
	print('Current final item:')
	print(finalitem[2], finalitem[4])
	finalid = b36(finalitem[0])

	print('Newest item:')
	newestid = processnewest()
	newestid = b36(newestid)
	

	modernlist = []
	for x in range(finalid, newestid):
		modernlist.append(b36(x).lower())
	processmega(modernlist)

def rounded(x, rounding=100):
	return int(round(x/rounding)) * rounding

def plotbars(title, inputdata, colorbg="#fff", colorfg="#000", colormid="#888", forcezero=False):
	"""Create postscript vectors of data

	title = Name of the file without extension

	inputdata = A list of two lists. First list has the x axis labels, second list
	has the y axis data. x label 14 coresponds to y datum 14, etc.
	"""
	print('Printing', title)
	t=tkinter.Tk()

	canvas = tkinter.Canvas(t, width=3840, height=2160, bg=colorbg)
	canvas.pack()
	canvas.create_line(430, 250, 430,1755, width=10, fill=colorfg)
	#Y axis
	canvas.create_line(430,1750, 3590,1750, width=10, fill=colorfg)
	#X axis

	dkeys = inputdata[0]
	dvals = inputdata[1]
	entrycount = len(dkeys)
	availablespace = 3140
	availableheight= 1490
	entrywidth = availablespace / entrycount
	#print(dkeys, dvals, "Width:", entrywidth)

	smallest = min(dvals)
	bottom = int(smallest*0.75) - 5
	bottom = 0 if bottom < 8 else rounded(bottom, 10)
	if forcezero:
		bottom = 0
	largest = max(dvals)
	top = int(largest + (largest/5))
	top = rounded(top, 10)
	print(bottom,top)
	span = top-bottom
	perpixel = span/availableheight

	curx = 445
	cury = 1735

	labelx = 420
	labely = 255
	#canvas.create_text(labelx, labely, text=str(top), font=("Consolas", 72), anchor="e")
	labelspan = 130#(1735-255)/10
	canvas.create_text(175, 100, text="Subreddits created", font=("Consolas", 72), anchor="w", fill=colorfg)
	for x in range(12):
		value = int(top -((labely - 245) * perpixel))
		value = rounded(value, 10)
		value = '{0:,}'.format(value)
		canvas.create_text(labelx, labely, text=value, font=("Consolas", 72), anchor="e", fill=colorfg)
		canvas.create_line(430, labely, 3590, labely, width=2, fill=colormid)
		labely += labelspan

	for entrypos in range(entrycount):
		entry = dkeys[entrypos]
		entryvalue = dvals[entrypos]
		entryx0 = curx + 10
		entryx1 = entryx0 + (entrywidth-10)
		curx += entrywidth

		entryy0 = cury
		entryy1 = entryvalue - bottom
		entryy1 = entryy1/perpixel
		#entryy1 -= bottom
		#entryy1 /= perpixel
		entryy1 = entryy0 - entryy1
		#print(perpixel, entryy1)
		#print(entry, entryx0,entryy0, entryx1, entryy1)
		canvas.create_rectangle(entryx0,entryy0, entryx1,entryy1, fill=colorfg, outline=colorfg)

		font0x = entryx0 + (entrywidth / 2)
		font0y = entryy1 - 5

		font1y = 1760

		entryvalue = round(entryvalue)
		fontsize0 = len(str(entryvalue)) 
		fontsize0 = round(entrywidth / fontsize0) + 3
		fontsize0 = 100 if fontsize0 > 100 else fontsize0
		fontsize1 = len(str(entry))
		fontsize1 = round(1.5* entrywidth / fontsize1) + 5
		fontsize1 = 60 if fontsize1 > 60 else fontsize1
		canvas.create_text(font0x, font0y, text=entryvalue, font=("Consolas", fontsize0), anchor="s", fill=colorfg)
		canvas.create_text(font0x, font1y, text=entry, font=("Consolas", fontsize1), anchor="n", fill=colorfg)
		canvas.update()
	print('\tDone')
	canvas.postscript(file='spooky\\' +title+".ps", width=3840, height=2160)
	t.geometry("1x1+1+1")
	t.update()
	t.destroy()