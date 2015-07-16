#/u/GoldenSights
import praw
import time
import sqlite3
import datetime
import traceback

'''USER CONFIGURATION'''

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
RATIO = 2
#This is the required ratio of COMMENTS divided by SUBMISSIONS

PUNISHMENTREPORT = False
#Should the bot report the comment? (Use True or False. Use Capitals, no quotations.)

PUNISHMENTREMOVE = False
#Should the bot remove the comment? (Use True or False. Use Capitals, no quotations.)

PUNISHMENTREPLY = False
PUNISHMENTREPLYSTR = "You have fallen below the comment/submission ratio of " + str(RATIO) + "."
PUNISHMENTREPLYDISTINGUISH = True
#Should the bot reply to the comment? If True, it will use this string. 

PUSHTOWIKI = True
PUSHTOWIKIFILE = "wiki.txt"
PUSHTOWIKISUBREDDIT = "GoldTesting"
PUSHTOWIKIPAGE = "heyo"
#Should the database be displayed on a subreddit wiki page?
#The wiki page (PUSHTOWIKIPAGE) will be updated in accordance to a file (PUSHTOWIKIFILE) stored in the same directory as this .py
#You must restart this bot if you edit the wiki file
PUSHTOWIKIWAIT = 120
#This is how many seconds you will wait between wiki page updates. The wiki does not need to be updated on every run

TABLESORT = 3
#This is how the Table on the wiki will be sorted
#0 = Username
#1 = Comment count
#2 = Submission count
#3 = Comment/Submission ratio

MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''



WAITS = str(WAIT)
lastwikiupdate = 0

try:
	import bot
	USERAGENT = bot.aG
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS users(NAME TEXT, COMMENTS INT, SUBMISSIONS INT, RATIO REAL)')
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
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

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
							table = '\n\nUsername | Comments | Submissions | Ratio\n'
							table += ':- | -: | -: | -:\n'
							for item in fetched:
								table += '/u/' + item[0] + ' | ' + str(item[1]) + ' | ' + str(item[2]) + ' | ' + str(item[3]) + '\n'
							table += '\n\n'
							lines[pos] = line.replace('__BUILDTABLE__', table)

						if "__STRFTIME" in line:
							print('\tBuilding timestamp')
							form = line.split('"')[1]
							now = getTime(False)
							now = now.strftime(form)
							lines[pos] = line.replace('__STRFTIME("' + form + '")__', now)
				except:
					pass

			final = '\n\n'.join(lines)
			r.edit_wiki_page(PUSHTOWIKISUBREDDIT, PUSHTOWIKIPAGE, final, reason=str(now))
			lastwikiupdate = now
			print('\tDone')

		else:
			print('Wiki page will update in ' + str(round(PUSHTOWIKIWAIT - (now-lastwikiupdate))) + ' seconds.')

def updatebase(l):
	for post in l:
		cur.execute('SELECT * FROM oldposts WHERE ID=?', [post.fullname])
		if not cur.fetchone():
			print(post.id)
			try:
				pauthor = post.author.name
				cur.execute('SELECT * FROM users WHERE NAME=?', [pauthor])
				fetched = cur.fetchone()
				if not fetched:
					print('\tNew user: ' + pauthor)
					cur.execute('INSERT INTO users VALUES(?, ?, ?, ?)', [pauthor, 0, 0, 0])
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
				cur.execute('UPDATE users SET COMMENTS=?, SUBMISSIONS=?, RATIO=? WHERE NAME=?', [comments, submissions, ratio, pauthor])

				if ratio < RATIO:
					print("\tUser's ratio is too low!")
					if PUNISHMENTREPORT:
						print('\tReporting post')
						post.report()
					if PUNISHMENTREMOVE:
						print('\tRemoving post')
						post.remove()
					if PUNISHMENTREPLY:
						print('\tReplying to post')
						if type(post) == praw.objects.Submission:
							new = post.add_comment(PUNISHMENTREPLYSTR)
						if type(post) == praw.objects.Comment:
							new = post.reply(PUNISHMENTREPLYSTR)
						if PUNISHMENTREPLYDISTINGUISH:
							print('\tDistinguishing reply')
							new.distinguish()

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