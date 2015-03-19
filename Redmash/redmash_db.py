#/u/GoldenSights
import traceback
import time
import datetime
import string
import sqlite3

'''USER CONFIGURATION'''

#TIMESTAMP = '%A %d %B %Y'
TIMESTAMP = '%a %d %b %Y'
#The time format.
#  "%A %d %B %Y" = "Wendesday 04 June 2014"
#http://docs.python.org/2/library/time.html#time.strftime

HEADER = ""
#Put this at the top of the .txt file


FORMAT = "_timestamp_: [_title_](_slink_) - /u/_author_ (+_score_)"
FORMAT_HTML = "_timestamp_: <a href=\"_shortlink_\">[_flairtext_] _title_</a> - <a href=\"_authorlink_\">_author_</a> (+_score_)<br>"
HTMLHEADER = '<html style="font-family:Consolas;font-size:10pt;">'
TSFORMAT = ""
#USE THESE INJECTORS TO CREATE CUSTOM OUTPUT
#_timestamp_ which follows the TIMESTAMP format
#_title_
#_url_
#_subreddit_
#_shortlink_
#_author_
#_authorlink_
#_numcomments_
#_score_
#_flairtext_
#_flaircss_

READ_FROM_FILE = input('] Input database = ')
if READ_FROM_FILE[-3:] != '.db':
	READ_FROM_FILE += '.db'
PRINTFILE = input('] Output filename = ')
SCORETHRESH = int(input('] Score threshold = '))

HTMLMODE = '.html' in PRINTFILE
if HTMLMODE:
	EXTENSION = '.html'
	PRINTFILE = PRINTFILE.replace('.html', '')
else:
	EXTENSION = '.txt'

'''All done!'''

sql = sqlite3.connect(READ_FROM_FILE)
cur = sql.cursor()
    #  0 - idint
    #  1 - idstr
    #  2 - created
    #  3 - self
    #  4 - nsfw
    #  5 - author
    #  6 - title
    #  7 - url
    #  8 - selftext
    #  9 - score
    # 10 - subreddit
    # 11 - distinguished
    # 12 - textlen
    # 13 - num_comments
    # 14 - flair_text
    # 15 - flair_css_class
def createpost(post):
	p = Post()
	p.id = post[1]
	p.created_utc = post[2]
	p.is_self = post[3]
	p.over_18 = post[4]
	p.author = post[5]
	p.title = post[6]
	p.title = p.title.replace('\n', '')
	p.url = post[7]
	p.selftext = post[8]
	p.score = post[9]
	p.subreddit = post[10]
	p.distinguished = post[11]
	p.textlen = post[12]
	p.num_comments = post[13]
	p.link_flair_text = post[14]
	p.link_flair_css_class = post[15]

	p.short_link = 'http://redd.it/' + p.id
	
	return p


def work(listfile):
	if HEADER != "":
		print(HEADER, file=listfile)
	previous_timestamp = ""
	while True:
		post = cur.fetchone()
		if post is None:
			break

		post = createpost(post)
		if post.score < SCORETHRESH:
			continue
		timestamp = post.created_utc
		timestamp = datetime.datetime.fromtimestamp(int(timestamp)).strftime(TIMESTAMP)
		if HTMLMODE:
			final = FORMAT_HTML
		else:
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
		authorlink = 'http://reddit.com/u/' + post.author
		final = final.replace('_author_', post.author)
		final = final.replace('_authorlink_', authorlink)
		final = final.replace('_subreddit_', post.subreddit)
		url = post.url
		url = url.replace('http://www.reddit.com', 'http://np.reddit.com')
		final = final.replace('_url_', url)
		shortlink = post.short_link
		#slink = slink.replace('http://', 'http://np.')
		final = final.replace('_slink_', shortlink)
		final = final.replace('_flairtext_', flair_text)
		final = final.replace('_score_', str(post.score))
		final = final.replace('_numcomments_', str(post.num_comments))
		print(final, file=listfile)
		previous_timestamp = timestamp


def preparefile(filesuffix):
	filesuffix += EXTENSION
	listfile = open(PRINTFILE + filesuffix, 'w', encoding='utf-8')
	if HTMLMODE is True:
		print(HTMLHEADER, file=listfile)
	return listfile

def closefile(listfile):
	if HTMLMODE is True:
		print('</html>', file=listfile)
	listfile.close()


def writefiles():

	print('Writing time files')
	listfile = preparefile('_date')
	cur.execute('SELECT * FROM posts WHERE score > ? ORDER BY created DESC', [SCORETHRESH])
	work(listfile)
	closefile(listfile)
	
	print('Writing title files')
	listfile = preparefile('_title')
	cur.execute('SELECT * FROM posts WHERE score > ? ORDER BY title ASC', [SCORETHRESH])
	work(listfile)
	closefile(listfile)

	print('Writing score files')
	listfile = preparefile('_score')
	cur.execute('SELECT * FROM posts WHERE score > ? ORDER BY score DESC', [SCORETHRESH])
	work(listfile)
	closefile(listfile)
	
	print('Writing author files')
	listfile = preparefile('_author')
	cur.execute('SELECT * FROM posts WHERE score > ? ORDER BY author ASC', [SCORETHRESH])
	work(listfile)
	closefile(listfile)
	
	print('Writing flair file')
	listfile = preparefile('_flair')
	cur.execute('SELECT * FROM posts WHERE score > ? AND flair_text IS NOT NULL ORDER BY flair_text, created ASC', [SCORETHRESH])
	work(listfile)
	cur.execute('SELECT * FROM posts WHERE score > ? AND flair_text IS NULL ORDER BY flair_text, created ASC', [SCORETHRESH])
	work(listfile)
	closefile(listfile)

	print('Done.')

def removeduplicates(lista):
	print('Removing duplicate posts in list')
	nodupes = []
	for post in lista:
		if not any(p.id == post.id for p in nodupes):
			nodupes.append(post)
	return nodupes


def main():
	writefiles()


class Post:
	#Generic class to convert SQL columns into an object
	pass

main()
quit()