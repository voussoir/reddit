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

def commentaugment(databasename, limit, threshold):
	sql = sqlite3.connect(databasename)
	cur = sql.cursor()
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
	cur.execute('SELECT * FROM posts WHERE url IS NOT NULL and num_comments > 0 ORDER BY num_comments DESC')
	while True:
		hundred = [cur.fetchone() for x in range(100)]
		hundred = remove_none(hundred)
		hundred = [h[1] for h in hundred]
		hundred = verify_t3(hundred)
		submissions = r.get_info(thing_id=hundred)
		print('Retrieved %d submissions' % len(submissions))

		for submission in submissions:
			print('Processing %s expecting %d | ' % (submission.fullname, submission.num_comments), end='')
			sys.stdout.flush()
			submission.replace_more_comments(limit, threshold)
			comments = praw.helpers.flatten_tree(submission.comments)
			print(len(comments))
			smartinsert(sql, cur, comments)

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

	commentaugment(databasename, limit, threshold)
	print('Done')
	input()
	quit()


if __name__ == '__main__':
	main()