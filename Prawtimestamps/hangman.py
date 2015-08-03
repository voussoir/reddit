# Consistency? Where?

import praw
import sqlite3
import datetime

import bot
r=praw.Reddit(bot.aG)

sql = sqlite3.connect('databases/@gallowboob.db')
cur = sql.cursor()
outfile = open('@hangman.md', 'w')

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

FOOTER = '''
submission | archive | note
---------- | ------- | -----
[`3e3d5a`](http://redd.it/3e3d5a) | https://archive.is/H1D2V | /r/woahdude 3d printing support
[`3e3e00`](http://redd.it/3e3e00) | https://archive.is/JcMRf | /r/pics statue
[`3e3isi`](http://redd.it/3e3isi) | https://archive.is/y6jJU | /r/me_ir jeans
[`3e3hdx`](http://redd.it/3e3hdx) | https://archive.is/9XI8J | /r/aww jeans
[`3e3hes`](http://redd.it/3e3hes) | https://archive.is/gwqhf | /r/unexpected jeans
[`3e3ebs`](http://redd.it/3e3ebs) | https://archive.is/FhkWD | /r/me_irl dogbird
[`3f27gh`](http://redd.it/3f27gh) | https://archive.is/CE653 | /r/pics axe spine handle
[`3f281g`](http://redd.it/3f281g) | https://archive.is/FbDZq | /r/pics axe spine handle again
[`3f2bk9`](http://redd.it/3f2bk9) | https://archive.is/c3cBW | /r/woahdude axe spine handle again again
[`3f2838`](http://redd.it/3f2838) | https://archive.is/lOhEe | /r/interestingasfuck axe spine handle again again again
[`3f2508`](http://redd.it/3f2508) | https://archive.is/5tXtG | /r/aww cat with a job
[`3f2axj`](http://redd.it/3f2axj) | https://archive.is/V1Mlx | /r/gifs drifting kid
[`3f29g7`](http://redd.it/3f29g7) | https://archive.is/2OBeP | /r/me_irl guy in water
[`3f25st`](http://redd.it/3f25st) | https://archive.is/vofui | /r/unexpected sexy video on the beach
[`3fjwoe`](http://redd.it/3fjwoe) | https://archive.is/WwRpr | /r/nonononoyes extreme biking
[`3fjws0`](http://redd.it/3fjws0) | https://archive.is/s1B1F | /r/pics RIP Hitchbot
[`3fjy38`](http://redd.it/3fjy38) | https://archive.is/5Rhzu | /r/peoplebeingjerks RIP Hitchbot again
'''

def out(*text):
	print(*text, file=outfile)

def frequencydict(datalist):
	datadict = {}
	print('freq')
	for item in datalist:
		datadict[item] = datadict.get(item, 0) + 1
	return datadict

def average(datalist):
	denominator = max(1, len(datalist))
	return sum(datalist) / denominator

def dictformat(datadict, joiner=', '):
	keys = list(datadict.keys())
	if isinstance(datadict[keys[0]], list):
		keys.sort(key=lambda x: (len(datadict.get(x)), datadict.get(x)[0]), reverse=True)
	else:
		keys.sort(key=datadict.get, reverse=True)
	longestkey = max([len(k) for k in keys])
	out = ''
	for key in keys:
		val = datadict[key]
		if isinstance(val, list):
			val = joiner.join([str(x) for x in val])
		out += '%s | %s\n' % (key, val)
	return out

def findduplicates(datalist, attribute):
	datadict = {}
	for item in datalist:
		attr = getattr(item, attribute)
		datadict[attr] = datadict.get(attr, []) + [item.id]
	datadict = {x:datadict[x] for x in datadict if len(datadict[x]) > 2}
	return datadict

