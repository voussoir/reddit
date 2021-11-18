import argparse
import bot3
import datetime
import praw3 as praw
import random
import sqlite3
import string
import subprocess
import sys
import time
import tkinter
import traceback
import types

from voussoirkit import betterhelp
from voussoirkit import mutables
from voussoirkit import operatornotify
from voussoirkit import pipeable
from voussoirkit import sqlhelpers
from voussoirkit import vlogging

log = vlogging.getLogger(__name__, 'sb')

USERAGENT = '''
/u/GoldenSights SubredditBirthdays data collection:
Gathering the creation dates of subreddits for visualization.
More at https://github.com/voussoir/reddit/tree/master/SubredditBirthdays
'''.replace('\n', ' ').strip()

LOWERBOUND_STR = '2qh0j'
LOWERBOUND_INT = 4594339

FORMAT_MEMBER = '{idstr:>5s}, {human}, {nsfw}, {name:<25s} {subscribers:>10,}'
FORMAT_MESSAGE_NEW = 'New: {idstr:>5s} : {human} : {nsfw} : {name} : {subscribers}'
FORMAT_MESSAGE_UPDATE = 'Upd: {idstr:>5s} : {human} : {nsfw} : {name} : {subscribers} ({subscriber_diff})'

RANKS_UP_TO = 20000
# For the files sorted by subscriber count, display ranks up to this many.

GOODCHARS = string.ascii_letters + string.digits + '_'

sql = sqlite3.connect('D:\\git\\reddit\\subredditbirthdays\\sb.db')
cur = sql.cursor()
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
    submission_type INT,
    last_scanned INT)
''')
# cur.execute('CREATE INDEX IF NOT EXISTS index_subreddits_idint ON subreddits(idint)')
cur.execute('CREATE INDEX IF NOT EXISTS index_subreddits_idstr ON subreddits(idstr)')
cur.execute('CREATE INDEX IF NOT EXISTS index_subreddits_name ON subreddits(name)')
cur.execute('CREATE INDEX IF NOT EXISTS index_subreddits_created ON subreddits(created)')
cur.execute('CREATE INDEX IF NOT EXISTS index_subreddits_subscribers ON subreddits(subscribers)')
# cur.execute('CREATE INDEX IF NOT EXISTS index_subreddits_last_scanned ON subreddits(last_scanned)')

cur.execute('''
    CREATE TABLE IF NOT EXISTS suspicious(
    idint INT,
    idstr TEXT,
    name TEXT,
    subscribers INT,
    noticed INT)
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS popular(
    idstr TEXT,
    last_seen INT)
''')
cur.execute('CREATE INDEX IF NOT EXISTS index_popular_idstr on popular(idstr)')
cur.execute('CREATE INDEX IF NOT EXISTS index_popular_last_seen on popular(last_seen)')

cur.execute('''
    CREATE TABLE IF NOT EXISTS jumble(
    idstr TEXT,
    last_seen INT)
