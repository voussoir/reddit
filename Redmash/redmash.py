#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import datetime
import pickle

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "all-funny-gifs-pics-aww-leagueoflegends-minecraft-mildlyinteresting-tipofmytongue-trees-askreddit"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subs, use "sub1+sub2+sub3+...". For all use "all"
KEYWORDS = [" NSA", "NSA " "Snowden", "Greenwald"]
#Words to look for
KEYDOMAINS = []
#Domains to look for
KEYNAMES = []
#Names to look for

IGNORESELF = False
#Do you want the bot to dump selfposts? Use True or False (Use capitals! No quotations!)
TIMESTAMP = '%A %d %B %Y'
#The time format.
#  "%A %d %B %Y" = "Wendesday 04 June 2014"
#http://docs.python.org/2/library/time.html#time.strftime

HEADER = ""
#Put this at the top of the .txt file

FORMAT = "_timestamp_: [_title_](_url_) - [r/_subreddit_](_nplink_)"
#USE THESE INJECTORS TO CREATE CUSTOM OUTPUT
#_timestamp_ which follows the TIMESTAMP format
#_title_
#_url_
#_subreddit_
#_nplink_
#_author_

PRINTFILE = "nsa"
#Name of the file that will be produced. Do not type the file extension

MAXPOSTS = 10000
#This is how many posts you want to retrieve all at once.

'''All done!'''

for m in ["_date", "_author", "_subreddit", "_title"]:
	clistfile = open(PRINTFILE + m + '.txt', "a+")
	clistfile.close()
#This is a hackjob way of creating the files if they do not exist.

MAXS = str(MAXPOSTS)
try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getuG()
    PASSWORD = bot.getpG()
    USERAGENT = bot.getaG()
except ImportError:
    pass

print('Logging in ' + USERNAME)
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)

def work(lista):
	global listfile
	if HEADER != "":
		print(HEADER,listfile)
	for post in lista:
		timestamp = post.created_utc
		timestamp = datetime.datetime.fromtimestamp(int(timestamp)).strftime(TIMESTAMP)
		final = FORMAT
		final = final.replace('_timestamp_', timestamp)
		final = final.replace('_title_', post.title)
		try:
			final = final.replace('_author_', post.author.name)
		except Exception:
			final = final.replace('_author_', '[DELETED]')
		final = final.replace('_subreddit_', post.subreddit.display_name)
		url = post.url
		url = url.replace('http://www.reddit.com', 'http://np.reddit.com')
		final = final.replace('_url_', url)
		slink = post.short_link
		slink = slink.replace('http://', 'http://np.')
		final = final.replace('_nplink_', slink)
		print(final, file=listfile)



lista = []
count =  0
counta = 0
try:
	print('Scanning.')
	subreddit = r.get_subreddit(SUBREDDIT)
	posts = subreddit.get_new(limit=MAXPOSTS)
	for post in posts:
		if not post.is_self or IGNORESELF == False:
			try:
				author = post.author.name
			except Exception:
				author = '[DELETED]'
			if any(m.lower() in post.title.lower() for m in KEYWORDS) \
			or any(m.lower() in post.url.lower() for m in KEYDOMAINS) \
			or any(m.lower() == author.lower() for m in KEYNAMES):
				lista.append(post)
				counta += 1
		count += 1
		print(str(count) + ' / ' + MAXS + ' | ' + str(counta))
	
	for item in lista:
		if item.author == None:
			item.author = '[DELETED]'
except Exception:
	print('EMERGENCY')

print('Collected ' + str(counta) + ' items.')
print('Writing Time file')
lista.sort(key=lambda x: x.created_utc, reverse=False)
listfile = open(PRINTFILE + '_date.txt', 'w')
work(lista)
listfile.close()

print('Writing Subreddit file')
lista.sort(key=lambda x: x.subreddit.display_name.lower(), reverse=False)
listfile = open(PRINTFILE + '_subreddit.txt', 'w')
work(lista)
listfile.close()

print('Writing Title file')
lista.sort(key=lambda x: x.title.lower(), reverse=False)
listfile = open(PRINTFILE + '_title.txt', 'w')
work(lista)
listfile.close()

print('Writing Author file')
lista.sort(key=lambda x: x.author.name.lower(), reverse=False)
listfile = open(PRINTFILE + '_author.txt', 'w')
work(lista)
listfile.close()

print('Saving to Pickle.')
class Posted(object):
	pass
listc = []
for item in lista:
	obj = Posted()
	obj.id = item.id
	obj.fullname = item.fullname
	obj.created_utc = item.created_utc
	obj.title = item.title
	obj.subreddit = item.subreddit.display_name
	obj.url = item.url
	obj.short_link = item.short_link
	try:
		obj.author = item.author.name
	except:
		obj.author = '[DELETED]'
	if item.is_self == True:
		obj.is_self = True
		obj.selftext = item.selftext
	else:
		obj.is_self = False
	listc.append(obj.__dict__)
filec = open(PRINTFILE + '.p', 'wb')
pickle.dump(listc, filec)
print('Done.')