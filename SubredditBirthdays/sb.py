#/u/GoldenSights
import datetime
import json
import os
import praw
import random
import string
import sqlite3
import subprocess
import sys
import time
import tkinter
import traceback
import types


'''USER CONFIGURATION'''
USERAGENT = '''
/u/GoldenSights SubredditBirthdays data collection:
Gathering the creation dates of subreddits for visualization.
More at https://github.com/voussoir/reddit/tree/master/SubredditBirthdays
'''.replace('\n', ' ')
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
# This is a short description of what the bot does.
# For example "/u/GoldenSights' Newsletter bot"

WAIT = 20
# This is how many seconds you will wait between cycles.
# The bot is completely inactive during this time.

LOWERBOUND_STR = '2qh0j'
LOWERBOUND_INT = 4594339

FORMAT_MEMBER = '{idstr:>5s}, {human}, {nsfw}, {name:<25s} {subscribers:>10,}'
FORMAT_MESSAGE_NEW = 'New: {idstr:>5s} : {human} : {nsfw} : {name} : {subscribers}'
FORMAT_MESSAGE_UPDATE = 'Upd: {idstr:>5s} : {human} : {nsfw} : {name} : {subscribers} ({subscriber_diff})'

RANKS_UP_TO = 20000
# For the files sorted by subscriber count, display ranks up to this many.

'''All done!'''

try:
    import bot
    #USERAGENT = bot.aG
    APP_ID = bot.oG_id
    APP_SECRET = bot.oG_secret
    APP_URI = bot.oG_uri
    APP_REFRESH = bot.oG_scopes['all']
except ImportError:
    pass


WAITS = str(WAIT)

GOODCHARS = string.ascii_letters + string.digits + '_'