''')
cur.execute('CREATE INDEX IF NOT EXISTS index_jumble_idstr on jumble(idstr)')
cur.execute('CREATE INDEX IF NOT EXISTS index_jumble_last_seen on jumble(last_seen)')
sql.commit()

# These numbers are used for interpreting the tuples that come from SELECT
SQL_SUBREDDIT_COLUMNS = [
    'idint',
    'idstr',
    'created',
    'human',
    'name',
    'nsfw',
    'subscribers',
    'subreddit_type',
    'submission_type',
    'last_scanned',
]
SQL_SUSPICIOUS_COLUMNS = [
    'idint',
    'idstr',
    'name',
    'subscribers',
    'noticed',
]

SQL_SUBREDDIT = {key: index for (index, key) in enumerate(SQL_SUBREDDIT_COLUMNS)}

noinfolist = []

monthnumbers = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Aug': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dec': '12',
}

SUBREDDIT_TYPE = {
    'public': 0,
    'restricted': 1,
    'private': 2,
    'archived': 3,
    None: 4,
    'employees_only': 5,
    'gold_restricted': 6,
    'gold_only': 7,
    'user': 8,
}
SUBMISSION_TYPE = {
    'any': 0,
    'link': 1,
    'self': 2,
    None: 3,
}

SUBREDDIT_TYPE_REVERSE = {v: k for (k, v) in SUBREDDIT_TYPE.items()}
SUBMISSION_TYPE_REVERSE = {v: k for (k, v) in SUBMISSION_TYPE.items()}

SUBMISSION_OBJ = praw.objects.Submission
SUBREDDIT_OBJ = praw.objects.Subreddit
COMMENT_OBJ = praw.objects.Comment


print('Logging in.')
r = praw.Reddit(USERAGENT)
bot3.login(r)


def base36encode(number, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    '''Converts an integer to a base36 string.'''
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

def completesweep(sleepy=0, orderby='subscribers desc', query=None):
    cur = sql.cursor()
    if query is None:
        if orderby is None:
            cur.execute('SELECT idstr FROM subreddits WHERE created > 0')
        else:
            cur.execute('SELECT idstr FROM subreddits WHERE created > 0 ORDER BY %s' % orderby)
    elif query == 'restricted':
        cur.execute('SELECT idstr FROM subreddits WHERE created > 0 AND subreddit_type != 0 ORDER BY subscribers DESC')
    else:
        cur.execute(query)

    try:
        while True:
            hundred = (cur.fetchone() for x in range(100))
            hundred = (row for row in hundred if row is not None)
            hundred = [idstr for (idstr,) in hundred]
            if len(hundred) == 0:
                break
            for retry in range(20):
                try:
                    processmega(hundred, commit=False)
                    break
                except Exception:
                    traceback.print_exc()
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

def get_jumble_subreddits():
    cur.execute('SELECT idstr FROM jumble')
    fetch = [x[0] for x in cur.fetchall()]
    fetch = ['\'%s\'' % x for x in fetch]
    fetch = '(' + ','.join(fetch) + ')'
    query = 'SELECT * FROM subreddits WHERE idstr IN %s' % fetch
    cur.execute(query)
    subreddits = cur.fetchall()
    #subreddits = []
    #for subreddit in fetch:
    #    cur.execute('SELECT * FROM subreddits WHERE idstr == ?', [subreddit])
    #    subreddits.append(cur.fetchone())
    return subreddits

def get_newest_sub():
    brandnewest = list(r.get_new_subreddits(limit=1))[0]
    return brandnewest.id

def get_now():
    return datetime.datetime.now(datetime.timezone.utc).timestamp()

def humanize(timestamp):
    day = datetime.datetime.utcfromtimestamp(timestamp)
    human = datetime.datetime.strftime(day, "%b %d %Y %H:%M:%S UTC")
    return human

def modernize(limit=None):
    cur.execute('SELECT * FROM subreddits ORDER BY created DESC LIMIT 1')
    finalitem = cur.fetchone()
    print('Current final item:')
    print(finalitem[SQL_SUBREDDIT['idstr']], finalitem[SQL_SUBREDDIT['human']], finalitem[SQL_SUBREDDIT['name']])
    finalid = finalitem[SQL_SUBREDDIT['idint']]

    print('Newest item:')
    newestid = get_newest_sub()
    print(newestid)
    newestid = b36(newestid)
    if limit is not None:
        newestid = min(newestid, finalid+limit-1)

    modernlist = [b36(x) for x in range(finalid, newestid+1)]
    if len(modernlist) > 0:
        processmega(modernlist, commit=False)
        sql.commit()

def modernize_forever(limit=10000):
    while True:
        try:
            modernize(limit=limit)
        except Exception:
            log.warning(traceback.format_exc())
        time.sleep(300)

def modsfromid(subid):
    if 't5_' not in subid:
        subid = 't5_' + subid
    subreddit = r.get_info(thing_id=subid)
    mods = list(subreddit.get_moderators())
    for m in mods:
        print(m)
    return mods

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
        commit=True,
    ):
    '''
    Retrieve the API info for the subreddit and save it to the database

    subreddit:
        The subreddit(s) to process. Can be an individual or list of:
        strings or Subreddit, Submission, or Comment objects.
    '''
    subreddits = []
    processed_subreddits = []

    if isinstance(subreddit, (tuple, list, set, types.GeneratorType)):
        subreddits = iter(subreddit)
    else:
        subreddits = [subreddit]

    for subreddit in subreddits:
        subreddit = normalize_subreddit_object(subreddit)
        processed_subreddits.append(subreddit)

        created = subreddit.created_utc
        created_human = humanize(subreddit.created_utc)
        idstr = subreddit.id
        is_nsfw = int(subreddit.over18 or 0)
        name = subreddit.display_name
        subscribers = subreddit.subscribers or 0
        subreddit_type = SUBREDDIT_TYPE[subreddit.subreddit_type]
        submission_type = SUBMISSION_TYPE[subreddit.submission_type]

        now = int(get_now())

        cur.execute('SELECT * FROM subreddits WHERE idstr == ?', [idstr])
        f = cur.fetchone()
        if f is None:
            message = FORMAT_MESSAGE_NEW.format(
                idstr=idstr,
                human=created_human,
                nsfw=is_nsfw,
                name=name,
                subscribers=subscribers,
            )
            print(message)

            data = {
                'idint': b36(idstr),
                'idstr': idstr,
                'created': created,
                'human': created_human,
                'nsfw': is_nsfw,
                'name': name,
                'subscribers': subscribers,
                'subreddit_type': subreddit_type,
                'submission_type': submission_type,
                'last_scanned': now,
            }

            (qmarks, bindings) = sqlhelpers.insert_filler(SQL_SUBREDDIT_COLUMNS, data)
            query = 'INSERT INTO subreddits VALUES(%s)' % qmarks
            cur.execute(query, bindings)
        else:
            old_subscribers = f[SQL_SUBREDDIT['subscribers']]
            subscriber_diff = subscribers - old_subscribers

            if subscribers == 0 and old_subscribers > 2 and subreddit_type != SUBREDDIT_TYPE['private']:
                print('SUSPICIOUS %s' % name)
                data = {
                    'idint': b36(idstr),
                    'idstr': idstr,
                    'name': name,
                    'subscribers': old_subscribers,
                    'noticed': int(get_now()),
                }
                (qmarks, bindings) = sqlhelpers.insert_filler(SQL_SUSPICIOUS_COLUMNS, data)
                query = 'INSERT INTO suspicious VALUES(%s)' % qmarks
                cur.execute(query, bindings)

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
                'idstr': idstr,
                'subscribers': subscribers,
                'subreddit_type': subreddit_type,
                'submission_type': submission_type,
                'last_scanned': now,
            }
            (query, bindings) = sqlhelpers.update_filler(data, where_key='idstr')
            query = 'UPDATE subreddits %s' % query
            cur.execute(query, bindings)
            #cur.execute('''
            #    UPDATE subreddits SET
            #    subscribers = @subscribers,
            #    subreddit_type = @subreddit_type,
            #    submission_type = @submission_type,
            #    last_scanned = @last_scanned
            #    WHERE idstr == @idstr
            #    ''', data)
        processed_subreddits.append(subreddit)

    if commit:
        sql.commit()
    return processed_subreddits

