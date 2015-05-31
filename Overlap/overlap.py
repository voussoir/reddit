import praw
import traceback
import time
import types
import os

''' CONFIG '''

USERAGENT = ''
MAXPOSTS = 100

DROPOUT = [404]
# This error code will cause the nofailrequest to exit.
# There's no reason to repeatedly request a 404.

''' END CONFIG '''

try:
	import bot
	USERAGENT = bot.uG
except ImportError:
	pass

r = praw.Reddit(USERAGENT)

def nfr2(function, *fargs, **fkwargs):
	'''
	Different version of NFR. 
	The first was having problems with generators and lazyload
	objects, because those functions return successfully
	even though the data isn't checked
	'''
	while True:
		try:
			results = function(*fargs, **fkwargs)
			if isinstance(results, types.GeneratorType):
				results = list(results)
			return results
		except praw.requests.exceptions.HTTPError as e:
			if e.response.status_code == DROPOUT:
				return None
			if isinstance(DROPOUT, list) and e.response.status_code in DROPOUT:
				return None
			traceback.print_exc()
			print('Retrying in 2...')
			time.sleep(2)
		except KeyboardInterrupt:
			return None
		except:
			traceback.print_exc()
			print('Retrying in 2...')
			time.sleep(2)

def nfr(function, dropout=None):
	'''
	"No Fail Request"
	Creates a function that will retry until it succeeds.
	This function accepts 1 parameter, a function, and returns a modified
	version of that function that will try-catch, sleep, and loop until it
	finally returns.
	'''
	def b():
		traceback.print_exc()
		print('Retrying in 2...')
		time.sleep(2)
	def a(*args, **kwargs):
		while True:
			try:
				result = function(*args, **kwargs)
				return result
			except praw.requests.exceptions.HTTPError as e:
				if e.response.status_code == dropout:
					return None
				if isinstance(dropout, list) and e.response.status_code in dropout:
					return None
				else:
					b()
			except requests.exceptions.ConnectionError:
				b()
			except AssertionError:
				# Strange PRAW bug causes certain MoreComments
				# To throw assertion error, so just ignore it
				# And get onto the next one.
				return []
			except KeyboardInterrupt:
				raise Exception("KeyboardInterrupt")
			except:
				b()
	return a

def get_subreddit_authors(sr):
	'''
	Given a subreddit name, go to /r/subreddit/new
	and /r/subreddit/comments, and return the names of post
	authors.
	'''
	sr = sr.lower()
	subreddit = nfr(r.get_subreddit)(sr)
	print('/r/%s/new' % sr)
	#posts = list(nfr(subreddit.get_new)(limit=MAXPOSTS))
	posts = nfr2(subreddit.get_new, limit=MAXPOSTS)
	print('/r/%s/comments' % sr)
	#posts += list(nfr(subreddit.get_comments)(limit=MAXPOSTS))
	posts += nfr2(subreddit.get_comments, limit=MAXPOSTS)

	authors = [post.author.name for post in posts if post.author is not None]
	authors = list(set(authors))
	authors.sort(key=lambda x: x.lower())
	print('Found %d authors' % len(authors))
	return authors

def process_userlist(authors, fromsubreddit=''):
	'''
	Given a list of usernames, put each into process_user()
	and collect a total dictionary of subreddits

	If this list of names comes from scanning a subreddit, you
	can provide `fromsubreddit`, which will be removed from the dict
	at the end, since it's useless data if everyone has it in common.
	'''
	authors = list(set(authors))
	fromsubreddit = fromsubreddit.lower()
	count = len(authors)
	i = 1
	userreddits = {}
	totalreddits = {}
	for username in authors:
		pre = '(%0{l}d/%0{l}d) '.format(l=len(str(count))) % (i, count)
		thisuser = process_user(username, pre=pre)
		userreddits[username] = thisuser
		for sub in thisuser:
			totalreddits[sub] = totalreddits.get(sub, 0) + thisuser[sub]
		#print(totalreddits)
		i += 1

	if fromsubreddit in totalreddits:
		del totalreddits[fromsubreddit]
	# -1 because of %totalposts%
	totalreddits['%totalsubs%'] = (len(totalreddits) - 1)
	return totalreddits

def process_subreddit(sr):
	'''
	Given a subreddit name, collect authors from submissions
	and comments, then pass them into process_userlist
	'''
	authors = get_subreddit_authors(sr)
	results = process_userlist(authors, fromsubreddit=sr)
	return results

def process_user(username, pre=''):
	'''
	Given a username, go to /u/username/submitted
	and /u/username/comments, and return the names
	of subreddits he has posted to, with their frequencies
	'''
	user = nfr(r.get_redditor, dropout=404)(username)
	if user is None:
		return {}
	print('\t%s/u/%s/submitted' % (pre, username))
	#userposts = list(nfr(user.get_submitted)(limit=MAXPOSTS))
	userposts = nfr2(user.get_submitted, limit=MAXPOSTS)
	print('\t%s/u/%s/comments' % (pre, username))
	#userposts += list(nfr(user.get_comments)(limit=MAXPOSTS))
	userposts += nfr2(user.get_comments, limit=MAXPOSTS)

	userreddits = {'%totalposts%':len(userposts)}
	for post in userposts:
		subreddit = post.subreddit.display_name.lower()
		userreddits[subreddit] = userreddits.get(subreddit, 0) + 1

	return userreddits

def write_json(filename, totalreddits):
	'''
	Given a dictionary totalreddits, sort by freq
	and write it to filename.json
	'''
	if filename[-5:] != '.json':
		filename += '.json'
	keys = list(totalreddits.keys())
	keys.sort(key=lambda x: (totalreddits.get(x), x.lower()), reverse=True)

	print('Creating %s' % filename)
	outfile = open(filename, 'w')
	outfile.write('{\n')
	for key in keys:
		val = totalreddits[key]
		outfile.write('\t"%s" : %d,\n' % (key, val))
	outfile.write('}')
	outfile.close()

def process_and_write(sr):
	'''
	shortcut to process_subreddit and write_json
	'''
	totalreddits = process_subreddit(sr)
	write_json(sr, totalreddits)

def file_lines(filename):
	textfile = open(filename, 'r')
	textlines = [line.strip() for line in textfile.readlines()]
	textfile.close()
	return textlines

def process_subfile(filename):
	'''
	Shortcut to open a txt file containing subreddit names
	automatically put each one into process_and_write
	'''
	sublines = file_lines(filename)

	for subname in sublines:
		process_and_write(subname)

def process_userfile(filename, jsonfilename):
	'''
	Shortcut to open a txt file containing user names
	automatically put each one into process_userlist

	jsonfilename is required since we don't have any subreddit
	to go off of.
	'''
	userlines = file_lines(filename)

	for username in userlines:
		results = process_userlist(username)
		write_json(jsonfilename, results)

if __name__ == '__main__':
	process_and_write('goldtesting')
	os._exit(0)