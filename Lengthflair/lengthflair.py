#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import datetime

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
MAXPOSTS = 2
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

LENGTHS = {100:'Flash Fiction', 200:'Short Fiction', 300:'Extended Fiction'}
#The body of the post is compared to this dictionary
#The function lengthflair() will assign the earliest possible member. If the body exceeds the dictionary, the longest available value is assigned
#100:'short' means that 0-100 characters is "short"; 101 - 200 is "medium"

USECSS = False
FLAIRCSS = {'Flash Fiction':'flashfiction', 'Short Fiction':'shortfiction', 'Extended Fiction':'extendedfiction'}
#Does your subreddit have css classes tied to the link flairs? Use True or False (Use Capitals! No quotations!)
#If True, assign each flair-text to its corresponding flair-css here. This is Case-Sensitive!
#If False, ignore this dictionary

IGNOREMODS = False
#Should the bot ignore posts made by moderators? Use True or False (Use Capitals! No quotations!)
DELAY = 180
#The bot will not flair a post if it is younger than this many seconds
#Give the user a chance to flair it himself.


'''All done!'''




WAITS = str(WAIT)
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
print('Loaded Completed table')

sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)


def lengthflair(string):
    l = len(string)
    keys = sorted(list(LENGTHS.keys()))
    for member in keys:
        if l <= member:
            f = LENGTHS[member]
            return f
    return LENGTHS[keys[-1]]

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
    moderators = subreddit.get_moderators()
    mods = []
    for moderator in moderators:
        mods.append(moderator.name)

    posts = subreddit.get_new(limit=MAXPOSTS)
    for post in posts:
        pid = post.id
        try:
            pauthor = post.author.name
        except AttributeError:
            pauthor = '[DELETED]'

        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if not cur.fetchone():
            pbody = post.selftext.lower()
            ptime = post.created_utc
            curtime = getTime(True)
            tdiff = curtime - ptime
            if pauthor not in mods or IGNOREMODS == False:
                if tdiff > DELAY:
                    pflair = post.link_flair_text
                    if pflair == '' or pflair == None:
                        newflair = lengthflair(pbody)
                        if USECSS == True:
                            try:
                                newcss = FLAIRCSS[newflair]
                            except KeyError:
                                print('Error: CSS class for flair ' + newflair + ' could not be found')
                                newcss = ''
                        else:
                            newcss = ''
                        print(pid + ': Setting flair: ' + newflair)
                        post.set_flair(flair_text=newflair, flair_css_class=newcss)

                    else:
                        print(pid + ': Already has flair: ' + pflair)
                    cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
                else:
                    print(pid + ': Waiting for user to flair his post.', "%0d" % (DELAY-tdiff), 'seconds.')
            else:
                print(pid + ': Ignoring Moderator')

    sql.commit()


while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', e)
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)