def process_input():
    while True:
        x = input('p> ')
        try:
            process(x)
        except KeyboardInterrupt:
            break
        except Exception:
            traceback.print_exc()

def processmega(srinput, isrealname=False, chunksize=100, docrash=False, commit=True):
    '''
    `srinput` can be a list of subreddit IDs or fullnames, or display names
    if `isrealname` is also True.

    isrealname:
        Interpret `srinput` as a list of actual subreddit names, not IDs.

    chunksize:
        The number of fullnames to get from api/info at once.

    docrash:
        If False, ignore HTTPExceptions and keep moving forward.
    '''
    global noinfolist
    if type(srinput) == str:
        srinput = srinput.replace(' ', '')
        srinput = srinput.split(',')

    if isrealname:
        for subname in srinput:
            process(subname)
        return

    processed_subreddits = []
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
                    processed_subreddits.extend(process(sub, commit=commit))
            except TypeError:
                traceback.print_exc()
                noinfolist = subset[:]
                if len(noinfolist) == 1:
                    print('Received no info. See variable `noinfolist`')
                else:
                    #for item in noinfolist:
                    #    processmega([item])
                    pass

            remaining -= len(subset)
        except praw.errors.HTTPException as e:
            traceback.print_exc()
            print(vars(e))
            if docrash:
                raise
    return processed_subreddits

