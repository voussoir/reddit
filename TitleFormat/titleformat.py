#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
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

FORMATS = ['[*] * - *']
#These are the permitted title formats

REMOVECOMMENT = "Your submission has been removed because the title does not follow a permitted format. Please check the sidebar"
#This is what the bot will say 
DISTINGUISHCOMMENT = True
#If your bot is a moderator, you can distinguish the comment. Use True or False (Use capitals! No quotations!)

IGNOREMODS = False
#Do you want the bot to ignore posts made by moderators? Use True or False (With capitals! No quotations!)
IGNORESELFPOST = False
#Do you want the bot to ignore selfposts?

MAXPOSTS = 15
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''

WAITS = str(WAIT)
done = False


try:
	import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
	USERNAME = bot.getuG()
	PASSWORD = bot.getpG()
	USERAGENT = bot.getaG()
except ImportError:
    pass
WAITS = str(WAIT)
sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded Completed table')
sql.commit()
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)
	
def work(a, format):
	pos = 0
	global done
	score = 0
	scorr = len(format.replace('*',''))
	for char in a:
		#print(char + ' | ', end='')
		if char == format[pos]:
			#print(format[pos])
			score +=1
			pos+=1
		else:
			#print('*')
			pass
	
		if pos >= len(format):
			pos = len(format)-1
	
		if format[pos] == '*':
			pos +=1
	
		if pos >= len(format):
			pos = len(format)-1
	if (format[0] != '*' and (format[0] != a[0])) or (format[len(format)-1] != '*' and (format[len(format)-1] != a[len(a)-1])):
		score -=1
	print(a + ':',score,'/',scorr)
	if score == scorr:
		done = True
	return done

def scanSub():
	global done
	print('Scanning '+ SUBREDDIT + '.')
	subreddit = r.get_subreddit(SUBREDDIT)
	moderators = subreddit.get_moderators()
	mods = []
	for moderator in moderators:
		mods.append(moderator.name)
	posts = subreddit.get_new(limit=MAXPOSTS)
	for post in posts:
		ptitle = post.title
		try:
			pauthor = post.author.name
		except AttributeError:
			pauthor = '[DELETED]'
		pid = post.id
		cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
		if not cur.fetchone():
			print(pid + ': ' + pauthor)
			if post.is_self == False or IGNORESELFPOST == False:
				if pauthor not in mods or IGNOREMODS == False:
					ptitle = post.title
					done = False
					for format in FORMATS:
						print('\t',end='')
						work(ptitle, format)
					if done == False:
						try:
							print('\tWriting comment')
							newcom = post.add_comment(REMOVECOMMENT)
							print('\tDistinguishing comment')
							newcom.distinguish()
							print('\tRemoving post')
							post.remove()
						except praw.errors.APIException:
							print('\tPost is deleted. Ignoring')
				else:
					print('\tIgnoring modpost.')
			else:
				print('\tIgnoring selfpost')
			cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
	sql.commit()

#scanSub()
while True:
	try:
		scanSub()
	except Exception as e:
		print('An error has occured:', e)
	sql.commit()
	print('Running again in ' + WAITS + ' seconds.\n')
	time.sleep(WAIT)