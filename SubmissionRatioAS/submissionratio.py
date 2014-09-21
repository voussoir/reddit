#/u/GoldenSights
import praw
import time
import sqlite3
import datetime
import traceback

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "AskScience"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."

PUSHTOWIKI = True
PUSHTOWIKIFILE = "wiki.txt"
PUSHTOWIKISUBREDDIT = "GoldTesting"
PUSHTOWIKIPAGE = "batman"
#Should the database be displayed on a subreddit wiki page?
#The wiki page (PUSHTOWIKIPAGE) will be updated in accordance to a file (PUSHTOWIKIFILE) stored in the same directory as this .py
#You must restart this bot if you edit the wiki file
PUSHTOWIKIWAIT = 60
#This is how many seconds you will wait between wiki page updates. The wiki does not need to be updated on every run

TABLESORT = 0
#This is how the Table on the wiki will be sorted
#0 = Username
#1 = Comment count
#2 = Submission count
#3 = Comment/Submission ratio

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

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS users(NAME TEXT, COMMENTS INT, SUBMISSIONS INT, RATIO REAL, FLAIR TEXT)')
print('Loaded Completed table')

if PUSHTOWIKI:
	try:
		wikifile = open(PUSHTOWIKIFILE, 'r')
		print('Loaded Wiki file')
	except FileNotFoundError:
		wikifile = open(PUSHTOWIKIFILE, 'w')
		print('Wiki File was not found, and has been created')

sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

def getTime(bool):
	timeNow = datetime.datetime.now(datetime.timezone.utc)
	timeUnix = timeNow.timestamp()
	if bool == False:
		return timeNow
	else:
		return timeUnix

def updatewiki():
	global lastwikiupdate
	if PUSHTOWIKI:
		now = getTime(True)
		if now - lastwikiupdate > PUSHTOWIKIWAIT:
			print('Updating wiki page "' + PUSHTOWIKIPAGE + '"')
			with open(PUSHTOWIKIFILE, 'r') as temp:
				lines = [line.strip() for line in temp]

			for pos in range(len(lines)):
				line = lines[pos]

				try:
					if line[0] == '#':
						lines[pos] = ''
					else:
						if "__BUILDTABLE__" in line:
							print('\tBuilding Table')
							cur.execute('SELECT * FROM users')
							fetched = cur.fetchall()
							try:
								fetched.sort(key=lambda x: x[TABLESORT].lower())
							except:
								fetched.sort(key=lambda x: x[TABLESORT])
							if TABLESORT != 0:
								fetched.reverse()
							table = '\n\nUsername | Flair | Comments | Submissions | Ratio\n'
							table += ':- | :- | -: | -: | -:\n'
							for item in fetched:
								table += '/u/' + item[0] + ' | ' + item[4] + ' | ' + str(item[1]) + ' | ' + str(item[2]) + ' | ' + str(item[3]) + '\n'
							table += '\n\n'
							lines[pos] = line.replace('__BUILDTABLE__', table)

						if "__STRFTIME" in line:
							print('\tBuilding timestamp')
							form = line.split('"')[1]
							tnow = getTime(False)
							tnow = tnow.strftime(form)
							lines[pos] = line.replace('__STRFTIME("' + form + '")__', tnow)
				except:
					pass

			final = '\n\n'.join(lines)
			r.edit_wiki_page(PUSHTOWIKISUBREDDIT, PUSHTOWIKIPAGE, final, reason=str(now))
			lastwikiupdate = now
			print('\tDone')

		else:
			willwait = round(PUSHTOWIKIWAIT - (now-lastwikiupdate))
			if willwait > WAIT:
				print('Wiki page will update in ' + str(willwait) + ' seconds.')
			else:
				print('Wiki page will update on the next run through.')

def updatebase(l):
	for post in l:
		userflair = None
		cur.execute('SELECT * FROM oldposts WHERE ID=?', [post.fullname])
		if not cur.fetchone():
			print(post.id)
			try:
				pauthor = post.author.name
				userflair = post.author_flair_text
				if userflair != '' and userflair != None:
					userflair = userflair.replace('|', '/')
					cur.execute('SELECT * FROM users WHERE NAME=?', [pauthor])
					fetched = cur.fetchone()
					if not fetched:
						print('\tNew user: ' + pauthor)
						cur.execute('INSERT INTO users VALUES(?, ?, ?, ?, ?)', [pauthor, 0, 0, 0, userflair])
						fetched = [pauthor, 0, 0, 0]
					comments = fetched[1]
					submissions = fetched[2]
					if type(post) == praw.objects.Comment:
						comments = comments + 1
					if type(post) == praw.objects.Submission:
						submissions = submissions + 1
					denominator = (1 if submissions == 0 else submissions)
					ratio = "%0.2f" % (comments / denominator)
					print('\t' + pauthor)
					print('\t' + str(comments) + 'c / ' + str(denominator) + 's = ' + str((comments / denominator))[:3])
					ratio = float(ratio)
					cur.execute('UPDATE users SET COMMENTS=?, SUBMISSIONS=?, RATIO=?, FLAIR=? WHERE NAME=?', [comments, submissions, ratio, userflair, pauthor])

			except AttributeError:
				print('\tComment or Author has been deleted')
			cur.execute('INSERT INTO oldposts VALUES(?)', [post.fullname])
		sql.commit()

def scan():
	print('Scanning ' + SUBREDDIT)
	subreddit = r.get_subreddit(SUBREDDIT)

	print('\tGathering submissions')
	posts = list(subreddit.get_new(limit=MAXPOSTS))
	updatebase(posts)

	print()

	print('\tGathering comments')
	comments = list(subreddit.get_comments(limit=MAXPOSTS))
	updatebase(comments)


	
while True:
	try:
		scan()
		print()
		updatewiki()
	except:
		traceback.print_exc()
	print('Running again in ' + WAITS + ' seconds.\n')
	time.sleep(WAIT)