def processrand(count, doublecheck=False, sleepy=0):
    '''
    Gets random IDs between a known lower bound and the newest collection, and
    pass them into processmega().

    count:
        How many you want

    doublecheck:
        Should it reroll duplicates before running

    sleepy:
        Used to sleep longer than the required 2 seconds
    '''
    lower = LOWERBOUND_INT

    cur.execute('SELECT * FROM subreddits ORDER BY idstr DESC LIMIT 1')
    upper = cur.fetchone()[SQL_SUBREDDIT['idstr']]
    print('<' + b36(lower) + ',', upper + '>', end=', ')
    upper = b36(upper)
    totalpossible = upper - lower
    print(totalpossible, 'possible')
    rands = set()
    for x in range(count):
        rand = random.randint(lower, upper)
        rand = b36(rand)
        if doublecheck:
            while rand in rands:
                rand = random.randint(lower, upper)
                rand = b36(rand)
        rands.add(rand)

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

    cur.execute('SELECT COUNT(idstr) FROM subreddits WHERE created != 0')
    itemcount_valid = cur.fetchone()[0]
    itemcount_nsfw = 0
    name_lengths = {}

    print(itemcount_valid, 'subreddits')

    print('Writing time files.')
    cur.execute('SELECT * FROM subreddits WHERE created !=0 ORDER BY created ASC')
    for item in fetchgenerator(cur):
        itemf = memberformat(item)
        print(itemf, file=file_all_time)
        if int(item[SQL_SUBREDDIT['nsfw']]) == 1:
            print(itemf, file=file_dirty_time)
            itemcount_nsfw += 1
    file_all_time.close()
    file_dirty_time.close()

    print('Writing name files and duplicates.')
    previousitem = None
    inprogress = False
    cur.execute('SELECT * FROM subreddits WHERE created != 0 ORDER BY LOWER(name) ASC')
    for item in fetchgenerator(cur):
        if previousitem is not None and item[SQL_SUBREDDIT['name']] == previousitem[SQL_SUBREDDIT['name']]:
            print(memberformat(previousitem), file=file_duplicates)
            inprogress = True
        elif inprogress:
            print(memberformat(previousitem), file=file_duplicates)
            inprogress = False
        previousitem = item

        name_length = len(item[SQL_SUBREDDIT['name']])
        name_lengths[name_length] = name_lengths.get(name_length, 0) + 1

        itemf = memberformat(item)
        print(itemf, file=file_all_name)
        if int(item[SQL_SUBREDDIT['nsfw']]) == 1:
            print(itemf, file=file_dirty_name)
    file_duplicates.close()
    file_all_name.close()
    file_dirty_name.close()
    name_lengths = {'%02d'%k: v for (k, v) in name_lengths.items()}

    print('Writing subscriber files.')
    ranks = {'all': 1, 'nsfw': 1}

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
        if int(item[SQL_SUBREDDIT['nsfw']]) == 1:
            write_with_rank(itemf, 'nsfw', file_dirty_subscribers)
    file_all_subscribers.close()
    file_dirty_subscribers.close()

    print('Writing jumble.')
    for item in get_jumble_subreddits():
        itemf = memberformat(item)
        if int(item[SQL_SUBREDDIT['nsfw']]) == 0:
            print(itemf, file=file_jumble_sfw)
        else:
            print(itemf, file=file_jumble_nsfw)
    file_jumble_sfw.close()
    file_jumble_nsfw.close()

    print('Writing missing.')
    cur.execute('SELECT * FROM subreddits WHERE created == 0 ORDER BY idstr ASC')
    for item in fetchgenerator(cur):
        print(item[SQL_SUBREDDIT['idstr']], file=file_missing)
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
    timediff = last20k[0][SQL_SUBREDDIT['created']] - last20k[-1][SQL_SUBREDDIT['created']]
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
        dt = datetime.datetime.utcfromtimestamp(item[SQL_SUBREDDIT['created']])

        datetimedict(hoddict, dt.strftime('%H')) # 01
        datetimedict(dowdict, dt.strftime('%A')) # Monday
        datetimedict(domdict, dt.strftime('%d')) # 01
        datetimedict(moydict, dt.strftime('%B')) # January
        datetimedict(myrdict, dt.strftime('%b%Y')) # Jan2015
        datetimedict(yerdict, dt.strftime('%Y')) # 2015

    print('    forming columns')
    plotnum = 0
    mapping = [
        {'label': 'hour of day', 'specialsort': None, 'dict': hoddict},
        {'label': 'day of week', 'specialsort': 'day', 'dict': dowdict},
        {'label': 'day of month', 'specialsort': None, 'dict': domdict},
        {'label': 'month of year', 'specialsort': 'month', 'dict': moydict},
        {'label': 'year', 'specialsort': None, 'dict': yerdict},
        {'label': 'month-year', 'specialsort': 'monthyear', 'dict': myrdict},
        {'label': 'name length', 'specialsort': None, 'dict': name_lengths},
    ]
    for (index, collection) in enumerate(mapping):
        d = collection['dict']
        dkeys_primary = list(d.keys())
        dkeys_primary.sort(key=d.get)
        dkeys_secondary = specialsort(dkeys_primary, collection['specialsort'])
        dvals = [d[x] for x in dkeys_secondary]

        statisticoutput += collection['label'] + '\n'
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
            statisticoutput += '\n'
        statisticoutput += '\n'

        if d is name_lengths:
            upperlabel = 'Name Lengths'
        else:
            upperlabel = 'Subreddits created - %s' % collection['label']
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
    readmelines[5] = '#####[Today\'s jumble](http://reddit.com/r/%s)\n' % jumble(nsfw=False)
    file_readme = open('README.md', 'w')
    file_readme.write(''.join(readmelines))
    file_readme.close()

    time.sleep(2)
    subprocess.call('PNGCREATOR.bat', shell=True, cwd='spooky')
    print()

