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
#The subreddit you are acting on.
SUBJECTLINE = ['submission']
#If the modmail subject line contains one of these keywords, he will be added

MAXPOSTS = 100
#The number of modmails to collect at once. 100 can be fetched with a single request
WAIT = 30
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
'''All done!'''


sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded Users table')

sql.commit()

try:
    import bot
    USERAGENT = bot.aG
except ImportError:
    pass
WAITS = str(WAIT)

print('Logging in.')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def scanmessages():
    print('Getting ' + SUBREDDIT + ' modmail')
    subreddit = r.get_subreddit(SUBREDDIT)
    modmail = list(subreddit.get_mod_mail(limit=MAXPOSTS))
    for message in modmail:
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [message.fullname])
        if not cur.fetchone():
            print(message.fullname)
            try:
                mauthor = message.author.name
                msubject = message.subject.lower()
                if any(keyword.lower() in msubject for keyword in SUBJECTLINE):
                    print('\tApproving ' + mauthor)
                    subreddit.add_contributor(mauthor)
                    message.mark_as_read()
            except AttributeError:
                print('Failed to fetch username')
            cur.execute('INSERT INTO oldposts VALUES(?)', [message.fullname])
            sql.commit()



while True:
    try:
        scanmessages()
    except Exception as e:
        print('ERROR: ' + str(e))
    sql.commit()
    print('Running again in ' + WAITS + ' seconds \n_________\n')
    time.sleep(WAIT)
