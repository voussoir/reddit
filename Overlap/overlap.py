import praw
import traceback
import time
import types

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
			raise Exception("CTRL+C")
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

def process_userlist(authors):
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

	if sr in totalreddits:
		del totalreddits[sr]
	# -1 because of %totalposts%
	totalreddits['%totalsubs%'] = (len(totalreddits) - 1)
	return totalreddits

def process_subreddit(sr):
	authors = get_subreddit_authors(sr)
	results = process_userlist(authors)
	return results

def process_user(username, pre=''):
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
	if filename[-5:] != '.json':
		filename += '.json'
	keys = list(totalreddits.keys())
	keys.sort(key=totalreddits.get, reverse=True)

	print('Creating %s' % filename)
	outfile = open(filename, 'w')
	outfile.write('{\n')
	for key in keys:
		val = totalreddits[key]
		outfile.write('\t"%s" : %d,\n' % (key, val))
	outfile.write('}')

def process_and_write(sr):
	totalreddits = process_subreddit(sr)
	write_json(sr, totalreddits)

if __name__ == '__main__':
	process_and_write('goldtesting')