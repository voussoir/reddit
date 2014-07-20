#By /u/GoldenSights
import praw
import configparser
import sqlite3

config = configparser.ConfigParser()
config.read('config.ini')
print('Loaded Config file.')

USERNAME = config['24']['USERNAME']
PASSWORD = config['24']['PASSWORD']
USERAGENT = config['24']['USERAGENT']

sql = sqlite3.connect('sql.db')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS requests(ID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS activedebates(ID TEXT, time TEXT, questions TEXT)')
print('Loaded SQL Database')



try:
	import bot
	USERNAME = bot.getuG()
	PASSWORD = bot.getpG()
	USERAGENT = bot.getaG()
except:
	pass

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)

def loadconfig():
	global QUESTIONDELAY
	global SUBREDDIT
	global WAIT
	global MAXPOSTS
	global REQUESTTAG

	config.read('config.ini')
	QUESTIONDELAY = int(config['24']['QUESTIONDELAY'])
	#The Default number of seconds between questions being posted. 
	SUBREDDIT = config['24']['SUBREDDIT']
	#The main subreddit
	WAIT = int(config['24']['WAIT'])
	#The amount of time between cycles. Inactive during this time.
	MAXPOSTS = int(config['24']['MAXPOSTS'])
	#Number of posts to gather at a time. Praw can download 100 in a single request
	REQUESTTAG = config['24']['REQUESTTAG']
	#The tag in the title which identifies the post as a request

def reqflair(post):
	print('\tChecking request flair')
	try:
		pflair = post.link_flair_text
	except:
		pflair = ''
	print('\t-' + pflair)

def scan():
	print('Scanning ' + SUBREDDIT)
	subreddit = r.get_subreddit(SUBREDDIT)
	posts = subreddit.get_new(MAXPOSTS)
	for post in posts:
		pid = post.id
		cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
		if not cur.fetchone():
			print(pid)
			if REQUESTTAG.lower() in post.title.lower():
				reqflair(post)



loadconfig()