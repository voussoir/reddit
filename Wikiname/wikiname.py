import praw
import sqlite3
import time
import string


USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "pics+gifs+funny+askreddit"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
WIKISUBREDDIT = "GoldTesting"
#This is the subreddit which owns the wikipage. Perhaps you wish to document posts on subs other than your own.
WIKIPAGE = "Gold"
#This is the page of the wiki that you will be editing
MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
VERBOSE = False
#IF Verbose is set to true, the console will spit out a lot more information. Use True or False (Use capitals! No quotations!)


'''All done!'''




WAITS = str(WAIT)
letters = string.ascii_uppercase
lets = string.ascii_letters
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
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')
print('Loaded Oldposts')
sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)

def scan():
	print('Reading Wiki')
	names = []
	finals = []
	wikisubreddit = r.get_subreddit(WIKISUBREDDIT)
	wikipage = r.get_wiki_page(wikisubreddit, WIKIPAGE)
	pcontent = wikipage.content_md
	print('Gathering names')
	pcontentsplit = pcontent.split('\n')
	for item in pcontentsplit:
		if 'http://' in item:
			names.append(item.replace('\r',''))

	print('Scanning ' + SUBREDDIT)
	scansub = r.get_subreddit(SUBREDDIT)
	posts = scansub.get_new(limit=MAXPOSTS)
	for post in posts:
		pid = post.id
		plink = post.permalink
		cur.execute('SELECT * FROM oldposts WHERE id=?', [pid])
		if not cur.fetchone():
			try:
				pauthor = post.author.name
				print(pid + ': ' + pauthor)
				for item in names:
					if pauthor in item:
						print('\tDeleting old entry')
						names.remove(item)
				print('\tAdding new entry')
				names.append('[' + pauthor + '](' + plink + ')')
			except AttributeError:
				print(pid + ': Post deleted')
			cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
		sql.commit()



	names = sorted(names, key=str.lower)
	if VERBOSE == True:
		print(names)
	finals.append('**0-9 and others**\n\n_____\n\n')
	for item in names:
		if item[1] not in lets:
			finals.append(item + '\n\n')
	for letter in letters:
		finals.append('**' + letter + '**\n\n_____\n\n')
		for item in names:
			if item[1].lower() == letter.lower():
				finals.append(item + '\n\n')
	if VERBOSE == True:
		print(finals)
	print('Saving wiki page')
	wikipage.edit(''.join(finals))





while True:
#	scan()
#	sql.commit()
	try:
		scan()
		sql.commit()
	except Exception:
		print('fail')
	print('Running again in ' + WAITS + ' seconds.\n')
	time.sleep(WAIT)