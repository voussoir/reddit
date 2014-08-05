#By /u/GoldenSights
#Python 3.4.1
import praw
import configparser
import sqlite3

config = configparser.ConfigParser()
config.read('config.ini')
#If you want to hide your credentials, you could put the file elsewhere and call it in.
print('Loaded Config file.')

USERNAME = config['24']['USERNAME']
PASSWORD = config['24']['PASSWORD']
USERAGENT = config['24']['USERAGENT']

sql = sqlite3.connect('sql.db')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
#Posts in here will never get scanned again
cur.execute('CREATE TABLE IF NOT EXISTS requests(ID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS activedebates(ID TEXT, time TEXT, questions TEXT)')
#Posts in here are active and will be repeatedly managed
print('Loaded SQL Database')


try:
	#My credentials are saved in my python library so I can push this code to git without you seeing it.
	import bot
	USERNAME = bot.uG
	PASSWORD = bot.pG
	USERAGENT = bot.aG
except:
	pass
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)


mods = []
#This will be filled on Refresh. Leave alone.

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
	FLAIRPENDING = config['24']['FLAIRPENDING']
	#Request flair: Pending. The request has been made but mods have not seen it yet
	FLAIRDISCUSS = config['24']['FLAIRDISCUSS']
	#Request flair: Discussing. The post has been xposted to relevant subreddits and members discuss the request
	FLAIRAPPROVE = config['24']['FLAIRAPPROVE']
	#Request flair: Approved. The community and moderators have approved the subreddit and will attempt to contact the Candidate

def reqflair(post):
	print('\tChecking request flair')
	try:
		pflair = post.link_flair_text
	except:
		pflair = 'No Flair'
	print('\t-' + pflair)
	if pflair == 'No Flair':
		print('\tApplying Flair: ' + FLAIRPENDING)
		post.set_flair(FLAIRPENDING)
		return True


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

def inbox():
	print('Scanning inbox')
	pms = r.get_unread(unset_has_mail=True, update_user=True)
	for pm in pms:
		try:
			mauthor = pm.author.name.lower()
			mid = pm.id
			print(mid)
			if mauthor in mods:
				print('\tFrom moderator')
				subject = pm.subject.lower()
				bodysplit = pm.body.lower().split('\n\n')
				if subject == 'crosspost':
					url = bodysplit[0]
					subs = bodysplit[1:]
					for m in range(len(subs)):
						subs[m] = subs[m].replace('/r/','')

		except:
			pauthor = '[deleted]'


def refresh():
	#Must happen FIRST in the while loop, before any scans
	#Refresh the list of moderators
	global mods
	subreddit = r.get_subreddit(SUBREDDIT)
	moderators = subreddit.get_moderators()
	mods = []
	for moderator in moderators:
		mods.append(moderator.name.lower())


loadconfig()
refresh()