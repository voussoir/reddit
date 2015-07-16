#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3

'''USER CONFIGURATION'''

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
RESPONSE = "I have detected some mobile links in your comment. Here are the non-mobile clickables:\n\n"
#This is what the bot says right before all the fixed links
MOBILES = {"http://m.":"http://", "http://en.m.":"http://en.", "http://i.reddit.":"http://reddit.", "http://mobile.":"http://"}
#These are the different forms of mobile links. To handle each one, scroll down to line 70.
MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

DOMAINBLACKLIST = ["imgur"]
#These are domains that you do not want to demobile, ever.

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
print('Loaded Completed table')

sql.commit()

r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def scanSub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_comments(limit=MAXPOSTS)
    for post in posts:
        corrections = []
        pid = post.id
        try:
            pauthor = post.author.name
        except AttributeError:
            pauthor = '[DELETED]'
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if not cur.fetchone():
            cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
            pbody = post.body
            pbodysplit = pbody.split()
            for word in pbodysplit:
                if any(mobile in word for mobile in MOBILES):
                    print(pid)
                    if all(domain not in word for domain in DOMAINBLACKLIST):
                        if '](' in word:
                            word = word[word.index('(')+1:]
                            word = word.replace(')','')

                        for item in MOBILES:
                            word = word.replace(item, MOBILES[item])
                            
                        corrections.append(word)

                    else:
                        print('\tDomain is blacklisted.')
            if len(corrections) > 0:
                print('\t' + pid + ' by ' + pauthor + ': Fixed ' + str(len(corrections)) + ' links.')
                f = '\n\n'.join(corrections)
                post.reply(RESPONSE + f)


    sql.commit()


while True:
    scanSub()
    #try:
    #    scanSub()
    #except Exception as e:
    #    print('An error has occured:', e)
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)