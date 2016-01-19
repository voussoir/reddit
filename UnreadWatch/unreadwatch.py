import os
import praw
import time

''' User Config '''
USERAGENT = ""
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
''' All done '''

try:
    import bot
    USERAGENT = bot.aG
    APP_ID = bot.oG_id
    APP_SECRET = bot.oG_secret
    APP_URI = bot.oG_uri
    APP_REFRESH = bot.oG_scopes['all']
except ImportError:
    pass

r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)
last_refresh = time.time()

def clearscreen():
    if os.system('cls') != 0:
        os.system('clear')

def unreadwatch():
    r.handler.clear_cache()
    unread = list(r.get_unread(limit=None))
    now = time.strftime('%H:%M:%S')
    clearscreen()
    print(now, len(unread))
    for item in unread:
        print('\t%s: %s' % (item.author, item.subject))

while True:
    try:
        unreadwatch()
    except:
        traceback.print_exc()
    time.sleep(15)