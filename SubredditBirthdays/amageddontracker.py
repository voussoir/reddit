import time
import sqlite3
import praw
import bot
import datetime

sql = sqlite3.connect('sql.db')
cur = sql.cursor()
cur2 = sql.cursor()

cur.execute('CREATE INDEX IF NOT EXISTS amaindex ON amageddon(idint)')
r = bot.rG()

DEFAULTS = [
'announcements','Art','AskReddit','askscience','aww',
'blog','books','creepy','dataisbeautiful','DIY','Documentaries',
'EarthPorn','explainlikeimfive','Fitness','food','funny',
'Futurology','gadgets','gaming','GetMotivated','gifs','history',
'IAmA','InternetIsBeautiful','Jokes','LifeProTips','listentothis',
'mildlyinteresting','movies','Music','news','nosleep','nottheonion',
'OldSchoolCool','personalfinance','philosophy','photoshopbattles',
'pics','science','Showerthoughts','space','sports','television',
'tifu','todayilearned','TwoXChromosomes','UpliftingNews','videos',
'worldnews','WritingPrompts']

SQL_COLUMNCOUNT = 10
SQL_IDINT = 0
SQL_IDSTR = 1
SQL_CREATED = 2
SQL_HUMAN = 3
SQL_NAME = 4
SQL_NSFW = 5
SQL_SUBSCRIBERS = 6
SQL_JUMBLE = 7
SQL_SUBREDDIT_TYPE = 8
SQL_SUBMISSION_TYPE = 9

def now():
	return datetime.datetime.now(datetime.timezone.utc).timestamp()

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

def get_hundred():
	cur.execute('SELECT * FROM subreddits WHERE subscribers > 50 AND subreddit_type != 2 ORDER BY subscribers DESC')
	while True:
		hundred = [cur.fetchone() for x in range(100)]
		hundred = list(filter(None, hundred))
		if len(hundred) == 0:
			print('Run finished.')
			break
		yield hundred

def human(timestamp):
	day = datetime.datetime.utcfromtimestamp(timestamp)
	human = datetime.datetime.strftime(day, "%d%b %H:%M")
	return human

def manage():
	hundredg = get_hundred()
	for hundred in hundredg:
		print('checking %s - %s %d' % (hundred[0][SQL_NAME], hundred[-1][SQL_NAME], hundred[-1][SQL_SUBSCRIBERS]))
		subreddits = r.get_info(thing_id=['t5_' + x[SQL_IDSTR] for x in hundred])
		hundred.sort(key=lambda x: x[SQL_CREATED])
		subreddits.sort(key=lambda x: x.created_utc)

		for sub in subreddits:
			for item in hundred:
				if item[SQL_IDSTR] == sub.id:
					sub.previous = item[SQL_SUBREDDIT_TYPE]
					sub.psubs = item[SQL_SUBSCRIBERS]

		for sub in subreddits:
			if sub.previous == 2:
				continue

			idint = b36(sub.id)
			cur2.execute('SELECT * FROM amageddon WHERE idint == ?', [idint])
			f = cur2.fetchone()
			if f:
				if sub.subreddit_type == 'private' and f[-1] is not None:
					cur2.execute('UPDATE amageddon SET returntime=? WHERE idint=?', [None, idint])
					print('  [PRIVATE] %s' % sub._fast_name)
					continue
				if sub.subreddit_type == 'private' or f[-1] is not None:
					continue
				returntime = int(now())
				print('     [OPEN] %s' % sub._fast_name)
				cur2.execute('UPDATE amageddon SET returntime=? WHERE idint=?', [returntime, idint])
			else:
				if sub.subreddit_type != 'private':
					continue
				data = [idint, sub.id, sub._fast_name, sub.psubs, None]
				print('  [PRIVATE] %s' % sub._fast_name)
				cur2.execute('INSERT INTO amageddon VALUES(?, ?, ?, ?, ?)', data)
		sql.commit()

def show():
	cur2.execute('SELECT * FROM amageddon ORDER BY subscribers DESC')
	outtotal = ''
	bonus = ''
	outtotal += '[**THIS PAGE IS HITTING THE CHARACTER LIMIT. CHECK THE WIKI PAGE FOR FULL TEXT.**]'
	outtotal += '(https://reddit.com/r/GoldTesting/wiki/amageddon)\n\n'
	#outtotal += 'I am currently AFK, letting the bot do its work. I hope it doesn\'t crash!\n\n'
	outtotal += 'This is a list of subreddits which became private at some point during the AMAgeddon.\n\n'
	outtotal += 'The subscriber counts are based on the last time I scanned them, which was, like, 2 days ago maybe.\n\n'
	outtotal += '{down} down  \n{up} up  \n{total} total\n\n'
	outtotal += 'ID|NAME|SUBSCRIBERS|REINSTATED (UTC)\n'
	outtotal += '-:|:-|-:|-:\n'
	down = 0
	up = 0
	total = 0
	while True:
		item = cur2.fetchone()
		if item is None:
			break
		item = list(item)
		if item[-1] is None:
			item[-1] = ''
			down += 1
		else:
			item[-1] = human(int(item[-1]))
			up += 1
		item = item[1:]
		if item[1] in DEFAULTS:
			item[1] = '%s ^D' % item[1]
		item[1] = 'r/' + item[1]
		subscribers = item[2]
		item[2] = '{:,}'.format(item[2])
		itemf = '|'.join(item) + '\n'
		if len(outtotal) < 39900:
			outtotal += itemf
		else:
			bonus += itemf
		total += 1
	outtotal = outtotal.format(up=up, down=down, total=total)
	print(len(outtotal))
	outfile = open('amageddon/outfile.txt', 'w')
	outfile.write(outtotal)
	outfile.close()
	if len(outtotal) > 40000:
		outtotal = outtotal[:40000]
	submission = r.get_info(thing_id='t3_3bypzz')
	submission.edit(outtotal)
	outtotal += bonus
	s = r.get_subreddit('goldtesting')
	s.edit_wiki_page('amageddon', outtotal)
	print(total)

def forever():
	while True:
		try:
			manage()
		except KeyboardInterrupt:
			break
		except:
			pass
		try:
			show()
		except:
			pass
		time.sleep(15)

def resetcur():
	cur.execute('SELECT * FROM amageddon WHERE idint==0')