#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sys
import string

''''USER CONFIGURATION'''
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."

'''All done!'''

try:
	import bot
	USERAGENT = bot.aG
except ImportError:
    pass

print('Logging in.')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)
def start():
	print('\nWho do you want to scrub?')
	USER = input('>/u/')
	print('\nYou are about to scrub /u/' + USER + "'s existence from /r/" + SUBREDDIT)
	print('Are you sure? Y/N')
	confirm = input('>')
	if confirm.lower() not in ['yes','y']:
		pass
	else:
		SCRUB(USER)
	
def work(posts):
	#By subreddit
	for post in posts:
		try:
			pauthor = post.author.name
			pid = post.id
			if pauthor.lower() == USER.lower() and post.banned_by == None:
				print(pid + ' - Removing', end='')
				sys.stdout.flush()
				post.remove()
				print('\r' + pid + ' - Done    ')
		except:
			pass

def worku(posts):
	#By user's profile page
	for post in posts:
		try:
			psub = post.subreddit.display_name
			pid = post.id
			if psub.lower() == SUBREDDIT.lower() and post.banned_by == None:
				print(pid + ' - Removing', end='')
				sys.stdout.flush()
				post.remove()
				print('\r' + pid + ' - Done    ')
		except:
			pass

def works(USER):
	#By subreddit search bar
	number = 1
	stage = 1
	print('Searching /r/' + SUBREDDIT + ' by author:"' + USER + '" || Stage ' + str(stage))
	while number > 0:
		stage+=1
		number = 0
		posts = r.search('author:"' + USER + '"', subreddit=SUBREDDIT,limit=1000)
		for post in posts:
			number +=1
			try:
				pauthor = post.author.name
				pid = post.id
				if pauthor.lower() == USER.lower() and post.banned_by == None:
					print(pid + ' - Removing', end='')
					sys.stdout.flush()
					post.remove()
					print('\r' + pid + ' - Done    ')
			except:
				pass
		print('Found ' + str(number) + ' items this run.')
		print('Waiting 15s to give the cache a moment to refresh...\n')
		time.sleep(15)

def SCRUB(USER):
	try:
		redditor = r.get_redditor(USER)
		print('\nBeginning scrub in 5 seconds...')
		time.sleep(5)
		print('Scrubbing /u/' + USER + ' from /r/' + SUBREDDIT + '\n')
		subreddit = r.get_subreddit(SUBREDDIT)
		print('Scanning /r/' + SUBREDDIT + '/New')
		posts = subreddit.get_new(limit=None)
		work(posts)
	
		print('Scanning /r/' + SUBREDDIT + '/top')
		posts = subreddit.get_top_from_all(limit=None)
		work(posts)
	
		print('Scanning /r/' + SUBREDDIT + '/comments')
		posts = subreddit.get_comments(limit=None)
		work(posts)
	
		redditor = r.get_redditor(USER,fetch=True)
		print('Scanning /u/' + USER + '/submitted')
		posts = redditor.get_submitted(limit=None)
		worku(posts)
	
		print('Scanning /u/' + USER + '/comments')
		posts = redditor.get_comments(limit=None)
		worku(posts)

		works(USER)
	
		print('\nFinished')
		input()
	except praw.requests.exceptions.HTTPError:
		print('That user does not exist')
		input()

while True:
	start()