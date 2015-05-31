#/u/GoldenSights
import traceback
import praw
import time
import datetime
import sqlite3
import sys

USERAGENT = ''
# Enter a useragent

try:
	import bot
	USERAGENT = bot.aPT
except ImportError:
	pass

print('Connecting to reddit')
r = praw.Reddit(USERAGENT)

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

def commentaugment(databasename, limit, threshold, numthresh, skips, verbose):
	sql = sqlite3.connect(databasename)
	cur = sql.cursor()
	cur2 = sql.cursor()
	cur.execute('SELECT COUNT(idint) FROM posts WHERE url IS NOT NULL and num_comments > ?', [numthresh])
	totalthreads = cur.fetchone()[0]

	cur.execute('SELECT idstr FROM posts WHERE url IS NOT NULL and num_comments > ? ORDER BY num_comments DESC', [numthresh])
	fetchall = cur.fetchall()
	fetchall = [f[0] for f in fetchall]

	scannedthreads = skips
	for x in fetchall[:skips]:
		print('Skipping %s, %d / %d' % (trash[SQL_IDSTR], x+1, totalthreads))
	fetchall = fetchall[skips:]

	while True:
		hundred = fetchall[:100]
		fetchall = fetchall[100:]
		hundred = list(filter(None, hundred))
		if len(hundred) == 0:
			return
		hundred = verify_t3(hundred)
		submissions = nofailrequest(r.get_info)(thing_id=hundred)
		print('Retrieved %d submissions' % len(submissions))

		for submission in submissions:
			if verbose:
				spacer = '\n\t'
			else:
				spacer = ' '
			print('Processing %s%sexpecting %d | ' % (submission.fullname, spacer, submission.num_comments), end='')
			sys.stdout.flush()
			if verbose:
				print()
			comments = get_comments_for_thread(submission, limit, threshold, verbose)
			smartinsert(sql, cur2, comments)
			scannedthreads += 1
			if verbose:
				print('\t', end='')
			print('Found %d | %d / %d threads complete' % (len(comments), scannedthreads, totalthreads))

def get_comments_for_thread(submission, limit, threshold, verbose):
	comments = nofailrequest(lambda x: x.comments)(submission)
	comments = praw.helpers.flatten_tree(comments)
	comments = manually_replace_comments(comments, limit, threshold, verbose)
	return comments

def nofailrequest(function):
	'''
	Creates a function that will retry until it succeeds.
	This function accepts 1 parameter, a function, and returns a modified
	version of that function that will try-catch, sleep, and loop until it
	finally returns.
	'''
	def a(*args, **kwargs):
		while True:
			try:
				try:
					result = function(*args, **kwargs)
					return result
				except AssertionError:
					# Strange PRAW bug causes certain MoreComments
					# To throw assertion error, so just ignore it
					# And get onto the next one.
					return []
			except:
				traceback.print_exc()
				print('Retrying in 2...')
				time.sleep(2)
	return a

def manually_replace_comments(incomments, limit=None, threshold=0, verbose=False):
	'''
	PRAW's replace_more_comments method cannot continue
	where it left off in the case of an Ow! screen.
	So I'm writing my own function to get each MoreComments item individually

	Furthermore, this function will maximize the number of retrieved comments by
	sorting the MoreComments objects and getting the big chunks before worrying
	about the tail ends.
	'''

	comments = []
	morecomments = []
	while len(incomments) > 0:
		item = incomments[0]
		if isinstance(item, praw.objects.MoreComments) and item.count >= threshold:
			morecomments.append(item)
		elif isinstance(item, praw.objects.Comment):
			comments.append(item)
		incomments = incomments[1:]

	try:
		while True:
			if limit is not None and limit <= 0:
				break
			if len(morecomments) == 0:
				break
			morecomments.sort(key=lambda x: x.count, reverse=True)
			mc = morecomments[0]
			morecomments = morecomments[1:]
			additional = nofailrequest(mc.comments)()
			additionals = 0
			if limit is not None:
				limit -= 1
			for item in additional:
				if isinstance(item, praw.objects.MoreComments) and item.count >= threshold:
					morecomments.append(item)
				elif isinstance(item, praw.objects.Comment):
					comments.append(item)
					additionals += 1
			if verbose:
				s = '\tGot %d more, %d so far.' % (additionals, len(comments))
				if limit is not None:
					s += ' Can perform %d more replacements' % limit
				print(s)
	except KeyboardInterrupt:
		pass
	except:
		traceback.print_exc()

	return comments

def verify_t3(itemlist):
	done = False
	while not done:
		done = True
		for index in range(len(itemlist)):
			item = itemlist[index]
			if 't1_' in item or item is None:
				done = False
				del itemlist[index]
				break
			if 't3_' not in item:
				itemlist[index] = 't3_' + item
	return itemlist

def smartinsert(sql, cur, results, nosave=False):
	for o in results:
		cur.execute('SELECT * FROM posts WHERE idint=?', [b36(o.id)])
		if not cur.fetchone():
			try:
				o.authorx = o.author.name
			except AttributeError:
				o.authorx = '[DELETED]'

			postdata = [None] * SQL_COLUMNCOUNT
			postdata[SQL_IDINT] = b36(o.id)
			postdata[SQL_IDSTR] = o.fullname
			postdata[SQL_CREATED] = o.created_utc
			postdata[SQL_SELF] = None
			postdata[SQL_NSFW] = None
			postdata[SQL_AUTHOR] = o.authorx
			postdata[SQL_TITLE] = o.parent_id
			postdata[SQL_URL] = None
			postdata[SQL_SELFTEXT] = o.body
			postdata[SQL_SCORE] = o.score
			postdata[SQL_SUBREDDIT] = o.subreddit.display_name
			postdata[SQL_DISTINGUISHED] = o.distinguished
			postdata[SQL_TEXTLEN] = len(o.body)
			postdata[SQL_NUM_COMMENTS] = None
			postdata[SQL_FLAIR_TEXT] = None
			postdata[SQL_FLAIR_CSS_CLASS] = None

			cur.execute('INSERT INTO posts VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', postdata)
			if nosave is False:
				sql.commit()

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

def fixint(i):
	if i == '':
		return 0
	i = int(i)
	if i < 0:
		return 0
	return i

def main():
	print('\nDatabase file')
	databasename = input(']: ')
	if databasename[-3:] != '.db':
		databasename += '.db'
	print('\nLimit - number of MoreComments objects to replace')
	print('Enter 0 to have no limit and get all')
	limit = input(']: ')
	if limit == '':
		limit = None
	else:
		limit = int(limit)
		if limit < 1:
			limit = None

	print('\nThreshold - minimum number of children comments a MoreComments')
	print('object must have to warrant a replacement')
	threshold = input(']: ')
	threshold = fixint(threshold)

	print('\nMinimum num_comments a thread must have to be scanned')
	numthresh = input(']: ')
	numthresh = fixint(numthresh)

	print('\nSkips - Skip ahead by this many threads, to pick up where you left off.')
	skips = input(']: ')
	skips = fixint(skips)

	print('\nVerbosity. 0 = quieter, 1 = louder')
	verbose = input(']: ')
	verbose = fixint(verbose)
	verbose = (verbose is 1)

	commentaugment(databasename, limit, threshold, numthresh, skips, verbose)
	print('Done')
	input()
	quit()


if __name__ == '__main__':
	main()