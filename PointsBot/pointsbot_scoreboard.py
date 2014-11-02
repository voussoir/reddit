#/u/GoldenSights
import datetime
import praw
import time
import sqlite3

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
PARENTSTRING = ["Solution Verified"]
MODSTRING = ["+1 Point"]
#These are the words you are looking for. If User says this, Parent gets 1 point in his flair
REPLYSTRING = "You have awarded one point to _parent_"
#This is the phrase that User will receive
#_parent_ will be replaced by the username of the Parent.
EXEMPT = []
#Any usernames in this list will not receive points. Perhaps they have special flair.

OPONLY = False
#Is OP the only person who can give points?
#I recommend setting this to False. Other users might have the same question and would like to reward a good answer.

MAXPERTHREAD = 200
#How many points can be distributed in a single thread?
EXPLAINMAX = True
#If the max-per-thread is reached and someone tries to give a point, reply to them saying that the max has already been reached
EXPLAINREPLY = "Sorry, but " + str(MAXPERTHREAD) + " point(s) have already been distributed in this thread. This is the maximum allowed at this time."
#If EXPLAINMAX is True, this will be said to someone who tries to give a point after max is reached

MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

LEADERBOARDPAGE = "leaderboard"
#This is the wiki page it will put the full leaderboard on
#Seen at /r/subreddit/wiki/LEADERBOARDPAGE
LEADERBOARDUPDATERATE = 5
#Set this to 1 if you want the leaderboard to update after every new point
#Or 5 for every fifth point, etc
LEADERBOARDTOPX = 10
#Leaderboard in sidebar will show this many users. Top 10 for example
LEADERBOARDHEADER = "\n\n[Top Breakers:](http://www.reddit.com/r/GoldTesting/wiki/leaderboard)\n\nRank | Username | Points\n-: | :- | -:"
#Setting up the table.


'''All done!'''



WAITS = str(WAIT)
leaderboardtick = 0
#Do not touch.

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
cur.execute('CREATE TABLE IF NOT EXISTS submissions(ID TEXT, count INT)')
cur.execute('CREATE TABLE IF NOT EXISTS users(NAME TEXT, POINTS TEXT)')
print('Loaded Completed table')

sql.commit()

print('Logging in')
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

print('Collecting subreddit moderators')
MODERATORS = []
s = SUBREDDIT.split('+')
for x in s:
	x = r.get_subreddit(x)
	m = list(x.get_moderators())
	for p in range(len(m)):
		m[p] = m[p].name

	MODERATORS += m
print(MODERATORS)

def getTime(bool):
	timeNow = datetime.datetime.now(datetime.timezone.utc)
	timeUnix = timeNow.timestamp()
	if bool == False:
		return timeNow
	else:
		return timeUnix
		
def flair(subreddit, username):
	global leaderboardtick
	#Subreddit must be the sub object, not a string
	#Returns True if the operation was successful
	success = False
	print('\tChecking flair for ' + username)
	flairs = subreddit.get_flair(username)
	flairs = flairs['flair_text']
	if flairs != None and flairs != '':
		print('\t :' + flairs)
		try:
			flairs = int(flairs)
			flairs += 1
			flairs = str(flairs)
			success = True
		except ValueError:
			print('\tCould not convert flair to a number.')
	else:
		print('\tNo current flair. 1 point')
		flairs = '1'
		success = True
	print('\tAssigning Flair: ' + flairs)
	subreddit.set_flair(username, flairs)

	if success:
		cur.execute('SELECT * FROM users WHERE NAME=?', [username])
		f = cur.fetchone()
		if f:
			cur.execute('UPDATE users SET POINTS=? WHERE NAME=?', [flairs, username])
		else:
			cur.execute('INSERT INTO users VALUES(?, ?)', [username, flairs])
		sql.commit()
		leaderboardtick += 1

	return success


