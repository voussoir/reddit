# /u/GoldenSights
import praw
#import sqlite3
import time
import traceback

''' USER CONFIG '''
USERAGENT = ""
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/

WAIT = 60
# The number of seconds between each cycle. The bot is completely inactive during this time.
''' All done! '''

try:
    import bot
    USERAGENT = bot.aG
    APP_ID = bot.oG_id
    APP_SECRET = bot.oG_secret
    APP_URI = bot.oG_uri
    APP_REFRESH = bot.oG_scopes['all']
except ImportError:
    pass

#sql = sqlite3.connect('filename.db')
#cur = sql.cursor()
#cur.execute('CREATE TABLE IF NOT EXISTS tablename(column TEXT)')
#cur.execute('CREATE INDEX IF NOT EXISTS indexname ON tablename(column)')
p
rint('Logging in.')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)


def main():
    pass


while True:
    try:
        main()
    except Exception as e:
        traceback.print_exc()
    print('Running again in %d seconds\n' % WAIT)
    time.sleep(WAIT)