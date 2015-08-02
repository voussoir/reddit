import praw
import sys
import time
import traceback

USERAGENT = ""
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/

try:
    import bot
    USERAGENT = bot.aG
    APP_ID = bot.oG_id
    APP_SECRET = bot.oG_secret
    APP_URI = bot.oG_uri
    APP_REFRESH = bot.oG_scopes['all']
except ImportError:
    pass

print('logging in')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def submissionscoretracker(submissionid):
    if '_' not in submissionid:
        submissionid = 't3_' + submissionid
    submission = r.get_info(thing_id=submissionid)
    
    outfile = open(submission.fullname + '.txt', 'a+')
    last_refresh = time.time()
    while True:
        try:
            if time.time() - last_refresh:
                r.refresh_access_information()
                last_refresh = time.time()
            submission.refresh()
            print('%s, %d' % (time.strftime('%H:%M:%S'), submission.score))
            outfile.write('%d, %d\n' % (int(time.time()), submission.score))
            outfile.flush()
        except KeyboardInterrupt:
            outfile.close()
            return
        except:
            traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        submissionid = input('id: ')
    else:
        submissionid = sys.argv[1]
    submissionscoretracker(submissionid)