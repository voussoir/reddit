import praw
import traceback
import time

''' CONFIG '''

USERAGENT = ''
MAXPOSTS = 100

''' END CONFIG '''

try:
	import bot
	USERAGENT = bot.uG
except ImportError:
	pass

r = praw.Reddit(USERAGENT)

def nfr(function, dropout=None):
	'''
	"No Fail Request"
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
				except praw.requests.exceptions.HTTPError as e:
					if dropout is None:
						raise e
					if e.response.status_code == dropout:
						return None
					if e.response.status_code in dropout:
						return None
					else:
						raise e
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

def process_subreddit(sr):
	subreddit = nfr(r.get_subreddit)(sr)
	print('/r/%s/new' % sr)
	posts = list(nfr(subreddit.get_new)(limit=MAXPOSTS))
	print('/r/%s/comments' % sr)
	posts += list(nfr(subreddit.get_comments)(limit=MAXPOSTS))

	authors = [post.author.name for post in posts if post.author is not None]
	authors = set(authors)
	count = len(authors)
	print('Found %d authors' % count)

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

	del totalreddits[sr]
	# -1 because of %totalposts%
	totalreddits['%totalsubs%'] = (len(totalreddits) - 1)
	return totalreddits

def process_user(username, pre=''):
	user = nfr(r.get_redditor, dropout=404)(username)
	if user is None:
		return {}
	print('\t%s/u/%s/submitted' % (pre, username))
	userposts = list(nfr(user.get_submitted)(limit=MAXPOSTS))
	print('\t%s/u/%s/comments' % (pre, username))
	userposts += list(nfr(user.get_comments)(limit=MAXPOSTS))

	userreddits = {'%totalposts%':len(userposts)}
	#print(userreddits)
	for post in userposts:
		subreddit = post.subreddit.display_name
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
	process_and_write('redditdev')
	quit()