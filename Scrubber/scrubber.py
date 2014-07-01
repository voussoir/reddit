#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sys
import string

''''USER CONFIGURATION'''
USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."

'''All done!'''

try:
	import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
	USERNAME = bot.getuG()
	PASSWORD = bot.getpG()
	USERAGENT = bot.getaG()
except ImportError:
    pass

print('Logging in as ' + USERNAME)
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)
print('\nWho do you want to scrub?')
USER = input('>/u/')
print('\nYou are about to scrub /u/' + USER + "'s existence from /r/" + SUBREDDIT)
print('Are you sure? Y/N')
confirm = input('>')
if confirm.lower() not in ['yes','y']:
	quit()
	
def work(posts):
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

def SCRUB(USER):
	try:
		redditor = r.get_redditor(USER)
	except:
		print('That user does not exist')
		print('Press enter to close')
		input()
		quit()
	print('\nBeginning scrub in 5 seconds...')
	time.sleep(5)
	print('Scrubbing /u/' + USER + ' from /r/' + SUBREDDIT + '\n')
	subreddit = r.get_subreddit(SUBREDDIT)
	print('Scanning /r/' + SUBREDDIT + '/New')
	posts = subreddit.get_new(limit=None)
	work(posts)

	print('Scanning /r/' + SUBREDDIT + '/top')
	posts = subreddit.get_top(limit=None)
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

	print('\nFinished')
	input()

SCRUB(USER)