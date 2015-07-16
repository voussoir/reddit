#/u/GoldenSights
import traceback
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import datetime
import pickle
import string

'''USER CONFIGURATION'''

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "nsaleaks"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subs, use "sub1+sub2+sub3+...". For all use "all"
KEYWORDS = string.ascii_letters
#Words to look for
KEYDOMAINS = []
#Domains to look for
KEYNAMES = [""]
#Names to look for

IGNORESELF = False
#Do you want the bot to dump selfposts? Use True or False (Use capitals! No quotations!)
TIMESTAMP = '%A %d %B %Y'
#The time format.
#  "%A %d %B %Y" = "Wendesday 04 June 2014"
#http://docs.python.org/2/library/time.html#time.strftime

HEADER = ""
#Put this at the top of the .txt file

#FORMAT = "_timestamp_: [_title_](_url_) - /u/_author_ - [**Discussion**](_nplink_)"
FORMAT = ">>\n* [_title_](_url_) - _flairtext_\n>>"
TSFORMAT = ">_timestamp_\n"
#USE THESE INJECTORS TO CREATE CUSTOM OUTPUT
#_timestamp_ which follows the TIMESTAMP format
#_title_
#_url_
#_subreddit_
#_nplink_
#_author_
#_numcomments_
#_score_

PRINTFILE = "nsa"
#Name of the file that will be produced. Do not type the file extension

MAXPOSTS = 100
#This is how many posts you want to retrieve all at once.

READ_FROM_FILE = "botwatch.db"
# A text file where a post ID is on each line
# These will be collected before anything from /new

'''All done!'''

try:
    import bot
    USERAGENT = bot.aG
except ImportError:
    pass

print('Logging in.')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def scansub():
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
			print('%d / %d | %d' % (count, MAXPOSTS, counta))
		
		for item in lista:
			if item.author is None:
				item.author = '[DELETED]'
	except Exception:
		traceback.print_exc()
	print('Collected ' + str(counta) + ' items.')
	return lista

def scanfile():
	idfile = open(READ_FROM_FILE)
	lines = [line.strip() for line in idfile.readlines()]
	idfile.close()
	for lineindex in range(len(lines)):
		if 't3_' not in lines[lineindex]:
			lines[lineindex] = 't3_' + lines[lineindex]
	filesize = len(lines)
	print('Found %d ids in file %s' % (filesize, READ_FROM_FILE_IDS))

	lista = []
	count = 0
	while len(lines) > 0:
		posts = list(r.get_info(thing_id=lines[:100]))
		lines = lines[100:]
		for post in posts:
			if post.author is None:
				post.author = '[DELETED]'
			lista.append(post)
			count += 1
		print('%d / %d' % (count, filesize))
	return lista


def work(lista, listfile):
	if HEADER != "":
		print(HEADER, file=listfile)
	previous_timestamp = ""
	for post in lista:
		timestamp = post.created_utc
		timestamp = datetime.datetime.fromtimestamp(int(timestamp)).strftime(TIMESTAMP)
		final = FORMAT
		if timestamp != previous_timestamp:
			final = TSFORMAT + final
		final = final.replace('_timestamp_', timestamp)
		final = final.replace('_title_', post.title)
		flair_text = post.link_flair_text if post.link_flair_text else ""
		flair_css = post.link_flair_css_class if post.link_flair_css_class else ""
		post.link_flair_text = flair_text
		post.link_flair_css_class = flair_css
		final = final.replace('_flairtext_', flair_text)
		final = final.replace('_flaircss_', flair_css)
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
		final = final.replace('_flairtext_', flair_text)
		final = final.replace('_score_', str(post.score))
		final = final.replace('_numcomments_', str(post.num_comments))
		print(final, file=listfile)
		previous_timestamp = timestamp


def writeindividual(printstatement, lista, sortmode, reverse, filesuffix):
	print(printstatement)
	lista.sort(key=sortmode, reverse=reverse)
	listfile = open(PRINTFILE + filesuffix, 'w', encoding='utf-8')
	work(lista, listfile)
	listfile.close()


def writefiles(lista):
	writeindividual('Writing time file', lista,
		lambda x:x.created_utc, True, '_date.txt')
	
	writeindividual('Writing subreddit file', lista,
		lambda x:x.subreddit.display_name.lower(), False, '_subreddit.txt')
	
	writeindividual('Writing title file', lista,
		lambda x:x.title.lower(), False, '_title.txt')
	
	writeindividual('Writing author file', lista,
		lambda x:x.author.name.lower(), False, '_author.txt')
	
	print('Writing flair file')
	now = datetime.datetime.now(datetime.timezone.utc).timestamp()
	lista.sort(key=lambda x: (x.link_flair_text, now-x.created_utc))
	for index in range(len(lista)):
		if lista[index].link_flair_text != "":
			lista = lista[index:] + lista[:index]
			break
	listfile = open(PRINTFILE + '_flair.txt', 'w', encoding='utf-8')
	work(lista, listfile)
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
	filec.close()
	print('Done.')

def removeduplicates(lista):
	print('Removing duplicate posts in list')
	nodupes = []
	for post in lista:
		if not any(p.id == post.id for p in nodupes):
			nodupes.append(post)
	return nodupes


def main():
	lista = []
	if READ_FROM_FILE_IDS:
		scanfile()
	else:
		lista = scansub()
		lista = removeduplicates(lista)

	writefiles(lista)

main()
quit()