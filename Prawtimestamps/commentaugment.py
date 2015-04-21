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

def commentaugment(databasename, limit, threshold, numthresh, verbose):
	sql = sqlite3.connect(databasename)
	cur = sql.cursor()
	cur2 = sql.cursor()
	#  0 - idint
	#  1 - idstr
	#  2 - created
	#  3 - self
	#  4 - nsfw
	#  5 - author
	#  6 - title
	#  7 - url
	#  8 - selftext
	#  9 - score
	# 10 - subreddit
	# 11 - distinguished
	# 12 - textlen
	# 13 - num_comments
	# 14 - flair_text
	# 15 - flair_css_class
	cur.execute('SELECT COUNT(idint) FROM posts WHERE url IS NOT NULL and num_comments > ?', [numthresh])
	totalthreads = cur.fetchone()[0]

	cur.execute('SELECT * FROM posts WHERE url IS NOT NULL and num_comments > ? ORDER BY num_comments DESC', [numthresh])
	scannedthreads = 0
	while True:
		hundred = [cur.fetchone() for x in range(100)]
		hundred = remove_none(hundred)
		if len(hundred) == 0:
			return
		hundred = [h[1] for h in hundred]
		hundred = verify_t3(hundred)
		submissions = nofailrequest(r.get_info)(thing_id=hundred)
		print('Retrieved %d submissions' % len(submissions))

		for submission in submissions:
			print('Processing %s expecting %d | ' % (submission.fullname, submission.num_comments), end='')
			sys.stdout.flush()
			if verbose:
				print()
			comments = get_comments_for_thread(submission, limit, threshold, verbose)
			smartinsert(sql, cur2, comments)
			scannedthreads += 1
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
				s = 'Got %d more, %d so far.' % (additionals, len(comments))
				if limit is not None:
					s += ' Can perform %d more replacements' % limit
				print(s)
	except KeyboardInterrupt:
		pass
	except:
		traceback.print_exc()

	return comments

def remove_none(itemlist):
	done = False
	while not done:
		done = True
		for index in range(len(itemlist)):
			if itemlist[index] is None:
				done = False
				del itemlist[index]
				break
	return itemlist

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

def smartinsert(sql, cur, results):
	for o in results:
		cur.execute('SELECT * FROM posts WHERE idint=?', [b36(o.id)])
		if not cur.fetchone():
			try:
				o.authorx = o.author.name
			except AttributeError:
				o.authorx = '[DELETED]'

			postdata = [b36(o.id), o.fullname, o.created_utc, None, None,
			o.authorx, o.parent_id, None, o.body, o.score,
			o.subreddit.display_name, o.distinguished, len(o.body),
			None, None, None]
			cur.execute('INSERT INTO posts VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', postdata)
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
	if threshold == '':
		threshold = 0
	else:
		threshold = int(threshold)
		if threshold < 0:
			threshold = 0

	print('\nMinimum num_comments a thread must have to be scanned')
	numthresh = input(']: ')
	if numthresh == '':
		numthresh = 0
	else:
		numthresh = int(numthresh)
		if numthresh < 0:
			numthresh = 0

	print('\nVerbosity. 0 = quieter, 1 = louder')
	verbose = input(']: ')
	if verbose == '':
		verbose = False
	else:
		verbose = int(verbose)
		verbose = (verbose is 1)

	commentaugment(databasename, limit, threshold, numthresh, verbose)
	print('Done')
	input()
	quit()


if __name__ == '__main__':
	main()