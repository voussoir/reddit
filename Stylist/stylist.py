#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import datetime

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

TIMES = {'00:00':'Midnight.txt', '06:00':'Day.txt', '18:00':'Night.txt'}
#Times and their corresponding stylesheet
#Times are in UTC timezone!!
#http://www.timeanddate.com/time/map/
#Times must be written as HH:MM, zero-padded, in 24h style

WAIT = 60
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''


WAITS = str(WAIT)
try:
    import bot
    USERAGENT = bot.aG
except ImportError:
    pass

def crash(errmessage):
    print('\n' + errmessage)
    try:
        input()
    except EOFError:
        pass
    quit()

def preparemod(idict):
    print('Preparing Minute-of-Day format')
    mod = {}
    for key in idict:
        print(key, end='')
        if len(key) == 5 and key[2] == ':':
            keysplit = key.split(':')
            try:
                hh = int(keysplit[0])
                mm = int(keysplit[1])
                newkey = 0
                if 0 <= hh <= 23:
                    newkey += (60 * hh)
                else:
                    crash('Error: Hour must be between 0 and 23')
                if 0 <=  mm <= 59:
                    newkey += (mm)
                else:
                    crash('Error: Minute must be between 0 and 59')
                mod[newkey] = idict[key]
                print(' >>',newkey, idict[key])
            except ValueError:
                crash('Error: Time contains non-numbers')
        else:
            crash('Error: Incorrect time form. Must be HH:MM in 24h mode')
    return mod

def choosetime(idict):
    print('Choosing style')
    ikeys = list(idict.keys())
    ikeys.sort()
    now = datetime.datetime.utcnow()
    now = datetime.datetime.strftime(now, '%H:%M')
    print(now, end='')
    now = now.split(':')
    now = (60 * int(now[0])) + (int(now[1]))
    for m in range(len(ikeys)):
        key = ikeys[m]
        try:
            if now >= key and now < ikeys[m+1]:
                choice = idict[key]
                break
        except IndexError:
            choice = idict[key]
    print(' >>', choice)
    return choice


def stylize():
    global previousstyle
    chosen = choosetime(MOD)
    subreddit = r.get_subreddit(SUBREDDIT, fetch=True)
    if previousstyle != chosen:
        print('Setting ' + SUBREDDIT + ' stylesheet to ' + chosen)
        try:
            chosenfile = open(chosen, 'r')
        except FileNotFoundError:
            crash('Could not find file ' + chosen)
        chosendata = chosenfile.read()
        chosenfile.close()

        try:
            subreddit.set_stylesheet(chosendata)
            print('Success')
            previousstyle = chosen
        except praw.errors.ModeratorOrScopeRequired:
            crash('Must be logged in as a moderator of ' + SUBREDDIT)
        except:
            crash('Some error during stylesheet set')
    else:
        print('Style already set.')


MOD = preparemod(TIMES)
print()
previousstyle = None

print('Logging in')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)


while True:
    try:
        stylize()
    except Exception as e:
        print('An error has occured:', e)
    print('Running again in ' + WAITS + ' seconds \n')
    time.sleep(WAIT)