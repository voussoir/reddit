#/u/GoldenSights
import praw
import time
import sqlite3
import datetime

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "Cinemasins"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
PRINTFILE = "userflair.txt"
#The file where the flairs will be shown

MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 30
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''



WAITS = str(WAIT)
lastwikiupdate = 0

try:
	import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
	USERNAME = bot.uG
	PASSWORD = bot.pG
	USERAGENT = bot.aG
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS users(NAME TEXT, FLAIR TEXT)')
print('Loaded Completed table')
sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 



def scan():
	print('Scanning ' + SUBREDDIT)
	subreddit = r.get_subreddit(SUBREDDIT)
	posts = []
	posts += subreddit.get_new(limit=MAXPOSTS)
	posts += subreddit.get_comments(limit=MAXPOSTS)
	for post in posts:
		try:
			pauthor = post.author.name
			try:
				pflair = post.author_flair_text
				if pflair != None:
					cur.execute('SELECT * FROM users WHERE NAME=?', [pauthor])
					fetched = cur.fetchone()
					if not fetched:
						cur.execute('INSERT INTO users VALUES(?, ?)', [pauthor, pflair])
						print('New user flair: ' + pauthor + ' : ' + pflair)
					else:
						oldflair = fetched[1]
						if pflair != oldflair:
							cur.execute('UPDATE users SET FLAIR=? WHERE NAME=?', [pflair, pauthor])
							print('Updating user flair: ' + pauthor + ' : ' + pflair)
					sql.commit()
				else:
					print(post.id, "No flair")
			except AttributeError:
				print(post.id, "No flair")
		except AttributeError:
			print(post.id, "Author is deleted")

	flairfile = open(PRINTFILE, 'w')
	cur.execute('SELECT * FROM users')
	fetch = cur.fetchall()
	fetch.sort(key=lambda x: x[0])
	flaircounts = {}
	for item in fetch:
		itemflair = item[1]
		if itemflair not in flaircounts:
			flaircounts[itemflair] = 1
		else:
			flaircounts[itemflair] += 1
	print('FLAIR: NO. OF USERS WITH THAT FLAIR', file=flairfile)
	presorted = []
	for flairkey in flaircounts:
		presorted.append(flairkey + ': ' + str(flaircounts[flairkey]))
	presorted.sort()
	for flair in presorted:
		print(flair, file=flairfile)
	print('\n\n', file=flairfile)
	print('USERNAME: USER\'S FLAIR', file=flairfile)
	for user in fetch:
		print(user[0] + ': ' + user[1], file=flairfile)
	flairfile.close()


while True:
	try:
		scan()
	except EOFError:
		print("Error:", e)
	sql.commit()
	print('Running again in ' + str(WAIT) + ' seconds')
	time.sleep(WAIT)