def memberformat(member):
    member = FORMAT_MEMBER.format(
        idstr=member[SQL_SUBREDDIT['idstr']],
        human=member[SQL_SUBREDDIT['human']],
        nsfw=member[SQL_SUBREDDIT['nsfw']],
        name=member[SQL_SUBREDDIT['name']],
        subscribers=member[SQL_SUBREDDIT['subscribers']],
    )
    return member

def dictadding(targetdict, item):
    if item not in targetdict:
        targetdict[item] = 1
    else:
        targetdict[item] = targetdict[item] + 1
    return targetdict

def specialsort(inlist, mode=None):
    if mode == 'month':
        return [
            'January',
            'February',
            'March', 'April',
            'May',
            'June',
            'July',
            'August',
            'September',
            'October',
            'November',
            'December'
        ]
    if mode == 'day':
        return [
            'Sunday',
            'Monday',
            'Tuesday',
            'Wednesday',
            'Thursday',
            'Friday',
            'Saturday'
        ]
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

def search(
        query='',
        casesense=False,
        filterout=[],
        subscribers=0,
        nsfwmode=2,
        doreturn=False,
        sort=None,
    ):
    '''
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
    '''
    querys = ''.join([c for c in query if c in GOODCHARS])
    queryx = '%%{term}%%'.format(term=querys)
    if '!' in query:
        cur.execute('SELECT * FROM subreddits WHERE name LIKE ?', [querys])
        return cur.fetchone()
    if nsfwmode in [0, 1]:
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
        name = item[SQL_SUBREDDIT['name']]
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

    if len(results) == 0:
        if doreturn:
            return []
        else:
            return

    if sort is not None:
        is_numeric = isinstance(results[0][sort], int)
        if is_numeric:
            results.sort(key=lambda x: x[sort], reverse=True)
        else:
            results.sort(key=lambda x: x[sort].lower())

    if doreturn is True:
        return results
    else:
        for item in results:
            print(item)

