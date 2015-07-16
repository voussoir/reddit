import praw
import sqlite3
import datetime
import time


USERAGENT = ""

r = praw.Reddit(USERAGENT)

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS submissiondata(id TEXT, created INT, title TEXT, score INT, subreddit TEXT, author TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS commentdata(id TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')
print('Loaded Completed table')

print()


MAXPOSTS = 1000
MINAGE = 86400
DUPECANCEL = 150
SLOWDOWN = 15


SUBREDDITMODE = 1
#0 = Use String, effectively a single sub
#1 = Use list, each sub independent
SUBREDDITS = 'pics'
SUBREDDITL = ['news', 'askreddit', 'pics', 'gifs', \
'videos', 'funny', 'mildlyinteresting', 'movies', 'aww', \
'worldnews', 'todayIlearned', 'gaming', 'all'\
'minecraft', 'reactiongifs', 'circlejerk', 'notinteresting', \
'lifeprotips']

BROWSEBY = ['hot', 'top day', 'top week']
#hot
#new
#top all
#top day
#top week
#top month



def getTime(bool):
	timeNow = datetime.datetime.now(datetime.timezone.utc)
	timeUnix = timeNow.timestamp()
	if bool == False:
		return timeNow
	else:
		return timeUnix

def buildlist(generator):
	dupes = 0
	result = []
	for item in generator:
		if dupes < DUPECANCEL:
			cur.execute('SELECT * FROM oldposts WHERE id=?', [item.id])
			if cur.fetchone():
				dupes +=1
			else:
				result.append(item)
		else:
			print()
			print('Canceling. Too many dupes', end='')
			break
		print('\rFound ' + "%04d" % (len(result)) + ' and ' + "%04d" % (dupes) + ' dupes', end='')
	print()

	print('Returned ' + str(len(result)) + ' items. Omitted ' + str(dupes) + ' dupes.')
	return result



def gatherposts():
	for browseby in BROWSEBY:
		print('Browseby ' + browseby)

		if SUBREDDITMODE == 0:
			subreddit = [SUBREDDITS]
		else:
			subreddit = SUBREDDITL[:]

		for sub in subreddit:
			print('Subreddit: ' + sub)
			s = r.get_subreddit(sub)
			print('Gathering ' + str(MAXPOSTS) + ' items. Est ' + "%0.0f" % (MAXPOSTS * 2 / 100) + ' seconds.')
			if browseby == 'new':
				n = buildlist(s.get_new(limit=MAXPOSTS))
			elif browseby == 'hot':
				n = buildlist(s.get_hot(limit=MAXPOSTS))
			elif browseby[:3] == 'top':
				if browseby[4:] == 'all':
					n = buildlist(s.get_top_from_all(limit=MAXPOSTS))
				if browseby[4:] == 'day':
					n = buildlist(s.get_top_from_day(limit=MAXPOSTS))
				if browseby[4:] == 'week':
					n = buildlist(s.get_top_from_week(limit=MAXPOSTS))
				if browseby[4:] == 'month':
					n = buildlist(s.get_top_from_month(limit=MAXPOSTS))
			else:
				raise Exception("You have entered an improper browseby setting.")
			now = getTime(True)
			successes = 0
			fails = 0
			for post in n:
				if now - post.created_utc > MINAGE:
					try:
						pauthor = post.author.name
					except:
						pauthor = '[[DELETED]]'
					print('New: ' + post.id + '\t' + pauthor + ('.' * (22-len(pauthor))) + str(post.score))
					cur.execute('INSERT INTO oldposts VALUES(?)', [post.id])
					cur.execute('INSERT INTO submissiondata VALUES(?,?,?,?,?, ?)', [post.id, post.created_utc, post.title, post.score, post.subreddit.display_name, pauthor])
					successes += 1
				else:
					fails += 1
			print('[   ] Added ' + str(successes) + '.\tFailed ' + str(fails) + '\n')
			sql.commit()
			if not subreddit.index(sub) == (len(subreddit) - 1):
				print('Sleeping ' + str(SLOWDOWN) + '\n')
				time.sleep(SLOWDOWN)

gatherposts()
quit()