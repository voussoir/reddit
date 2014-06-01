import praw
import time
import datetime
import sqlite3

'''USER CONFIGURATION'''

USERNAME = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter Bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
MAXPOSTS = 30
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
DELAY = 86400
#This is the time between Daily threads, IN SECONDS. 1h = 3600 || 12h = 43200 || 24h = 86400 || 144h = 518400
#Obviously daily means 24h, but it's always nice to have configurability
BODY = '[d]\n\nThis thread is for the days you draw a lucky number for which there is no matching OTN thread.\n\nPlease follow this commenting format^1\n\n>My lucky number: #####\n\n>Time until midnight\n\n>My OTN thread\n\n>The Prize I wish to win\n\nThis way other players can check if a traded pokemon has the number.\n\nMay the odds be ever in your favor.\n\n^1: ^The ^last ^five ^characters ^of ^your ^first ^line ^should ^be ^your ^OTN ^only. ^Do ^NOT ^bolden, ^italicize, ^or ^otherwise ^mark ^it. ^Do ^not ^add ^puncutation ^to ^it'
#This is the body of Dailythreads. It follows reddit's usual markdown syntax where \n\n stars a new line
NORESULTS = 'We have checked your lucky number against our database, but found no matches!'
#This is what the bot says to you if your comment in Daily doesn't match any databased OTNs
YESRESULTS = 'We have matched your lucky number against our database. Check it out!'
#This is what the bot says to you if your comment in Daily matches some results. The result chart comes immediatly after this.
'''All done!'''






WAITS = str(WAIT)
try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getuG()
    PASSWORD = bot.getpG()
    USERAGENT = bot.getaG()
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS daily(id TEXT)')
print('Loaded previous Daily')
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT, otn TEXT)')
print('Loaded OTN numbers')
cur.execute('CREATE TABLE IF NOT EXISTS oldcomments(id TEXT)')
print('Loaded old comments')
sql.commit()

r = praw.Reddit(USERAGENT)

Trying = True
while Trying:
	try:
		r.login(USERNAME, PASSWORD)
		print('Successfully logged in')
		Trying = False
	except praw.errors.InvalidUserPass:
		print('Wrong Username or Password')
		quit()
	except Exception as e:
		print("%s" % e)
		time.sleep(5)

def getTime(bool):
	timeNow = datetime.datetime.now(datetime.timezone.utc)
	timeUnix = timeNow.timestamp()
	if bool == False:
		return timeNow
	else:
		return timeUnix

def generateReport(number):
	print('Attemping to generate report for luckynumber ' + number)
	cur.execute('SELECT * FROM oldposts')
	f = cur.fetchall()
	idlist = []
	otnlist = []
	results = []
	for m in f:
		idlist.append(m[0])
		otnlist.append(m[1])
	for m in range(len(otnlist)):
		otn = otnlist[m]
		mid = idlist[m]
		if otn == number:
			results.append(number + '|http://redd.it/' + mid)

		elif otn[-4:] == number[-4:]:
			results.append('*' + number[-4:] + '|http://redd.it/' + mid)


		elif otn[-3:] == number[-3:]:
			results.append('**' + number[-3:] + '|http://redd.it/' + mid)

		elif otn[-2:] == number[-2:]:
			results.append('***' + number[-2:] + '|http://redd.it/' + mid)
	results = sorted(results)
	if len(results) == 0:
		print('\tNo results!')
		s = NORESULTS
	else:
		print('\tSuccessfuly generated report')
		s = '\n'.join(results)
		s = YESRESULTS + '\n\nMatch|Thread\n:-|:-\n' + s

	return s


	
def scan():
	print('Scanning ' + SUBREDDIT + ' for new OTN posts')
	subreddit = r.get_subreddit(SUBREDDIT)
	posts = subreddit.get_new(limit=MAXPOSTS)
	for post in posts:
		pid = post.id
		if post.link_flair_text == 'OTN':
			cur.execute('SELECT * FROM oldposts WHERE id="%s"' % pid)
			if not cur.fetchone():
				ptitle = post.title
				try:
					int(ptitle)
				except ValueError:
					ptitle = 'NULL'
				print(pid + ': ' + ptitle)
				cur.execute('INSERT INTO oldposts VALUES("%s", "%s")' % (pid, ptitle))
		sql.commit()

def daily():
	print('Managing Dailypost')
	nowtime = getTime(True)
	nowdate = time.strftime("%d %B %Y")
	print('It is ' + nowdate + ' || ' + str(nowtime))
	cur.execute('SELECT * FROM daily')
	f = cur.fetchone()
	try:
		previd = f[0]
		prevpost = r.get_info(thing_id='t3_' + previd)
		prevtime = prevpost.created_utc
		prevtitle = prevpost.title
	except TypeError:
		print('Database does not have a Dailythread yet. Creating one')
		previd = '0'
		prevtime = 0
		prevtitle = 'None'
	print('Previous Daily: ' + previd + ' "' + prevtitle + '"')
	difference = nowtime - prevtime
	if difference >= DELAY or nowdate not in prevtitle:
		print('Previous Dailypost is too old')
		try:
			prevpost.mark_as_nsfw()
		except UnboundLocalError:
			pass
		title = 'Daily lucky number checking thread - ' + nowdate
		newpost = r.submit(SUBREDDIT, title, text=BODY, captcha=None)
		newid = newpost.id
		print('Created new Dailypost with id ' + newid)
		cur.execute('DELETE FROM daily WHERE id="%s"' % previd)
		cur.execute('INSERT INTO daily VALUES("%s")' % newid)
		sql.commit()
	else:
		print('Scanning root comments')
		comments = prevpost.comments
		for comment in comments:
			if comment.is_root:
				cid = comment.id
				cur.execute('SELECT * FROM oldcomments WHERE id="%s"' % cid)
				if not cur.fetchone():
					cbody = comment.body.lower()
					cbodysplit = cbody.split('\n\n')
					try:
						int(cbodysplit[0][-5:])
						number = cbodysplit[0][-5:] #Str
						report = generateReport(number)
						comment.reply(report)
					except ValueError:
						pass
					cur.execute('INSERT INTO oldcomments VALUES("%s")' % cid)
			sql.commit()

while True:
	try:
		scan()
	except Exception as e:
		print('An error has occured during scan:', e)
	print('')
	try:
		daily()
	except Exception as e:
		print('An error has occured during daily:', e)
	print('Running again in ' + WAITS + ' seconds.\n')
	sql.commit()
	time.sleep(WAIT)