def findwrong():
    cur.execute('SELECT * FROM subreddits WHERE name != ?', ['?'])
    fetch = cur.fetchall()
    fetch.sort(key=lambda x: x[SQL_SUBREDDIT['idstr']])
    #sorted by ID
    fetch = fetch[25:]

    pos = 0
    wrongs = []

    while pos < len(fetch)-5:
        if fetch[pos][1] > fetch[pos+1][1]:
            wrongs.append(str(fetch[pos-1]))
            wrongs.append(str(fetch[pos]))
            wrongs.append(str(fetch[pos+1]) + "\n")
        pos += 1

    for wrong in wrongs:
        print(wrong)

def processjumble(count, nsfw=False):
    for x in range(count):
        sub = r.get_random_subreddit(nsfw=nsfw)
        process(sub, commit=False)
        last_seen = int(get_now())
        cur.execute('SELECT * FROM jumble WHERE idstr == ?', [sub.id])
        if cur.fetchone() is None:
            cur.execute('INSERT INTO jumble VALUES(?, ?)', [sub.id, last_seen])
        else:
            cur.execute(
                'UPDATE jumble SET last_seen = ? WHERE idstr == ?',
                [sub.id, last_seen]
            )
    sql.commit()

def processpopular(count, sort='hot'):
    subreddit = r.get_subreddit('popular')
    if sort == 'hot':
        submissions = subreddit.get_hot(limit=count)
    elif sort == 'new':
        submissions = subreddit.get_new(limit=count)
    else:
        raise ValueError(sort)

    submissions = list(submissions)
    subreddit_ids = list({submission.subreddit_id for submission in submissions})
    subreddits = processmega(subreddit_ids, commit=False)
    last_seen = int(get_now())
    for subreddit in subreddits:
        cur.execute('SELECT * FROM popular WHERE idstr == ?', [subreddit.id])
        if cur.fetchone() is None:
            cur.execute('INSERT INTO popular VALUES(?, ?)', [subreddit.id, last_seen])
        else:
            cur.execute(
                'UPDATE popular SET last_seen = ? WHERE idstr == ?',
                [last_seen, subreddit.id]
            )
    sql.commit()

def jumble(count=20, nsfw=False):
    subreddits = get_jumble_subreddits()
    if nsfw is not None:
        subreddits = [x for x in subreddits if x[SQL_SUBREDDIT['nsfw']] == int(bool(nsfw))]

    random.shuffle(subreddits)
    subreddits = subreddits[:count]
    subreddits = [f[:-1] for f in subreddits]
    jumble_string = [x[SQL_SUBREDDIT['name']] for x in subreddits]
    jumble_string = '+'.join(jumble_string)
    output = [jumble_string, subreddits]
    return jumble_string