def scan():
	global leaderboardtick
	print("Scanning " + SUBREDDIT)
	subreddit = r.get_subreddit(SUBREDDIT)
	comments = subreddit.get_comments(limit=MAXPOSTS)
	for comment in comments:
		cid = comment.id
		cur.execute('SELECT * FROM oldposts WHERE ID=?', [cid])
		if not cur.fetchone():
			print(cid)
			cbody = comment.body.lower()
			try:
				if not comment.is_root:
					cauthor = comment.author.name
					
					if (cauthor not in MODERATORS and any(flag.lower() in cbody for flag in PARENTSTRING)) or\
					   (cauthor in MODERATORS and any(flag.lower() in cbody for flag in MODSTRING)):
						print('\tFlagged.')
						print('\tFetching parent and Submission data.')
						parentcom = r.get_info(thing_id=comment.parent_id)
						pauthor = parentcom.author.name
						op = comment.submission.author.name
						opid = comment.submission.id

						if pauthor != cauthor:
							if not any(exempt.lower() == pauthor.lower() for exempt in EXEMPT):
								if OPONLY == False or cauthor == op or cauthor in MODERATORS:
									cur.execute('SELECT * FROM submissions WHERE ID=?', [opid])
									fetched = cur.fetchone()
									if not fetched:
										cur.execute('INSERT INTO submissions VALUES(?, ?)', [opid, 0])
										fetched = 0
									else:
										fetched = fetched[1]

									if fetched < MAXPERTHREAD:
										if flair(subreddit, pauthor):
											print('\tWriting reply')
											comment.reply(REPLYSTRING.replace('_parent_', pauthor))
											cur.execute('UPDATE submissions SET count=? WHERE ID=?', [fetched+1, opid])
									else:
										print('\tMaxPerThread has been reached')
										if EXPLAINMAX == True:
											print('\tWriting reply')
											comment.reply(EXPLAINREPLY)
								else:
									print('\tOther users cannot give points.')
							else:
								print('\tParent is on the exempt list.')
						else:
							print('\tCannot give points to self.')
				else:
					print('\tRoot comment. Ignoring.')

			except AttributeError:
				print('\tCould not fetch usernames. Cannot proceed.')


			cur.execute('INSERT INTO oldposts VALUES(?)', [cid])
		sql.commit()
	if leaderboardtick >= LEADERBOARDUPDATERATE:
		updateleaders(subreddit)
		leaderboardtick = 0

def updateleaders(subreddit):
	print('Making leaderboards')
	now = getTime(False)
	now = datetime.datetime.strftime(now, "%B %d %Y, %H:%M UTC")
	cur.execute('SELECT * FROM users')
	f = cur.fetchall()
	doloop = True
	while doloop:
		doloop = False
		for name in f:
			try:
				int(name[1])
			except ValueError:
				doloop = True
				f.remove(name)
	f.sort(key=lambda x:int(x[1]))
	f.reverse()
	tabledata = []
	for x in range(len(f)):
		tabledata.append(str(x+1) + ' | /u/' + f[x][0] + ' | ' + f[x][1])
	finaltable = LEADERBOARDHEADER + '\n' + '\n'.join(tabledata)
	finaltable += '\n\n' + now
	print('Built table')

	print('Setting wiki page: ' + LEADERBOARDPAGE)
	subreddit.edit_wiki_page(LEADERBOARDPAGE, finaltable, reason=now)

	finaltable = LEADERBOARDHEADER + '\n' + '\n'.join(tabledata[:LEADERBOARDTOPX])
	finaltable += '\n\n' + now
	subdesc = subreddit.description
	subdesc = subdesc.split(LEADERBOARDHEADER)[0]
	subdesc += finaltable
	print('Setting sidebar')
	subreddit.update_settings(description=subdesc)
	print('Finished leaderboards')
	
while True:
	try:
		scan()
	except Exception as e:
		print('ERROR:', e)
	print('Running again in ' + WAITS + ' seconds.\n')
	time.sleep(WAIT)