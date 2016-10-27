#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import datetime
import sqlite3

'''USER CONFIGURATION'''

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "NSALeaksbot"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subs, use "sub1+sub2+sub3+...". For all use "all"
KEYWORDS = ["snowden", "greenwald", "nsa"]
#Any comment containing these words will be saved.
KEYDOMAINS = []

SUBDUMP = True
#Do you want the bot to dump into a subreddit as posts? Use True or False (Use capitals! No quotations!)
DSUB = "GoldTesting"
#If SUBDUMP is set to True, you will need to choose a subreddit to submit to.
ALLOWSELF = False
#Do you want the bot to dump selfposts? Use True or False (Use capitals! No quotations!)
DISTINGUISHPOST = False
#Do you want the bot to mod-distinguish the post?
DISTINGUISHCOMMENT = False
#Do you want the bot to mod-distinguish the comment on the dump?
TITLE = "_subreddit_: _ptitle_"
#This is the title of the submission to your dump
#Leave blank to keep the original post's title
#Otherwise, use these injectors to create dynamic title:
#_subreddit_ = subreddit of original post
#_author_ = OP of original post
#_ptitle_ = Title of original post

NSUB = "GoldTesting"
#This is the subreddit that will undergo the Other Discussions test.
DELAY = 10
#How many SECONDS old must a post be on your sub before it receives an Other Discussion box?
DISTINGUISHN = False
#Do you want the bot to mod-distinguish the comment?
HEADER = "**Other Discussions on reddit:**\n\nSubreddit | Author | Post | Comments | Time\n:- | - | - | - | -:\n"
#This will be at the top of the Other Discussions comment. This formatting will prepare the box.


MAXPOSTS = 1
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

EDITPASTMAX = 172800
#How far back do you want to go when editing posts, in seconds?
#A value of 172800 will only edit comments that are less than 2 days old


'''All done!'''




WAITS = str(WAIT)
try:
    import bot
    USERAGENT = bot.aG
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS oldpost_index ON oldposts(id)')
cur.execute('CREATE TABLE IF NOT EXISTS oldlinks(ID TEXT)')
print('Loaded Completed table')

sql.commit()

print('Logging in')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)


def getTime(bool):
    timeNow = datetime.datetime.now(datetime.timezone.utc)
    timeUnix = timeNow.timestamp()
    if bool is False:
        return timeNow
    else:
        return timeUnix

def scanSub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_new(limit=MAXPOSTS)
    for post in posts:
        pid = post.id
        plink = post.permalink
        if not post.is_self or ALLOWSELF is True:
            ptitle = post.title
            purl = post.url
            cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
            if not cur.fetchone():
                cur.execute('SELECT * FROM oldlinks WHERE ID=?', [purl])
                if not cur.fetchone():
                    if (KEYWORDS == [] or any(key.lower() in ptitle.lower() for key in KEYWORDS)) and (KEYDOMAINS == [] or any(key.lower() in purl.lower() for key in KEYDOMAINS)):
                        try:
                            pauthor = post.author.name
                            psub = post.subreddit.display_name
                            print(pid + ', ' + pauthor)
                            if TITLE == "":
                                newtitle = ptitle
                            else:
                                newtitle = TITLE
                                newtitle = newtitle.replace('_ptitle_', ptitle)
                                newtitle = newtitle.replace('_author_', pauthor)
                                newtitle = newtitle.replace('_subreddit_', psub)

                            if len(newtitle) > 300:
                                newtitle = newtitle[:297] + '...'

                            if SUBDUMP is True:
                                print('\tDumping to ' + DSUB)
                                try:
                                    create = r.submit(DSUB, newtitle, url=purl, captcha = None)
                                except praw.errors.AlreadySubmitted:
                                    print('Error: Already Submitted. Skipping...')
                                print('\tCreated post ' + create.id)
                                if DISTINGUISHPOST is True:
                                    print('\tDistinguishing post')
                                    create.distinguish()
                        except AttributeError:
                            print(pid + ': Author deleted. Ignoring')
                    cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
                    cur.execute('INSERT INTO oldlinks VALUES(?)', [purl])
                else:
                    print(pid + ': Already linked somewhere else')  
        else:
            print(pid + ': Ignoring selfpost')
            cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
        
        sql.commit()

def discussions():
    print('\nScanning ' + NSUB)
    subreddit = r.get_subreddit(NSUB)
    posts = subreddit.get_new(limit=MAXPOSTS)
    for post in posts:
        result = []
        pid = post.id
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if not cur.fetchone():
            ptime = post.created_utc
            curtime = getTime(True)
            if curtime - ptime > DELAY:
                generatebox(post, result)
                if len(result) > 0:
                    final = HEADER + '\n'.join(result)
                    if len(final) < 10000:
                        print('\tCreating comment')
                        post.add_comment(final)
                        cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
                else:
                    print('\tNo results!')
                if post.is_self:
                    cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
            else:
                print(pid + ': Too young')
        sql.commit()

def editpast():
    print('\nUpdating previous comments')
    user = r.user
    comments = user.get_comments(limit=MAXPOSTS)
    for comment in comments:
        result = []
        ctime = comment.created_utc
        curtime = getTime(True)
        if curtime - ctime > EDITPASTMAX:
            print('\tReached end')
            break
        else:
            print(comment.id)
            post = comment.submission
            generatebox(post, result)
            if len(result) > 0:
                final = HEADER + '\n'.join(result)
                if len(final) < 10000:
                    if final != comment.body:
                        print('\tUpdating')
                        comment.edit(final)
                    else:
                        print('\tDoes not need updating')
            else:
                print('\tNone!')


def generatebox(post, result):
    purl = post.url
    print(post.id + ': Trying OD box')
    search = r.search('url:"' + purl + '"', sort='new', limit=None)
    for item in search:
        if item.id != post.id:
            timestamp = item.created_utc
            timestamp = datetime.datetime.utcfromtimestamp(int(timestamp)).strftime("%A %B %d, %Y %H:%M UTC")
            try:
                iauthor = '/u/' + item.author.name
            except AttributeError:
                pauthor = '[deleted]'
            subreddit = '/r/' + item.subreddit.display_name
            ilink = item.permalink
            ilink = ilink.replace('http://www', 'http://np')
            result.append(subreddit + ' | ' + iauthor + ' | [post](' + ilink + ') | ' + str(item.num_comments) + ' | ' + timestamp)





while True:
    try:
        scanSub()
        discussions()
        editpast()
    except Exception as e:
        print('An error has occured:', str(e))
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)
 