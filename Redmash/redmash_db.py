#/u/GoldenSights
import traceback
import sys
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

READ_FROM_FILE = ""
PRINTFILE = ""
SCORETHRESH = 0
HTMLMODE = False
USERMODE = False
BREAKDOWNMODE = False
EXTENSION = '.txt'
# Variables are input by user during the
# inputvars() method
'''All done!'''


class Post:
	#Generic class to convert SQL columns into an object
	pass
sql = None
cur = None
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
def createpost(postdata):
	post = Post()
	post.id = postdata[1]
	if 't3_' in post.id or 't1_' in post.id:
		post.fullname = post.id
		post.id = post.id.split('_')[1]
	else:
		post.fullname = 't3_' + post.id
	post.type = int(post.fullname.split('_')[0][-1])
	post.created_utc = postdata[2]
	post.is_self = postdata[3]
	post.over_18 = postdata[4]
	post.author = postdata[5]
	post.title = postdata[6]
	post.title = post.title.replace('\n', '')
	post.url = postdata[7]
	post.selftext = postdata[8]
	post.score = postdata[9]
	post.subreddit = postdata[10]
	post.distinguished = postdata[11]
	post.textlen = postdata[12]
	post.num_comments = postdata[13]
	post.link_flair_text = postdata[14]
	post.link_flair_css_class = postdata[15]

	post.short_link = 'http://redd.it/' + post.id
	
	return post

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

def work(listfile):
	if HEADER != '':
		print(HEADER, file=listfile)
	previous_timestamp = ''
	while True:
		post = cur.fetchone()
		if post is None:
			break

		post = createpost(post)
		if post.score < SCORETHRESH:
			continue
		if post.type != 3:
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

def writefiles():
	print('Writing time files')
	listfile = preparefile('_date')
	cur.execute('SELECT * FROM posts WHERE score >= ? ORDER BY created DESC', [SCORETHRESH])
	work(listfile)
	closefile(listfile)
	
	print('Writing title files')
	listfile = preparefile('_title')
	cur.execute('SELECT * FROM posts WHERE score >= ? ORDER BY title ASC', [SCORETHRESH])
	work(listfile)
	closefile(listfile)

	print('Writing score files')
	listfile = preparefile('_score')
	cur.execute('SELECT * FROM posts WHERE score >= ? ORDER BY score DESC', [SCORETHRESH])
	work(listfile)
	closefile(listfile)
	
	if USERMODE is False:
		print('Writing author files')
		listfile = preparefile('_author')
		cur.execute('SELECT * FROM posts WHERE score >= ? ORDER BY author ASC', [SCORETHRESH])
		work(listfile)
		closefile(listfile)

	if USERMODE is True:
		print('Writing subreddit files')
		listfile = preparefile('_subreddit')
		cur.execute('SELECT * FROM posts WHERE score >= ? ORDER BY subreddit ASC', [SCORETHRESH])
		work(listfile)
		closefile(listfile)
	
	print('Writing flair file')
	listfile = preparefile('_flair')
	cur.execute('SELECT * FROM posts WHERE score >= ? AND flair_text IS NOT NULL ORDER BY flair_text, created ASC', [SCORETHRESH])
	work(listfile)
	cur.execute('SELECT * FROM posts WHERE score >= ? AND flair_text IS NULL ORDER BY flair_text, created ASC', [SCORETHRESH])
	work(listfile)
	closefile(listfile)

	print('Done.')

def breakdown(doreturn=False, mode='user'):
	print('\nBreaking it down...')
	listfile = preparefile('')
	if mode == 'subreddit':
		cur.execute('SELECT * FROM posts WHERE score >= ? ORDER BY author ASC', [SCORETHRESH])
	if mode == 'user':
		cur.execute('SELECT * FROM posts WHERE score >= ? ORDER BY subreddit ASC', [SCORETHRESH])
	count_submissions = 0
	count_comments = 0
	previous = ''
	breakdowndict = {}
	while True:
		post = cur.fetchone()
		if post is None:
			breakdowndict[previous] = {'submissions':count_submissions, 'comments':count_comments}
			break
		post = createpost(post)
		if mode == 'subreddit':
			relevant = post.author
		elif mode == 'user':
			relevant = post.subreddit
		if relevant != previous:
			breakdowndict[previous] = {'submissions':count_submissions, 'comments':count_comments}
			previous = relevant
			count_submissions = 0
			count_comments = 0

		if post.type == 1:
			count_comments += 1
		if post.type == 3:
			count_submissions += 1

	del breakdowndict['']

	if doreturn is True:
		return breakdowndict

	keys = list(breakdowndict.keys())
	longestkey = max([len(k) for k in keys])
	keys.sort(key=lambda x: (breakdowndict[x]['submissions'] + breakdowndict[x]['comments'], x), reverse=True)
	out = []
	for k in keys:
		relevant = (' '*(longestkey-len(k))) + ('"%s"' % k)
		submissions = breakdowndict[k]['submissions']
		comments = breakdowndict[k]['comments']
		o = '%s:{%s:%d, %s:%d}' % (relevant, '"submissions"', submissions, '"comments"', comments)
		out.append(o)
	out = ',\n'.join(out)
	out = '{\n' + out + '\n}'
	print(out, file=listfile)
	#json.dump(breakdowndict, listfile, sort_keys=True, indent=4)


def inputvars():
	global READ_FROM_FILE
	global PRINTFILE
	global SCORETHRESH
	global HTMLMODE
	global USERMODE
	global BREAKDOWNMODE
	global EXTENSION
	global sql
	global cur

	try:
		READ_FROM_FILE = sys.argv[1]
	except IndexError:
		READ_FROM_FILE = input('] Input database = ')

	if READ_FROM_FILE[-3:] != '.db':
		READ_FROM_FILE += '.db'
	filename = READ_FROM_FILE.replace('\\', '/')
	filename = filename.split('/')[-1]
	if filename[0] == '@':
		USERMODE = True

	try:
		PRINTFILE = sys.argv[2]
	except IndexError:
		PRINTFILE = input('] Output filename = ')

	try:
		SCORETHRESH = int(sys.argv[3])
	except IndexError:
		SCORETHRESH = int(input('] Score threshold = '))
	
	HTMLMODE = '.html' in PRINTFILE
	BREAKDOWNMODE = '.json' in PRINTFILE
	if HTMLMODE:
		EXTENSION = '.html'
		PRINTFILE = PRINTFILE.replace('.html', '')
	elif BREAKDOWNMODE:
		EXTENSION = '.json'
		PRINTFILE = PRINTFILE.replace('.json', '')
	else:
		EXTENSION = '.txt'
		PRINTFILE = PRINTFILE.replace('.txt', '')

	sql = sqlite3.connect(READ_FROM_FILE)
	cur = sql.cursor()

def main():
	inputvars()
	if BREAKDOWNMODE is False:
		writefiles()
	else:
		if USERMODE is True:
			breakdown(mode='user')
		else:
			breakdown(mode='subreddit')


if __name__ == '__main__':
	main()