sql = sqlite3.connect('C:/git/reddit/subredditbirthdays/sql.db')
cur = sql.cursor()
cur2 = sql.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS subreddits(
    idint INT,
    idstr TEXT,
    created INT,
    human TEXT,
    name TEXT,
    nsfw INT,
    subscribers INT,
    jumble INT,
    subreddit_type INT,
    submission_type INT)
    ''')
cur.execute('CREATE INDEX IF NOT EXISTS subindex ON subreddits(idint)')

cur.execute('''
    CREATE TABLE IF NOT EXISTS suspicious(
    idint INT,
    idstr TEXT,
    name TEXT,
    subscribers INT)
    ''')
sql.commit()

SQL_COLUMNCOUNT = 10

# These numbers are used for interpreting the tuples that come from SELECT
SQL_IDINT = 0
SQL_IDSTR = 1
SQL_CREATED = 2
SQL_HUMAN = 3
SQL_NAME = 4
SQL_NSFW = 5
SQL_SUBSCRIBERS = 6
SQL_JUMBLE = 7
SQL_SUBREDDIT_TYPE = 8
SQL_SUBMISSION_TYPE = 9

# These strings are used for binding columns during INSERT AND UPDATE
SQLS_IDINT = 'idint'
SQLS_IDSTR = 'idstr'
SQLS_CREATED = 'created'
SQLS_HUMAN = 'human'
SQLS_NAME = 'name'
SQLS_NSFW = 'nsfw'
SQLS_SUBSCRIBERS = 'subscribers'
SQLS_JUMBLE = 'jumble'
SQLS_SUBREDDIT_TYPE = 'subreddit_type'
SQLS_SUBMISSION_TYPE = 'submission_type'

print('Logging in.')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

noinfolist = []

monthnumbers = {
    "Jan":"01",
    "Feb":"02",
    "Mar":"03",
    "Apr":"04",
    "May":"05",
    "Jun":"06",
    "Jul":"07",
    "Aug":"08",
    "Sep":"09",
    "Oct":"10",
    "Nov":"11",
    "Dec":"12",
}

SUBREDDIT_TYPE = {
    'public':0,
    'restricted':1,
    'private':2,
    'archived':3,
    None:4,
    'employees_only':5,
    'gold_restricted':6,
    'gold_only':7,
}
SUBMISSION_TYPE = {
    'any':0,
    'link':1,
    'self':2,
    None:3,
}
SUBREDDIT_TYPE_REVERSE = {v:k for (k,v) in SUBREDDIT_TYPE.items()}
SUBMISSION_TYPE_REVERSE = {v:k for (k,v) in SUBMISSION_TYPE.items()}

SUBMISSION_OBJ = praw.objects.Submission
SUBREDDIT_OBJ = praw.objects.Subreddit
COMMENT_OBJ = praw.objects.Comment

def base36encode(number, alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    """Converts an integer to a base36 string."""
    if not isinstance(number, (int)):
        raise TypeError('number must be an integer')
    base36 = ''
    sign = ''
    if number < 0:
        sign = '-'
        number = -number
    if 0 <= number < len(alphabet):
        return sign + alphabet[number]
    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36
    return sign + base36

def base36decode(number):
    return int(number, 36)

def b36(i):
    if type(i) == int:
        return base36encode(i)
    if type(i) == str:
        return base36decode(i)

def chunklist(inputlist, chunksize):
    if len(inputlist) < chunksize:
        return [inputlist]
    else:
        outputlist = []
        while len(inputlist) > 0:
            outputlist.append(inputlist[:chunksize])
            inputlist = inputlist[chunksize:]
        return outputlist

def cls():
    if os.system('cls'):
        os.system('clear')

def completesweep(shuffle=False, sleepy=0, query=None):
    if shuffle is True:
        cur2.execute('SELECT idstr FROM subreddits WHERE created > 0 ORDER BY RANDOM()')
    elif query is None:
        cur2.execute('SELECT idstr FROM subreddits WHERE created > 0')
    elif query == 'subscribers':
        cur2.execute('SELECT idstr FROM subreddits WHERE created > 0 ORDER BY subscribers DESC')
    elif query == 'restricted':
        cur2.execute('SELECT idstr FROM subreddits WHERE created > 0 AND subreddit_type != 0 ORDER BY subscribers DESC')
    else:
        cur2.execute(query)

    try:
        while True:
            hundred = [cur2.fetchone() for x in range(100)]
            while None in hundred:
                hundred.remove(None)
            if len(hundred) == 0:
                break
            # h[0] because the selection query calls for idstr
            # This is not a mistake
            hundred = [h[0] for h in hundred]
            processmega(hundred, nosave=True)
            time.sleep(sleepy)
    except KeyboardInterrupt:
        pass
    except Exception:
        traceback.print_exc()
    sql.commit()

def fetchgenerator(cur):
    while True:
        fetch = cur.fetchone()
        if fetch is None:
            break
        yield fetch

def get_newest_sub():
    brandnewest = list(r.get_new_subreddits(limit=1))[0]
    return brandnewest.id

def humanize(timestamp):
    day = datetime.datetime.utcfromtimestamp(timestamp)
    human = datetime.datetime.strftime(day, "%b %d %Y %H:%M:%S UTC")
    return human

def modernize():
    cur.execute('SELECT * FROM subreddits ORDER BY created DESC LIMIT 1')
    finalitem = cur.fetchone()
    print('Current final item:')
    print(finalitem[SQL_IDSTR], finalitem[SQL_HUMAN], finalitem[SQL_NAME])
    finalid = finalitem[SQL_IDINT]

    print('Newest item:')
    newestid = get_newest_sub()
    print(newestid)
    newestid = b36(newestid)
    

    modernlist = []
    for x in range(finalid, newestid+1):
        modernlist.append(b36(x).lower())
    processmega(modernlist)

def modsfromid(subid):
    if 't5_' not in subid:
        subid = 't5_' + subid
    subreddit = r.get_info(thing_id=subid)
    mods = list(subreddit.get_moderators())
    for m in mods:
        print(m)
    return mods

def now():
    return datetime.datetime.now(datetime.timezone.utc).timestamp()

def normalize_subreddit_object(thing):
    '''
    Given a string, Subreddit, Submission, or Comment object, return
    a Subreddit object.
    '''
    if isinstance(thing, SUBREDDIT_OBJ):
        return thing

    if isinstance(thing, str):
        return r.get_subreddit(thing)

    if isinstance(thing, (SUBMISSION_OBJ, COMMENT_OBJ)):
        return thing.subreddit

    raise ValueError('Dont know how to normalize', type(thing))

def process(
    subreddit,
    isjumbled=False,
    nosave=False,
    ):
    '''
    Retrieve the API info for the subreddit and save it to the database

    subreddit:
        The subreddit(s) to process. Can be an individual or list of:
        strings or Subreddit, Submission, or Comment objects.

    isjumbled:
        Indicate that this subreddit came from /r/random, because
        the function has no way of knowing on its own.

    nosave:
        If True, don't do any database commits.

        Default = True

    '''
    subreddits = []

    if isinstance(subreddit, (tuple, list, set, types.GeneratorType)):
        subreddits = iter(subreddit)
    else:
        subreddits = [subreddit]

    for subreddit in subreddits:
        subreddit = normalize_subreddit_object(subreddit)

        created = subreddit.created_utc
        created_human = humanize(subreddit.created_utc)
        idint = b36(subreddit.id)
        idstr = subreddit.id
        is_nsfw = int(subreddit.over18 or 0)
        name = subreddit.display_name
        subscribers = subreddit.subscribers or 0
        subreddit_type = SUBREDDIT_TYPE[subreddit.subreddit_type]
        submission_type = SUBMISSION_TYPE[subreddit.submission_type]
        
        cur.execute('SELECT * FROM subreddits WHERE idint == ?', [idint])
        f = cur.fetchone()
        if f is None:
            h = humanize(subreddit.created_utc)
            isjumbled = isjumbled or 0

            message = FORMAT_MESSAGE_NEW.format(
                idstr=idstr,
                human=created_human,
                nsfw=is_nsfw,
                name=name,
                subscribers=subscribers,
                )
            print(message)

            data = {
                SQLS_IDINT: idint,
                SQLS_IDSTR: idstr,
                SQLS_CREATED: created,
                SQLS_HUMAN: created_human,
                SQLS_NSFW: is_nsfw,
                SQLS_NAME: name,
                SQLS_SUBSCRIBERS: subscribers,
                SQLS_JUMBLE: isjumbled,
                SQLS_SUBREDDIT_TYPE: subreddit_type,
                SQLS_SUBMISSION_TYPE: submission_type,
            }

            cur.execute('''
                INSERT INTO subreddits VALUES(
                    @idint,
                    @idstr,
                    @created,
                    @human,
                    @name,
                    @nsfw,
                    @subscribers,
                    @jumble,
                    @subreddit_type,
                    @submission_type
                    )''', data)
        else:
            isjumbled = isjumbled or int(f[SQL_JUMBLE]) or 0
            old_subscribers = f[SQL_SUBSCRIBERS]
            subscriber_diff = subscribers - old_subscribers

            if subscribers == 0 and old_subscribers > 2 and subreddit_type != SUBREDDIT_TYPE['private']:
                print('SUSPICIOUS %s' % name)
                data = {
                    SQLS_IDINT: idint,
                    SQLS_IDSTR: idstr,
                    SQLS_NAME: name,
                    SQLS_SUBSCRIBERS: old_subscribers,
                }
                cur.execute('''
                    INSERT INTO suspicious VALUES(
                        @idint,
                        @idstr,
                        @name,
                        @subscribers
                        )''', data)

            message = FORMAT_MESSAGE_UPDATE.format(
                idstr=idstr,
                human=created_human,
                nsfw=is_nsfw,
                name=name,
                subscribers=subscribers,
                subscriber_diff=subscriber_diff
                )
            print(message)

            data = {
                SQLS_IDINT: idint,
                SQLS_SUBSCRIBERS: subscribers,
                SQLS_JUMBLE: isjumbled,
                SQLS_SUBREDDIT_TYPE: subreddit_type,
                SQLS_SUBMISSION_TYPE: submission_type,
            }
            cur.execute('''
                UPDATE subreddits SET
                subscribers == @subscribers,
                jumble == @jumble,
                subreddit_type == @subreddit_type,
                submission_type == @submission_type
                WHERE idint == @idint
                ''', data)

    if not nosave:
        sql.commit()

def processmega(srinput, isrealname=False, chunksize=100, docrash=False, nosave=False):
    '''
    `srinput` can be a list of subreddit IDs or fullnames, or display names
    if `isrealname` is also True.

    isrealname:
        Interpret `srinput` as a list of actual subreddit names, not IDs.

    chunksize:
        The number of fullnames to get from api/info at once.

    docrash:
        If False, ignore HTTPExceptions and keep moving forward.

    nosave:
        Passed directly into process()

    '''
    global noinfolist
    if type(srinput) == str:
        srinput = srinput.replace(' ', '')
        srinput = srinput.split(',')

    if isrealname:
        for subname in srinput:
            process(subname)
        return

    remaining = len(srinput)
    for x in range(len(srinput)):
        if 't5_' not in srinput[x]:
            srinput[x] = 't5_' + srinput[x]
    srinput = chunklist(srinput, chunksize)
    for subset in srinput:
        try:
            print(subset[0] + ' - ' + subset[-1], remaining)
            subreddits = r.get_info(thing_id=subset)
            try:
                for sub in subreddits:
                    process(sub, nosave=nosave)
            except TypeError:
                noinfolist = subset[:]
                if len(noinfolist) == 1:
                    print('Received no info. See variable `noinfolist`')
                else:
                    for item in noinfolist:
                        processmega([item])

            remaining -= len(subset)
        except praw.errors.HTTPException as e:
            traceback.print_exc()
            print(vars(e))
            if docrash:
                raise

def processrand(count, doublecheck=False, sleepy=0):
    '''
    Gets random IDs between a known lower bound and the newest collection, and pass
    them into processmega().
    
    count:
        How many you want

    doublecheck:
        Should it reroll duplicates before running

    sleepy:
        Used to sleep longer than the required 2 seconds
    '''
    lower = LOWERBOUND_INT

    cur.execute('SELECT * FROM subreddits ORDER BY idint DESC LIMIT 1')
    upper = cur.fetchone()[SQL_IDSTR]
    print('<' + b36(lower).lower() + ',',  upper + '>', end=', ')
    upper = b36(upper)
    totalpossible = upper-lower
    print(totalpossible, 'possible')
    rands = []
    if doublecheck:
        allids = [x[SQL_IDSTR] for x in fetched]
    for x in range(count):
        rand = random.randint(lower, upper)
        rand = b36(rand).lower()
        if doublecheck:
            while rand in allids or rand in rands:
                if rand in allids:
                    print('Old:', rand, 'Rerolling: in allid')
                else:
                    print('Old:', rand, 'Rerolling: in rands')
                rand = random.randint(lower, upper)
                rand = b36(rand).lower()
        rands.append(rand)

    rands.sort()
    processmega(rands)

def show():
    file_all_time = open('show\\all-time.txt', 'w')
    file_all_name = open('show\\all-name.txt', 'w')
    file_all_subscribers = open('show\\all-subscribers.txt', 'w')
    file_dirty_time = open('show\\dirty-time.txt', 'w')
    file_dirty_name = open('show\\dirty-name.txt', 'w')
    file_dirty_subscribers = open('show\\dirty-subscribers.txt', 'w')
    file_jumble_sfw = open('show\\jumble.txt', 'w')
    file_jumble_nsfw = open('show\\jumble-nsfw.txt', 'w')
    file_duplicates = open('show\\duplicates.txt', 'w')
    file_missing = open('show\\missing.txt', 'w')
    file_stats = open('show\\statistics.txt', 'w')
    file_readme = open('README.md', 'r')

    cur.execute('SELECT COUNT(idint) FROM subreddits WHERE created != 0')
    itemcount_valid = cur.fetchone()[0]
    itemcount_nsfw = 0
    name_lengths = {}

    print(itemcount_valid, 'subreddits')

    print('Writing time files.')
    cur.execute('SELECT * FROM subreddits WHERE created !=0 ORDER BY created ASC')
    for item in fetchgenerator(cur):
        itemf = memberformat(item)
        print(itemf, file=file_all_time)
        if int(item[SQL_NSFW]) == 1:
            print(itemf, file=file_dirty_time)
            itemcount_nsfw += 1
    file_all_time.close()
    file_dirty_time.close()

    print('Writing name files and duplicates.')
    previousitem = None
    inprogress = False
    cur.execute('SELECT * FROM subreddits WHERE created != 0 ORDER BY LOWER(name) ASC')
    for item in fetchgenerator(cur):
        if previousitem is not None and item[SQL_NAME] == previousitem[SQL_NAME]:
            print(memberformat(previousitem), file=file_duplicates)
            inprogress = True
        elif inprogress:
            print(memberformat(previousitem), file=file_duplicates)
            inprogress = False
        previousitem = item

        name_length = len(item[SQL_NAME])
        name_lengths[name_length] = name_lengths.get(name_length, 0) + 1

        itemf = memberformat(item)
        print(itemf, file=file_all_name)
        if int(item[SQL_NSFW]) == 1:
            print(itemf, file=file_dirty_name)
    file_duplicates.close()
    file_all_name.close()
    file_dirty_name.close()
    name_lengths = {'%02d'%k:v for (k,v) in name_lengths.items()}


    print('Writing subscriber files.')
    ranks = {'all':1, 'nsfw':1}
    def write_with_rank(itemf, ranktype, filehandle):
        index = ranks[ranktype]
        if index <= RANKS_UP_TO:
            itemf += '{:>9,}'.format(index)
        print(itemf, file=filehandle)
        ranks[ranktype] += 1

    cur.execute('SELECT * FROM subreddits WHERE created != 0 ORDER BY subscribers DESC')
    for item in fetchgenerator(cur):
        itemf = memberformat(item)
        write_with_rank(itemf, 'all', file_all_subscribers)
        if int(item[SQL_NSFW]) == 1:
            write_with_rank(itemf, 'nsfw', file_dirty_subscribers)
    file_all_subscribers.close()
    file_dirty_subscribers.close()

    print('Writing jumble.')
    cur.execute('SELECT * FROM subreddits WHERE jumble == 1 ORDER BY subscribers DESC')
    for item in fetchgenerator(cur):
        if int(item[SQL_NSFW]) == 0:
            print(itemf, file=file_jumble_sfw)
        else:
            print(itemf, file=file_jumble_nsfw)
    file_jumble_sfw.close()
    file_jumble_nsfw.close()

    print('Writing missing.')
    cur.execute('SELECT * FROM subreddits WHERE created == 0 ORDER BY idint ASC')
    for item in fetchgenerator(cur):
        print(item[SQL_IDSTR], file=file_missing)
    file_missing.close()


    print('Writing statistics.')
    headline = 'Collected {0:,} subreddits\n'.format(itemcount_valid)
    statisticoutput = headline + '\n\n'
    statisticoutput += ' SFW: {0:,}\n'.format(itemcount_valid - itemcount_nsfw)
    statisticoutput += 'NSFW: {0:,}\n\n\n'.format(itemcount_nsfw)

    statisticoutput += 'Subreddit type:\n'
    subreddit_types = list(SUBREDDIT_TYPE_REVERSE.keys())
    subreddit_types.sort()
    subreddit_types = [SUBREDDIT_TYPE_REVERSE[k] for k in subreddit_types]
    for subreddit_type in subreddit_types:
        index = SUBREDDIT_TYPE[subreddit_type]
        cur.execute('SELECT COUNT(*) FROM subreddits WHERE created != 0 AND subreddit_type == ?', [index])
        count = cur.fetchone()[0]
        statisticoutput += '{:>16s}: {:,}\n'.format(str(subreddit_type), count)

    statisticoutput += '\n'
    statisticoutput += 'Submission type (None means approved submitters only or inaccessible):\n'
    submission_types = list(SUBMISSION_TYPE_REVERSE.keys())
    submission_types.sort()
    submission_types = [SUBMISSION_TYPE_REVERSE[k] for k in submission_types]
    for submission_type in submission_types:
        index = SUBMISSION_TYPE[submission_type]
        cur.execute('SELECT COUNT(*) FROM subreddits WHERE created != 0 AND submission_type == ?', [index])
        count = cur.fetchone()[0]
        statisticoutput += '{:>16s}: {:,}\n'.format(str(submission_type), count)

    statisticoutput += '\n\n'
    cur.execute('SELECT * FROM subreddits WHERE created != 0 ORDER BY created DESC limit 20000')
    last20k = cur.fetchall()
    timediff = last20k[0][SQL_CREATED] - last20k[-1][SQL_CREATED]
    statisticoutput += 'Over the last 20,000 subreddits:\n'
    statisticoutput += '%.2f subs are created each hour\n' % (20000 / (timediff/3600))
    statisticoutput += '%.2f subs are created each day\n\n\n' % (20000 / (timediff/86400))


    ################################
    # Breakdown by time period
    # hour of day, day of week, day of month, month of year, month-year, year

    def datetimedict(statsdict, strf):
        statsdict[strf] = statsdict.get(strf, 0) + 1
    hoddict = {}
    dowdict = {}
    domdict = {}
    moydict = {}
    myrdict = {}
    yerdict = {}
    print('    performing time breakdown')
    cur.execute('SELECT * FROM subreddits WHERE created != 0')
    for item in fetchgenerator(cur):
        dt = datetime.datetime.utcfromtimestamp(item[SQL_CREATED])
        strftimes = strftime_dict(dt)

        datetimedict(hoddict, strftimes['%H']) # 01
        datetimedict(dowdict, strftimes['%A']) # Monday
        datetimedict(domdict, strftimes['%d']) # 01
        datetimedict(moydict, strftimes['%B']) # January
        datetimedict(myrdict, strftimes['%b%Y']) # Jan2015
        datetimedict(yerdict, strftimes['%Y']) # 2015

    print('    forming columns')
    plotnum = 0
    labels = ['hour of day', 'day of week', 'day of month', 'month of year', 'year', 'month-year', 'name length']
    modes = [None,    'day',   None,    'month', None,    'monthyear', None]
    dicts = [hoddict, dowdict, domdict, moydict, yerdict, myrdict, name_lengths]
    for (index, d) in enumerate(dicts):
        dkeys_primary = list(d.keys())
        dkeys_primary.sort(key=d.get)
        dkeys_secondary = specialsort(dkeys_primary, modes[index])
        dvals = [d[x] for x in dkeys_secondary]

        statisticoutput += labels[index] + '\n'
        for (keyindex, key) in enumerate(dkeys_primary):
            val = d[key]
            val = '{0:,}'.format(val)
            spacer = 34 - (len(key) + len(val))
            spacer = '.' * spacer
            statisticoutput += key + spacer + val
            statisticoutput += ' ' * 8

            key = dkeys_secondary[keyindex]
            val = d[key]
            val = '{0:,}'.format(val)
            spacer = 34 - (len(key) + len(val))
            spacer = '.' * spacer
            statisticoutput += key + spacer + val
            statisticoutput +=  '\n'
        statisticoutput += '\n'

        if d is name_lengths:
            upperlabel = 'Name Lengths'
        else:
            upperlabel = 'Subreddits created - %s' % labels[index]
        plotbars(
            filename=upperlabel,
            upperlabel=upperlabel,
            inputdata=[dkeys_secondary, dvals],
            colormid='#43443a',
            forcezero=True,
            )
        plotnum += 1
        if d is myrdict:
            # In addition to the total month graph, plot the last 15 months
            plotbars(
                filename=upperlabel + ' short',
                upperlabel=upperlabel + ' short',
                inputdata=[dkeys_secondary[-15:], dvals[-15:]],
                colorbg='#272822',
                colorfg='#000',
                colormid='#43443a',
                forcezero=True,
                )
            plotnum += 1
    #
    # Breakdown by time period
    ################################

    print(statisticoutput, file=file_stats)
    file_stats.close()

    print('Updating Readme')
    readmelines = file_readme.readlines()
    file_readme.close()
    readmelines[3] = '#####' + headline
    readmelines[5] = '#####[Today\'s jumble](http://reddit.com/r/%s)\n' % jumble(doreturn=True)[0]
    file_readme = open('README.md', 'w')
    file_readme.write(''.join(readmelines))
    file_readme.close()

    time.sleep(2)
    x = subprocess.call('PNGCREATOR.bat', shell=True, cwd='spooky')
    print()

def memberformat(member):
    member = FORMAT_MEMBER.format(
        idstr=member[SQL_IDSTR],
        human=member[SQL_HUMAN],
        nsfw=member[SQL_NSFW],
        name=member[SQL_NAME],
        subscribers=member[SQL_SUBSCRIBERS])
    return member

def dictadding(targetdict, item):
    if item not in targetdict:
        targetdict[item] = 1
    else:
        targetdict[item] = targetdict[item] + 1
    return targetdict

def specialsort(inlist, mode=None):
    if mode == 'month':
        return ['January', 'February', 'March', \
                'April', 'May', 'June', 'July', \
                'August', 'September', 'October', \
                'November', 'December']
    if mode == 'day':
        return ['Sunday', 'Monday', 'Tuesday', \
                'Wednesday', 'Thursday', 'Friday', \
                'Saturday']
    if mode == 'monthyear':
        td = {}
        for item in inlist:
            nitem = item
            nitem = item.replace(item[:3], monthnumbers[item[:3]])
            nitem = nitem[3:] + nitem[:3]
            td[item] = nitem
        tdkeys = list(td.keys())
        #print(td)
        tdkeys.sort(key=td.get)
        #print(tdkeys)
        return tdkeys
    if mode is None:
        return sorted(inlist)

def search(query="", casesense=False, filterout=[], subscribers=0, nsfwmode=2, doreturn=False, sort=None):
    """
    Search for a subreddit by name
    *str query = The search query
        "query"    = results where "query" is in the name
        "*query"   = results where "query" is at the end of the name
        "query*"   = results where "query" is at the beginning of the name
        "*query*" = results where "query" is in the middle of the name
    bool casesense = is the search case sensitive
    list filterout = [list, of, words] to omit from search. Follows casesense
    int subscribers = minimum number of subscribers
    int nsfwmode =
      0 - Clean only
      1 - Dirty only
      2 - All
    int sort = The integer representing the sql column to sort by. Defaults
               to no sort.
    """
    querys = ''.join([c for c in query if c in GOODCHARS])
    queryx = '%%%s%%' % querys
    if '!' in query:
        cur.execute('SELECT * FROM subreddits WHERE name LIKE ?', [querys])
        return cur.fetchone()
    if nsfwmode in [0,1]:
        cur.execute('SELECT * FROM subreddits WHERE name LIKE ? AND subscribers > ? AND nsfw=?', [queryx, subscribers, nsfwmode])
    else:
        cur.execute('SELECT * FROM subreddits WHERE name LIKE ? AND subscribers > ?', [queryx, subscribers])

    results = []
    if casesense is False:
        querys = querys.lower()
        filterout = [x.lower() for x in filterout]

    if '*' in query:
        positional = True
        front = query[-1] == '*'
        back = query[0] == '*'
        if front and back:
            mid = True
            front = False
            back = False
        else:
            mid = False
    else:
        positional = False

    lenq = len(querys)
    for item in fetchgenerator(cur):
        name = item[SQL_NAME]
        if casesense is False:
            name = name.lower()
        if querys not in name:
            #print('%s not in %s' % (querys, name))
            continue
        if (positional and front) and (name[:lenq] != querys):
            #print('%s not front %s (%s)' % (querys, name, name[:lenq]))
            continue
        if (positional and back) and (name[-lenq:] != querys):
            #print('%s not back %s (%s)' % (querys, name, name[-lenq:]))
            continue
        if (positional and mid) and (querys not in name[1:-1]):
            #print('%s not mid %s (%s)' % (querys, name, name[1:-1]))
            continue
        if any(filters in name for filters in filterout):
            #print('%s not filter %s' % (querys, name))
            continue
        results.append(item)

    if sort is not None:
        results.sort(key=lambda x: x[sort], reverse=True)
    if doreturn is True:
        return results
    else:
        for item in results:
            print(item)

def strftime_dict(dt):
    '''
    Given a datetime object, prepare a dictionary containing the strftime strings
    for the following formatters:'%H', '%A', '%d', '%B', '%b%Y', '%Y'.
    '''
    formatters = ['%H', '%A', '%d', '%B', '%b%Y', '%Y']
    fmt = '||'.join(formatters)
    strf = datetime.datetime.strftime(dt, fmt)
    strf = strf.split('||')
    d = {formatters[i]:strf[i] for i in range(len(formatters))}
    return d

def findwrong():
    cur.execute('SELECT * FROM subreddits WHERE NAME!=?', ['?'])
    fetch = cur.fetchall()
    fetch.sort(key=lambda x: x[SQL_IDINT])
    #sorted by ID
    fetch = fetch[25:]
    
    pos = 0
    l = []

    while pos < len(fetch)-5:
        if fetch[pos][1] > fetch[pos+1][1]:
            l.append(str(fetch[pos-1]))
            l.append(str(fetch[pos]))
            l.append(str(fetch[pos+1]) + "\n")
        pos += 1

    for x in l:
        print(x)

def processjumble(count, nsfw=False):
    for x in range(count):
        sub = r.get_random_subreddit(nsfw=nsfw)
        process(sub, isjumbled=True)
        sql.commit()

def jumble(count=20, doreturn=False, nsfw=False):
    nsfw = 1 if nsfw else 0
    cur.execute('SELECT * FROM subreddits WHERE jumble=1 AND nsfw=? ORDER BY RANDOM() LIMIT ?', [nsfw, count])
    fetch = cur.fetchall()
    random.shuffle(fetch)
    fetch = fetch[:count]
    fetch = [f[:-1] for f in fetch]
    fetchstr = [i[SQL_NAME] for i in fetch]
    fetchstr = '+'.join(fetchstr)
    output = [fetchstr, fetch]
    if doreturn:
        return output
    print(output[0])
    for x in output[1]:
        print(str(x).replace("'", ''))

def rounded(x, rounding=100):
    return int(round(x/rounding)) * rounding

def plotbars(filename, inputdata, upperlabel='Subreddits created', colorbg="#fff", colorfg="#000", colormid="#888", forcezero=False):
    """Create postscript vectors of data

    filename = Name of the file without extension

    inputdata = A list of two lists. First list has the x axis labels, second list
    has the y axis data. x label 14 coresponds to y datum 14, etc.
    """
    print('    Printing', filename)
    t=tkinter.Tk()

    canvas = tkinter.Canvas(t, width=3840, height=2160, bg=colorbg)
    canvas.pack()
    #Y axis
    canvas.create_line(430, 250, 430, 1755, width=10, fill=colorfg)
    #X axis
    canvas.create_line(430, 1750, 3590, 1750, width=10, fill=colorfg)

    dkeys = inputdata[0]
    dvals = inputdata[1]
    entrycount = len(dkeys)
    availablespace = 3140
    availableheight= 1490
    entrywidth = availablespace / entrycount
    #print(dkeys, dvals, "Width:", entrywidth)

    smallest = min(dvals)
    bottom = int(smallest*0.75) - 5
    bottom = 0 if bottom < 8 else rounded(bottom, 10)
    if forcezero:
        bottom = 0
    largest = max(dvals)
    top = int(largest + (largest/5))
    top = rounded(top, 10)
    print(bottom,top)
    span = top-bottom
    perpixel = span/availableheight

    curx = 445
    cury = 1735

    labelx = 420
    labely = 255
    #canvas.create_text(labelx, labely, text=str(top), font=("Consolas", 72), anchor="e")
    labelspan = 130#(1735-255)/10
    canvas.create_text(175, 100, text=upperlabel, font=("Consolas", 72), anchor="w", fill=colorfg)
    for x in range(12):
        value = int(top -((labely - 245) * perpixel))
        value = rounded(value, 10)
        value = '{0:,}'.format(value)
        canvas.create_text(labelx, labely, text=value, font=("Consolas", 72), anchor="e", fill=colorfg)
        canvas.create_line(430, labely, 3590, labely, width=2, fill=colormid)
        labely += labelspan

    for entrypos in range(entrycount):
        entry = dkeys[entrypos]
        entryvalue = dvals[entrypos]
        entryx0 = curx + 10
        entryx1 = entryx0 + (entrywidth-10)
        curx += entrywidth

        entryy0 = cury
        entryy1 = entryvalue - bottom
        entryy1 = entryy1/perpixel
        #entryy1 -= bottom
        #entryy1 /= perpixel
        entryy1 = entryy0 - entryy1
        #print(perpixel, entryy1)
        #print(entry, entryx0,entryy0, entryx1, entryy1)
        canvas.create_rectangle(entryx0,entryy0, entryx1,entryy1, fill=colorfg, outline=colorfg)

        font0x = entryx0 + (entrywidth / 2)
        font0y = entryy1 - 5

        font1y = 1760

        entryvalue = round(entryvalue)
        fontsize0 = len(str(entryvalue)) 
        fontsize0 = round(entrywidth / fontsize0) + 3
        fontsize0 = 100 if fontsize0 > 100 else fontsize0
        fontsize1 = len(str(entry))
        fontsize1 = round(1.5* entrywidth / fontsize1) + 5
        fontsize1 = 60 if fontsize1 > 60 else fontsize1
        canvas.create_text(font0x, font0y, text=entryvalue, font=("Consolas", fontsize0), anchor="s", fill=colorfg)
        canvas.create_text(font0x, font1y, text=entry, font=("Consolas", fontsize1), anchor="n", fill=colorfg)
        canvas.update()
    print('    Done')
    canvas.postscript(file='spooky\\' +filename+".ps", width=3840, height=2160)
    t.geometry("1x1+1+1")
    t.update()
    t.destroy()

def execit(*args, **kwargs):
    exec(*args, **kwargs)
