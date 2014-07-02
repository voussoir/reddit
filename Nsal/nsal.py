#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import datetime
import sqlite3

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "Test"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subs, use "sub1+sub2+sub3+...". For all use "all"
KEYWORDS = ["snowden", "greenwald", "nsa"]
#Any comment containing these words will be saved.
KEYDOMAINS = ["theguardian.com", "techdirt.com"]

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
HEADER = "**Other Discussions on reddit:**\n\nSubreddit | Author | Post | Time\n:- | - | - | -:\n"
#This will be at the top of the Other Discussions comment. This formatting will prepare the box.


MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


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

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS oldlinks(ID TEXT)')
print('Loaded Completed table')

sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 


def getTime(bool):
    timeNow = datetime.datetime.now(datetime.timezone.utc)
    timeUnix = timeNow.timestamp()
    if bool == False:
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
        if not post.is_self or ALLOWSELF == True:
            ptitle = post.title
            purl = post.url
            cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
            if not cur.fetchone():
                cur.execute('SELECT * FROM oldlinks WHERE ID=?', [purl])
                if not cur.fetchone():
                    if any(key.lower() in ptitle.lower() for key in KEYWORDS) and any(key.lower() in purl.lower() for key in KEYDOMAINS):
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

                            if SUBDUMP == True:
                                print('\tDumping to ' + DSUB)
                                try:
                                    create = r.submit(DSUB, newtitle, url=purl, captcha = None)
                                except praw.errors.AlreadySubmitted:
                                    print('Error: Already Submitted. Skipping...')
                                print('\tCreated post ' + create.id)
                                if DISTINGUISHPOST == True:
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
                purl = post.url
                print(pid + ': Trying OD box')
                search = r.search('url:"' + purl + '"', sort='new')
                for item in search:
                    if item.id != pid:
                        timestamp = item.created_utc
                        timestamp = datetime.datetime.fromtimestamp(int(timestamp)).strftime("%A %B %d, %Y %H:%M UTC")
                        try:
                            iauthor = '/u/' + item.author.name
                        except AttributeError:
                            pauthor = '[deleted]'
                        subreddit = '/r/' + item.subreddit.display_name
                        ilink = item.permalink
                        ilink = ilink.replace('http://www', 'http://np')
                        result.append(subreddit + ' | ' + iauthor + ' | [post](' + ilink + ') | ' + timestamp)
                if len(result) > 0:
                    final = HEADER + '\n'.join(result)
                    if len(final) < 10000:
                        print('\tCreating comment')
                        post.add_comment(final)
                else:
                    print('\tNo results!')
                cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
            else:
                print(pid + ': Too young')




while True:
    try:
        scanSub()
        discussions()
    except Exception as e:
        print('An error has occured:', str(e))
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)
 