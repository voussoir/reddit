import praw
import sqlite3
import datetime

import bot
r=praw.Reddit(bot.aG)

sql = sqlite3.connect('@gallowboob.db')
cur = sql.cursor()
outfile = open('@hangman.txt', 'w')

SQL_COLUMNCOUNT = 16
SQL_IDINT = 0
SQL_IDSTR = 1
SQL_CREATED = 2
SQL_SELF = 3
SQL_NSFW = 4
SQL_AUTHOR = 5
SQL_TITLE = 6
SQL_URL = 7
SQL_SELFTEXT = 8
SQL_SCORE = 9
SQL_SUBREDDIT = 10
SQL_DISTINGUISHED = 11
SQL_TEXTLEN = 12
SQL_NUM_COMMENTS = 13
SQL_FLAIR_TEXT = 14
SQL_FLAIR_CSS_CLASS = 15

def out(*text):
	print(*text, file=outfile)

def frequencydict(datalist):
	dataset = set(datalist)
	datadict = {}
	for item in dataset:
		datadict[item] = datalist.count(item)
	return datadict

def average(datalist):
	denominator = max(1, len(datalist))
	return sum(datalist) / denominator

def dictformat(datadict):
	keys = list(datadict.keys())
	if isinstance(datadict[keys[0]], list):
		keys.sort(key=lambda x: (len(datadict.get(x)), datadict.get(x)[0]), reverse=True)
	else:
		keys.sort(key=datadict.get, reverse=True)
	longestkey = max([len(k) for k in keys])
	out = ''
	for key in keys:
		val = datadict[key]
		key = (' ' * (longestkey - len(key))) + key
		out += '\t%s : %s\n' % (key, val)
	return out

def findduplicates(datalist, attribute):
	datadict = {}
	for item in datalist:
		attr = getattr(item, attribute)
		datadict[attr] = datadict.get(attr, []) + [item.id]
	datadict = {x:datadict[x] for x in datadict if len(datadict[x]) > 2}
	return datadict

def listblock(x, blocklength=10, joins=', '):
    out = ''
    x = [str(i) for i in x]
    l = len(x)
    ra = (l // blocklength)
    if l % blocklength is not 0:
        ra += 1
    for i in range(ra):
        a = i*blocklength
        b = a + blocklength
        out += joins.join(x[a:b])
        out += '\n'
    return out


def main():
	out('/u/GallowBoob\n')
	out('Deletions can only be detected if the post is found while new')
	out('These numbers should be considered lower than is correct.\n')
	cur.execute('SELECT COUNT(idint) FROM posts')
	totalitems = cur.fetchone()[0]
	out('Submissions on record: %d' % totalitems)

	cur.execute('SELECT idstr FROM posts')
	refreshids = [x[0] for x in cur.fetchall()]
	living = []
	nonliving = []
	while len(refreshids) > 0:
		print('Updating. %d remaining' % len(refreshids))
		items = r.get_info(thing_id=refreshids[:100])
		refreshids = refreshids[100:]
		for item in items:
			if item.author is None:
				nonliving.append(item)
			else:
				living.append(item)
	out('Submissions alive: %d' % len(living))
	out('Submissions deleted: %d' % len(nonliving))
	out('')
	cur.execute('SELECT COUNT(idint) FROM posts WHERE self == 1')
	selfposts = cur.fetchone()[0]
	out('Selfposts: %d' % selfposts)
	out('Linkposts: %d' % (totalitems-selfposts))
	out('')
	scores_total = [[item.score, item.id] for item in living+nonliving]
	scores_living = [[item.score, item.id] for item in living]
	scores_nonliving = [[item.score, item.id] for item in nonliving]
	scores_total.sort(key=lambda x: x[0], reverse=True)
	scores_living.sort(key=lambda x: x[0], reverse=True)
	scores_nonliving.sort(key=lambda x: x[0], reverse=True)
	out('Average score: %d' % (average([x[0] for x in scores_total])))
	out('Average score of living: %d' % (average([x[0] for x in scores_living])))
	out('Average score of deleted: %d' % (average([x[0] for x in scores_nonliving])))
	out('')
	out('Highest score: %s' % scores_total[0])
	out('Highest score of living: %s' % scores_living[0])
	out('Lowest score of living: %s' % scores_living[-1])
	out('Highest score of deleted: %s' % scores_nonliving[0])
	out('')
	freq_total = findduplicates(living+nonliving, 'url')
	freq_living = findduplicates(living, 'url')
	freq_nonliving = findduplicates(nonliving, 'url')
	duplicates_total = sum([len(freq_total[x]) for x in freq_total])
	duplicates_living = sum([len(freq_living[x]) for x in freq_living])
	duplicates_nonliving = sum([len(freq_nonliving[x]) for x in freq_nonliving])
	out('Submissions with the same link as another: %d' % duplicates_total)
	out('Submissions living with the same link as another living: %d' % duplicates_living)
	out('Submissions deleted with the same link as another deleted: %d' % duplicates_nonliving)
	out('Submissions deleted with the same link as another living: %d' % (duplicates_total - (duplicates_living+duplicates_nonliving)))
	out(dictformat(freq_total))
	out('')
	freq_total = frequencydict([x.subreddit.display_name for x in living+nonliving])
	freq_living = frequencydict([x.subreddit.display_name for x in living])
	freq_nonliving = frequencydict([x.subreddit.display_name for x in nonliving])
	out('Subreddits posted to: %d' % len(freq_total))
	out('Subreddits posted to, living: %d' % len(freq_living))
	out('Subreddits posted to, deleted: %d' % len(freq_nonliving))
	for subreddit in freq_total:
		karma = 0
		deletions = 0
		for post in living+nonliving:
			if post.subreddit.display_name == subreddit:
				karma += post.score
				if post.author is None:
					deletions += 1
		freq_total[subreddit] = [freq_total[subreddit], deletions, karma]
	out('\t            subreddit : [posts made, posts deleted, score total]')
	out(dictformat(freq_total))
	out('')
	out('Living posts')
	out(listblock([x.id for x in living]))
	out('')
	out('Deleted posts')
	out(listblock([x.id for x in nonliving]))

main()
outfile.close()