def rounded(x, rounding=100):
    return int(round(x/rounding)) * rounding

def plotbars(
        filename,
        inputdata,
        upperlabel='Subreddits created',
        colorbg="#fff",
        colorfg="#000",
        colormid="#888",
        forcezero=False,
    ):
    '''
    Create postscript vectors of data

    filename = Name of the file without extension

    inputdata = A list of two lists. First list has the x axis labels, second list
    has the y axis data. x label 14 coresponds to y datum 14, etc.
    '''
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
    top = int(largest + (largest / 5))
    top = rounded(top, 10)
    print(bottom, top)
    span = top - bottom
    perpixel = span / availableheight

    curx = 445
    cury = 1735

    labelx = 420
    labely = 255
    #canvas.create_text(labelx, labely, text=str(top), font=("Consolas", 72), anchor="e")
    labelspan = 130
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
        canvas.create_rectangle(entryx0, entryy0, entryx1, entryy1, fill=colorfg, outline=colorfg)

        font0x = entryx0 + (entrywidth / 2)
        font0y = entryy1 - 5

        font1y = 1760

        entryvalue = round(entryvalue)
        fontsize0 = len(str(entryvalue))
        fontsize0 = round(entrywidth / fontsize0) + 3
        fontsize0 = 100 if fontsize0 > 100 else fontsize0
        fontsize1 = len(str(entry))
        fontsize1 = round(1.5 * entrywidth / fontsize1) + 5
        fontsize1 = 60 if fontsize1 > 60 else fontsize1
        canvas.create_text(font0x, font0y, text=entryvalue, font=("Consolas", fontsize0), anchor="s", fill=colorfg)
        canvas.create_text(font0x, font1y, text=entry, font=("Consolas", fontsize1), anchor="n", fill=colorfg)
        canvas.update()
    print('    Done')
    canvas.postscript(file=f'spooky\\{filename}.ps', width=3840, height=2160)
    t.geometry("1x1+1+1")
    t.update()
    t.destroy()

def _idle():
    while True:
        try:
            modernize()
            processpopular(100, 'new')
            processjumble(30, nsfw=False)
            processjumble(30, nsfw=True)
            print('Great job!')
        except Exception:
            traceback.print_exc()
        time.sleep(180)

# Command line #####################################################################################

DOCSTRING = '''
Subreddit Birthdays
===================

{modernize_forever}

{modernize_once}
'''

SUB_DOCSTRINGS = dict(
modernize_forever='''
modernize_forever:
    Gather new subreddits forever.
''',

modernize_once='''
modernize_once:
    Gather new subreddits once.
''',
)

DOCSTRING = betterhelp.add_previews(DOCSTRING, SUB_DOCSTRINGS)
NOTIFY_EVERY_LINE = mutables.Boolean(False)

@pipeable.ctrlc_return1
def modernize_once_argparse(args):
    modernize(limit=args.limit)
    return 0

@pipeable.ctrlc_return1
def modernize_forever_argparse(args):
    NOTIFY_EVERY_LINE.set(True)
    modernize_forever()
    return 0

@operatornotify.main_decorator(subject='sb', notify_every_line=NOTIFY_EVERY_LINE)
@vlogging.main_decorator
def main(argv):
    parser = argparse.ArgumentParser(description=DOCSTRING)
    subparsers = parser.add_subparsers()

    p_modernize_once = subparsers.add_parser('modernize_once', aliases=['modernize-once'])
    p_modernize_once.add_argument('--limit', default=None)
    p_modernize_once.set_defaults(func=modernize_once_argparse)

    p_modernize_forever = subparsers.add_parser('modernize_forever', aliases=['modernize-forever'])
    p_modernize_forever.set_defaults(func=modernize_forever_argparse)

    return betterhelp.subparser_main(argv, parser, DOCSTRING, SUB_DOCSTRINGS)

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
