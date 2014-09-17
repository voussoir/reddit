#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import json
import urllib.request
from bs4 import BeautifulSoup

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"

#This bot gets its subreddits from subreddit.txt

MAXPERTHREAD = 4
#This is the maximum number of individuals to be fetched in a single thread

COMMENTHEADER = ""
#At the top of the comment
COMMENTALSOSEE = "**Also see:**"
#After the first individual's full rundown
COMMENTFOOTER = "This comment was automatically generated. [Source Code](https://github.com/voussoir/reddit/tree/master/Politician)"
#At the bottom of the comment
#Newline characters will be managed automatically in all three

MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''




WAITS = str(WAIT)

with open('full.txt', 'r') as f:
	FULL = json.loads(f.read())
with open('nick.txt', 'r') as f:
	NICK = json.loads(f.read())
print('Loaded name tables.')
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
cur.execute('CREATE TABLE IF NOT EXISTS oldthreads(ID TEXT, COUNT INT, NAMES TEXT)')
print('Loaded Completed table')

sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

def generatepolitician(iid, terminate=False):
	print('Fetching ' + iid)
	url = 'https://www.opensecrets.org/politicians/summary.php?cycle=2014&cid=%s&type=I' % iid
	filea = BeautifulSoup(urllib.request.urlopen(url))
	
	comment = ''
	
	comment += '[**' + filea.find_all('h1')[1].string
	comment += ', ' + filea.find(id='title').string + '**](' + url + ')\n\n'

	if terminate:
		return comment
	
	elecinfo = filea.find(id='elec').contents
	comment += elecinfo[1].string + ', '
	comment += elecinfo[2].strip() + '\n\n.\n\n'
	
	f = filea.find(id='summaryData').find_all('td')
	l = []
	for i in f:
		for c in i.contents:
			c = str(c).strip().replace('\n', '')
			if '$' in c:
				l.append(c.split()[-1])
				

	h = filea.find(id='profileLeftColumn')
	h = h.h2.contents[-1]
	comment += '**' + h + '**\n\n'
	table = 'Raised | ' + l[0] + '\n:- | -:\n'
	table += 'Spent | ' + l[1] + '\n'
	table += 'Cash on hand | ' + l[2] + '\n'
	table += 'Debts | ' + l[3] + '\n'
	
	comment += table

	comment += '\n\n.\n\n'

	h2s = filea.find_all('h2')
	h = h2s[2].string
	comment += '**' + h + '**\n\n'
	table = 'Industry | Total | Indivs | PACs\n:- | -: | -: | -:\n'
	industries = filea.find(id='topIndus').contents
	item = industries[1]
	contents = item.contents
	for i in contents:
		for x in i:
			table += x.string + ' | '
		table += '\n'

	comment += table

	return comment

def dropfrom(filename, content):
	print('Dropping ' + content + ' from ' + filename)
	f = open(filename, 'r')
	l = [line.strip() for line in f.readlines()]
	f.close()
	for i in range(len(l)):
		item = l[i]
		if content.lower() == item.lower():
			l[i] = ''
	while '' in l:
		l.remove('')
	while '\n' in l:
		l.remove('\n')
	f = open(filename, 'w')
	for item in l:
		print(item, file=f)
	f.close()


def scan():
	print('\nChecking blacklist')
	blackfile = open('blacklist.txt', 'r')
	blacklist = blackfile.readlines()
	blackfile.close()

	print('Checking subreddits\n')
	subfile = open('subreddit.txt', 'r')
	sublist = subfile.readlines()
	while '' in sublist:
		sublist.remove('')
	subfile.close()

	if sublist == []:
		print('Subreddit list is empty')
		return
		
	SUBREDDIT = '+'.join(sublist)

	print('Scanning ' + SUBREDDIT)
	subreddit = r.get_subreddit(SUBREDDIT)
	print('Getting submissions...')
	posts = list(subreddit.get_new(limit=MAXPOSTS))
	print('Getting comments...')
	posts += list(subreddit.get_comments(limit=MAXPOSTS))

	for post in posts:
		cur.execute('SELECT * FROM oldposts WHERE ID=?', [post.fullname])
		if not cur.fetchone():
			print(post.fullname + ': New')
			ids = []
			try:
				pauthor = post.author.name.lower()
				if not any(pauthor == blacklisted.lower() for blacklisted in blacklist):
					if type(post) == praw.objects.Comment:
						submissionid = post.link_id
					if type(post) == praw.objects.Submission:
						submissionid = post.fullname
					print(post.fullname + ': Passed blacklist check')
					cur.execute('SELECT * FROM oldthreads WHERE ID=?', [submissionid])
					fetched = cur.fetchone()
					if not fetched:
						cur.execute('INSERT INTO oldthreads VALUES(?, ?, ?)', [submissionid, 0, ''])
						fetched = [submissionid, 0, '']
					
					if fetched[1] <= MAXPERTHREAD:
						if type(post) == praw.objects.Submission:
							pbody = post.title.lower() + '\n\n' + post.selftext.lower()
						if type(post) == praw.objects.Comment:
							pbody = post.body.lower()
						#print(pbody)
						for member in FULL:
							if member.lower() in pbody:
								idd = FULL[member]
								if idd not in ids:
									ids.append(idd)
						for member in NICK:
							if member.lower() in pbody:
								idd = NICK[member]
								if idd not in ids:
									ids.append(idd)
					else:
						print(submissionid + ': Already reached limit for thread')
				else:
					print(post.fullname + ': Author ' + pauthor + ' is blacklisted.')
			except AttributeError:
				print(post.fullname + ': Author is deleted.')

			ids = ids[:5]
			if len(ids) > 0:
				print(post.fullname + ': Produced ' + str(len(ids)) + ' items.')
				print('\t', ids)
				count = fetched[1]
				print(submissionid + ': has', count)
				alreadyseen = fetched[2].split()
				print(submissionid + ': already seen:', alreadyseen)
				for item in range(len(ids)):
					if ids[item] in alreadyseen:
						print('\t' + ids[item] + ' has already been seen in this thread')
						ids[item] = ''
				while '' in ids:
					ids.remove('')

			if len(ids) > 0:
				newcomment = COMMENTHEADER + '\n\n'
				newcomment += generatepolitician(ids[0])
				if len(ids) > 1:
					newcomment += '\n\n.\n\n' + COMMENTALSOSEE + '\n\n'
					for member in ids[1:]:
						newcomment += generatepolitician(member, terminate=True)
				newcomment += '\n\n' + COMMENTFOOTER

				print(post.fullname + ': Writing reply.')
				try:
					if type(post) == praw.objects.Submission:
						post.add_comment(newcomment)
					if type(post) == praw.objects.Comment:
						post.reply(newcomment)
				except praw.request.exceptions.HTTPError:
					print('HTTPError. Probably banned in this sub')
					dropfrom(subreddit.txt, post.subreddit.display_name)

				alreadyseen = ' '.join(alreadyseen) + ' ' + ' '.join(ids)

				cur.execute('UPDATE oldthreads SET COUNT=?, NAMES=? WHERE ID=?', [count+len(ids), alreadyseen, submissionid])
			cur.execute('INSERT INTO oldposts VALUES(?)', [post.fullname])
		sql.commit()


while True:
	scan()
	print('Running again in ' + WAITS + ' seconds.')
	time.sleep(WAIT)