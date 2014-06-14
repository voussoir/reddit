#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import string

''''USER CONFIGURATION'''
USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
NORMALSTRING = ": [Submissions](http://reddit.com/u/_username_/submitted) | [Comments](http://reddit.com/u/_username_/comments)"
#This is the remark that every user gets. _username_ will be replaced by the username automatically
SPECIALS = ["GoldenSights", "duckvimes_"]
#This is the list of Special Users
SPECIALSTRING = [" | [Author!](http://reddit.com/u/_username_/gilded)", " | [Moderator!](http://reddit.com/u/_username_/gilded)"]
#This is the extra remark that Special Users get. _username_ will be replaced by the username automatically
DEADUSER = ": [Dead User](http://reddit.com/u/_username_/submitted)"
#This is the remark for accounts which are invalid or shadowbanned. _username_ will be replaced by the username automatically
HEADER = "These users have been mentioned:\n\n#####&#009;\n\n######&#009;\n\n####&#009;\n\n"
#This will be at the very top of the comment. \n\n creates a new line. Set this to "" if you don't want anything.
FOOTER = "\n\n*This was done by a bot. Contact the moderators or [author](http://reddit.com/u/GoldenSights) if there is a problem.*"
#This will be at the very bottom of the comment. Set to "" if you don't want anything.
DISTINGUISHCOMMENT = True
#If your bot is a moderator, you can distinguish the comment. Use True or False (Use capitals! No quotations!)
TRIGGERSTRING = '/u/'
#This is the thing in the title you're looking for.
MAXPOSTS = 15
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
BREAKPOINTS = ["'"]
#This is a list of characters which will halt the username creation. Breakpoints.


'''All done!'''



CHARS = string.digits + string.ascii_letters + '-_'
#This is the list of characters which are allowed in usernames. Don't change this.

try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getuG()
    PASSWORD = bot.getpG()
    USERAGENT = bot.getaG()
except ImportError:
    pass
WAITS = str(WAIT)
sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded Completed table')


sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

def breakpoint(word):
    newword = ''
    for c in word:
        if c in CHARS:
            newword += c
        if c in BREAKPOINTS:
            break
    return newword

def scanSub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_new(limit=MAXPOSTS)
    for post in posts:
        ptitle = post.title
        try:
            pauthor = post.author.name
        except AttributeError:
            pauthor = '[DELETED]'
        pid = post.id
        cur.execute('SELECT * FROM oldposts WHERE ID="%s"' % pid)
        if not cur.fetchone():
            cur.execute('INSERT INTO oldposts VALUES("%s")' % pid)
            print(pid)
            result = []
            if TRIGGERSTRING in ptitle:
                ptitlesplit = ptitle.split(' ')
                for word in ptitlesplit:
                    if TRIGGERSTRING in word:
                        print(word)
                        word = word.replace(TRIGGERSTRING, '')
                        word = breakpoint(word)
                        finalword = TRIGGERSTRING + word
                        try:
                            user = r.get_redditor(word, fetch=True)
                            finalword = finalword.replace(word, user.name)
                            finalword += NORMALSTRING.replace('_username_', word)
                        except Exception:
                            finalword += DEADUSER.replace('_username_', word)
                            print('\tDead')

                        for m in range(len(SPECIALS)):
                            name = SPECIALS[m]
                            if name.lower() == word.lower():
                                print('\tSpecial')
                                finalword += SPECIALSTRING[m].replace('_username_', word)

                        result.append(finalword)
            if len(result) > 0:
                final = HEADER + '\n\n'.join(result) + FOOTER
                print('Creating comment.')
                newcomment = post.add_comment(final)
                if DISTINGUISHCOMMENT == True:
                    print('Distinguishing Comment.')
                    newcomment.distinguish()
            else:
                print('\tNone!')
        sql.commit()


while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', str(e))
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)