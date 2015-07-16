#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time

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
MAXPOSTS = 1000
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 60
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''


WAITS = str(WAIT)
try:
    import bot
    USERAGENT = bot.aG
except ImportError:
    pass

print("Logging in")
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def scanSub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_new(limit=MAXPOSTS)
    for post in posts:
        try:
            pauthor = post.author.name
        except AttributeError:
            print(post.id, 'is being removed')
            post.remove()
            print('\tDone')

while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', e)
    print('Running again in ' + WAITS + ' seconds \n')
    time.sleep(WAIT)