def listblock(x, blocklength=12, joins=', '):
    out = ''
    x = ['[`{i}`](http://redd.it/{i})'.format(i=i) for i in x]
    l = len(x)
    ra = (l // blocklength)
    if l % blocklength is not 0:
        ra += 1
    for i in range(ra):
        a = i*blocklength
        b = a + blocklength
        out += joins.join(x[a:b])
        out += '  \n'
    return out


def main():
	out('/u/GallowBoob\n======\n\n')
	out('Obviously I can\'t tell if a deleted post was its if I find it too late,')
	out('so these numbers should be considered lower than is correct.  ')
	out('[click here](https://github.com/voussoir/reddit/raw/master/Prawtimestamps/%40gallowboob.db) to download the sqlite db.')
	out('')
	cur.execute('SELECT COUNT(idint) FROM posts')
	totalitems = cur.fetchone()[0]
	out('Submissions on record: %d  ' % totalitems)

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
	out('Submissions alive: %d  ' % len(living))
	out('Submissions deleted: %d  ' % len(nonliving))
	out('')
	cur.execute('SELECT COUNT(idint) FROM posts WHERE self == 1')
	selfposts = cur.fetchone()[0]
	out('Selfposts: %d  ' % selfposts)
	out('Linkposts: %d  ' % (totalitems-selfposts))
	out('')
	scores_total = [[item.score, item.id] for item in living+nonliving]
	scores_living = [[item.score, item.id] for item in living]
	scores_nonliving = [[item.score, item.id] for item in nonliving]
	scores_total.sort(key=lambda x: x[0], reverse=True)
	scores_living.sort(key=lambda x: x[0], reverse=True)
	scores_nonliving.sort(key=lambda x: x[0], reverse=True)
	print('Measuring scores')
	out('Average score: %d  ' % (average([x[0] for x in scores_total])))
	out('Average score of living: %d  ' % (average([x[0] for x in scores_living])))
	out('Average score of deleted: %d  ' % (average([x[0] for x in scores_nonliving])))
	out('')
	if scores_total:
		out('Highest score: [%d](http://redd.it/%s)  ' % (scores_total[0][0], scores_total[0][1]))
	if scores_living:
		out('Highest score of living: [%d](http://redd.it/%s)  ' % (scores_living[0][0], scores_living[0][1]))
		out('Lowest score of living: [%d](http://redd.it/%s)  ' % (scores_living[-1][0], scores_living[-1][1]))
	if scores_nonliving:
		out('Highest score of deleted: [%d](http://redd.it/%s)  ' % (scores_nonliving[0][0], scores_nonliving[0][1]))
	out('')
	freq_total = findduplicates(living+nonliving, 'url')
	freq_living = findduplicates(living, 'url')
	freq_nonliving = findduplicates(nonliving, 'url')
	duplicates_total = sum([len(freq_total[x]) for x in freq_total])
	duplicates_living = sum([len(freq_living[x]) for x in freq_living])
	duplicates_nonliving = sum([len(freq_nonliving[x]) for x in freq_nonliving])
	print('Measuring reposts')
	out('&nbsp;\n\n#reposts\n')
	out('Submissions with the same link as another: %d  ' % duplicates_total)
	out('Submissions living with the same link as another living: %d  ' % duplicates_living)
	out('Submissions deleted with the same link as another deleted: %d  ' % duplicates_nonliving)
	out('Submissions deleted with the same link as another living: %d  ' % (duplicates_total - (duplicates_living+duplicates_nonliving)))
	out('')
	for key in freq_total:
		val = freq_total[key]
		freq_total[key] = ['[`{i}`](http://redd.it/{i})'.format(i=i) for i in val]
	out('url | karma farmas')
	out('----- | -----')
	out(dictformat(freq_total))
	out('')
	print('Measuring subreddits')
	freq_total = frequencydict([x.subreddit.display_name for x in living+nonliving])
	freq_living = frequencydict([x.subreddit.display_name for x in living])
	freq_nonliving = frequencydict([x.subreddit.display_name for x in nonliving])
	out('&nbsp;\n\n#subreddits\n')
	out('Subreddits posted to: %d  ' % len(freq_total))
	out('Subreddits posted to, living: %d  ' % len(freq_living))
	out('Subreddits posted to, deleted: %d  ' % len(freq_nonliving))
	out('')
	for subreddit in freq_total:
		karma = 0
		deletions = 0
		for post in living+nonliving:
			if post.subreddit.display_name == subreddit:
				karma += post.score
				if post.author is None:
					deletions += 1
		freq_total[subreddit] = [freq_total[subreddit], deletions, karma]
	out('subreddit | posts made | posts deleted | score total')
	out(':-------- | ---------: | ------------: | ----------:')
	out(dictformat(freq_total, joiner=' | '))
	out('')
	out('&nbsp;\n\n#living\n')
	out(listblock([x.id for x in living]))
	out('')
	out('&nbsp;\n\n#deleted\n')
	out(listblock([x.id for x in nonliving]))
	out('')
	out('&nbsp;\n\n#archives\n')
	out(FOOTER)

main()
outfile.close()