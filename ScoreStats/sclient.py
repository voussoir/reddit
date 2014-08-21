import sqlite3
import datetime
import gplot


g = gplot.Gnuplot()


def load():
	sql = sqlite3.connect('sql.db')
	cur = sql.cursor()
	print('Loaded SQL')
	return sql, cur

def fetchall():
	sql, cur = load()
	cur.execute('SELECT * FROM submissiondata')
	f = cur.fetchall()
	return f

def help():
	print('0: ID\n1: Created\n2: Title\n3: Score\n4: Subreddit\n5: Author')


def purge(l, time=0, score=0, subreddit='all'):
	f = []
	if type(subreddit) == str:
		s= subreddit.split(',')
		for m in range(len(s)):
			s[m] = s[m].strip()
		subreddit = s[:]
	purged = 0
	print('Time > ' + str(time), ', Score > ' + str(score), subreddit)
	for item in l:
		if (item[1] > time) and (item[3] > score) and (subreddit==['all'] or any(item[4].lower == s.lower for s in subreddit)):
			f.append(item)
		else:
			purged +=1
	print('Purged ' + str(purged) + ' items.')
	return f

def secondofday(timestamp):
	d= datetime.datetime.utcfromtimestamp(timestamp)
	hour = int(datetime.datetime.strftime(d, '%H'))
	minute = int(datetime.datetime.strftime(d, '%M'))
	second = int(datetime.datetime.strftime(d, '%S'))
	f = (3600 * hour) + (60 * minute) + (second)
	return f

def dayofweek(timestamp):
	d= datetime.datetime.utcfromtimestamp(timestamp)
	day = int(datetime.datetime.strftime(d, "%w"))
	return day

def secondofweek(timestamp):
	d= datetime.datetime.utcfromtimestamp(timestamp)
	hour = int(datetime.datetime.strftime(d, '%H'))
	minute = int(datetime.datetime.strftime(d, '%M'))
	second = int(datetime.datetime.strftime(d, '%S'))
	day = dayofweek(timestamp)
	f = (86400 * day) + (3600 * hour) + (60 * minute) + (second)
	return f

def minuteofday(timestamp):
	d= datetime.datetime.utcfromtimestamp(timestamp)
	hour = int(datetime.datetime.strftime(d, '%H'))
	minute = int(datetime.datetime.strftime(d, '%M'))
	f = (60 * hour) + minute
	return f

def hourofweek(timestamp):
	d= datetime.datetime.utcfromtimestamp(timestamp)
	hour = int(datetime.datetime.strftime(d, '%H'))
	day = dayofweek(timestamp)
	f = (24 * day) + hour
	return f

def pressaverages(x,y):
	print('x:',x)
	print('y:',y)
	class Value(object):
	    value = 0
	    nums = 0
	d={}
	for i in range(len(x)):
		if x[i] not in d:
			d[x[i]] = Value()
		else:
			d[x[i]].value += y[i]
			d[x[i]].nums +=1
	m = []
	n = []
	for i in d:
		try:
			#print(i, d[i].value / d[i].nums)
			m.append(i)
			n.append(d[i].value / d[i].nums)
		except:
			#print(i, 0)
	return m, n


def plot(xvalue, yvalue, xlabel="", ylabel="", title=""):
	g.xlabel(xlabel)
	g.ylabel(ylabel)
	g.title(title)
	g.plot(xvalue, yvalue)