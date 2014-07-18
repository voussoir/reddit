#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subs, use "sub1+sub2+sub3+...". For all use "all"

HEADER = "**More posts from /u/_username_:**\n\n"
#This will be at the top of the Other Posts comment. This formatting will prepare the box.
#_username_ will be replaced by the OP's username
FOOTER = "\n\n^(This is a bot, go to /r/subreddit for more information)"
#This will be at the bottom of the Other Posts comment.

IGNORESELF = False
IGNORELINK = True
IGNOREMODS = False
#Will the bot ignore selfposts or linkposts or posts made by moderators? 
#Use True or False (Use Capitals! No quotations!)

IGNOREFLAGS = ['[meta]', '[modpost]']
#If the title of the post contains any of these flags, ignore it
#Useful for moderator posts, meta posts, or updates.

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


def scanSub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    moderators = subreddit.get_moderators()
    mods = []
    for moderator in moderators:
        mods.append(moderator.name)
    posts = subreddit.get_new(limit=MAXPOSTS)
    for post in posts:
        final = ''
        pid = post.id
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if not cur.fetchone():
            print(pid)
            try:
                pauthor = post.author.name
                ptitle = post.title
                if (post.is_self == True and IGNORESELF == False) or (post.is_self == False and IGNORELINK == False):
                    if pauthor not in mods or IGNOREMODS == False:
                        if all(flag.lower() not in ptitle.lower() for flag in IGNOREFLAGS):
                            result = []
                            ilist = []
                            print('\tBeginning search on /u/' + pauthor)
                            search = r.search('author:"' + pauthor + '"', subreddit=SUBREDDIT, sort='new', limit=1000)
                            for item in search:
                                if item.id != pid and all(flag.lower() not in item.title.lower() for flag in IGNOREFLAGS) and item.id not in ilist:
                                    if (item.is_self == True and IGNORESELF == False) or (item.is_self == False and IGNORELINK == False):
                                        print('\tResult: ' + item.id)
                                        ilist.append(item.id)
                                        result.append('- [' + item.title + '](' + item.short_link + ')')
                            print('\tCompleted Searching. ' + str(len(result)) + ' results.')
                            if len(result) > 0:
                                print('\tWriting comment')
                                final = HEADER.replace('_username_',pauthor) + '\n\n'.join(result) + FOOTER
                                post.add_comment(final)
                        else:
                            print('\tIgnoring Flag')
                    else:
                        print('\tIgnoring Moderator')
                else:
                    print('\tIgnoring Post type.')
            except AttributeError:
                print('\tAuthor is deleted. Ignoring.')
        cur.execute('INSERT INTO oldposts VALUES(?)',[pid])
        
        
    sql.commit()



while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', str(e))
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)
 