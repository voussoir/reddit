# Consistency? Where?

import datetime
import praw
import sqlite3

import bot
r=praw.Reddit(bot.aG)
r.config.api_request_delay=1
sql = sqlite3.connect('databases/@gallowboob.db')
cur = sql.cursor()
outfile = open('@hangman.md', 'w', encoding='utf-8')

SQL_COLUMNCOUNT = 16
SQL_IDINT = 0
SQL_IDSTR = 1
SQL_CREATED = 2
SQL_SELF = 3
SQL_NSFW = 4
SQL_AUTHOR = 5
SQL_TITLE = 6
SQL_URL = 7
SQL_SELFTEXT = 8
SQL_SCORE = 9
SQL_SUBREDDIT = 10
SQL_DISTINGUISHED = 11
SQL_TEXTLEN = 12
SQL_NUM_COMMENTS = 13
SQL_FLAIR_TEXT = 14
SQL_FLAIR_CSS_CLASS = 15

FOOTER = '''
submission | archive | note
---------- | ------- | -----
[`3e3d5a`](http://redd.it/3e3d5a) | https://archive.is/H1D2V | /r/woahdude 3d printing support
[`3e3e00`](http://redd.it/3e3e00) | https://archive.is/JcMRf | /r/pics statue
[`3e3isi`](http://redd.it/3e3isi) | https://archive.is/y6jJU | /r/me_ir jeans
[`3e3hdx`](http://redd.it/3e3hdx) | https://archive.is/9XI8J | /r/aww jeans
[`3e3hes`](http://redd.it/3e3hes) | https://archive.is/gwqhf | /r/unexpected jeans
[`3e3ebs`](http://redd.it/3e3ebs) | https://archive.is/FhkWD | /r/me_irl dogbird
[`3f27gh`](http://redd.it/3f27gh) | https://archive.is/CE653 | /r/pics axe spine handle
[`3f281g`](http://redd.it/3f281g) | https://archive.is/FbDZq | /r/pics axe spine handle again
[`3f2bk9`](http://redd.it/3f2bk9) | https://archive.is/c3cBW | /r/woahdude axe spine handle again again
[`3f2838`](http://redd.it/3f2838) | https://archive.is/lOhEe | /r/interestingasfuck axe spine handle again again again
[`3f2508`](http://redd.it/3f2508) | https://archive.is/5tXtG | /r/aww cat with a job
[`3f2axj`](http://redd.it/3f2axj) | https://archive.is/V1Mlx | /r/gifs drifting kid
[`3f29g7`](http://redd.it/3f29g7) | https://archive.is/2OBeP | /r/me_irl guy in water
[`3f25st`](http://redd.it/3f25st) | https://archive.is/vofui | /r/unexpected sexy video on the beach
[`3fjwoe`](http://redd.it/3fjwoe) | https://archive.is/WwRpr | /r/nonononoyes extreme biking
[`3fjws0`](http://redd.it/3fjws0) | https://archive.is/s1B1F | /r/pics RIP Hitchbot
[`3fjy38`](http://redd.it/3fjy38) | https://archive.is/5Rhzu | /r/peoplebeingjerks RIP Hitchbot again
[`3iivzt`](http://redd.it/3iivzt) | https://archive.is/R87l7 | /r/pics tiny wasp nest
[`3ptf6r`](http://redd.it/3ptf6r) | https://archive.is/LsDbE | /r/pics elephant rock
[`3snplt`](http://redd.it/3snplt) | https://archive.is/AIYFU | /r/pics kurds & coalition
[`3snr4u`](http://redd.it/3snr4u) | https://archive.is/GvYoZ | /r/pics dog was doing stuff
[`3snrwh`](http://redd.it/3snrwh) | https://archive.is/Iq29E | /r/pics I touch the poop
'''

def out(text):
    outfile.write(text)
    outfile.write('\n')

def frequencydict(datalist):
    '''
    Given a list, return a dictionary {item: occurances}
    '''
    datadict = {}
    for item in datalist:
        datadict[item] = datadict.get(item, 0) + 1
    return datadict

def average(iterable):
    total = 0
    denominator = 0
    for x in iterable:
        total += x
        denominator += 1

    if denominator == 0:
        return 0
    return total / denominator

def dictformat(datadict, joiner=', '):
    keys = list(datadict.keys())
    samplekey = keys[0]
    if isinstance(datadict[samplekey], list):
        # For duplicate lists, sort by longest list .
        keys.sort(key=lambda x: len(datadict[x]), reverse=True)
    elif isinstance(datadict[samplekey], dict):
        # For subreddit breakdowns, sort by total posts made.
        keys.sort(key=lambda x: datadict[x]['posts_made'])
    else:
        # For frequency dicts, sort by highest count.
        keys.sort(key=datadict.get, reverse=True)
    out = ''
    for key in keys:
        val = datadict[key]
        if isinstance(val, dict):
            val = [val['posts_made'], val['posts_deleted'], val['total_karma']]
        if isinstance(val, list):
            val = joiner.join([str(x) for x in val])
        out += '%s | %s\n' % (key, val)
    return out

def findduplicates(datalist, attribute):
    '''
    Given a list of objects, and an attribute of interest, return a dictionary
    {value: [object, object, ...]}
    which maps unique attribute values to a list of objects having that value,
    and there are at least two objects.
    '''
    datadict = {}
    for item in datalist:
        value = getattr(item, attribute)
        datadict.setdefault(value, [])
        datadict[value].append(item)
    datadict = {attribute:holders for (attribute, holders) in datadict.items() if len(holders) > 1}
    return datadict

def listblock(x, blocklength=12, joins=', '):
    out = ''
    x = ['[`{i}`](http://redd.it/{i})'.format(i=i) for i in x]
    l = len(x)
    ra = (l // blocklength)
    if l % blocklength is not 0:
        ra += 1
    for i in range(ra):
        a = i*blocklength
        b = a + blocklength
        out += joins.join(x[a:b])
        out += '  \n'
    return out


def main():
    out('/u/GallowBoob\n======\n\n')
    out('Obviously I can\'t tell if a deleted post was its if I find it too late,')
    out('so these numbers should be considered lower than is correct.  ')
    out('[click here](https://github.com/voussoir/reddit/raw/master/Prawtimestamps/databases/%40gallowboob.db) to download the sqlite db.')
    out('')

    cur.execute('SELECT idstr FROM posts WHERE idstr LIKE "t3_%" ORDER BY created DESC')
    refreshids = [x[0] for x in cur.fetchall()]

    submissions_total = []
    submissions_living = []
    submissions_nonliving = []
    while len(refreshids) > 0:
        print('Updating. %d remaining' % len(refreshids))
        items = r.get_info(thing_id=refreshids[:100])
        refreshids = refreshids[100:]
        for item in items:
            if item.author is None:
                item.dot = '-'
                submissions_nonliving.append(item)
            else:
                item.dot = '+'
                submissions_living.append(item)
            submissions_total.append(item)

    out('Submissions on record: %d  ' % len(submissions_total))
    out('Submissions alive: %d  ' % len(submissions_living))
    out('Submissions deleted: %d  ' % len(submissions_nonliving))
    out('')

    cur.execute('SELECT COUNT(idint) FROM posts WHERE self == 1')
    selfposts = cur.fetchone()[0]
    out('Selfposts: %d  ' % selfposts)
    out('Linkposts: %d  ' % (len(submissions_total)-selfposts))
    out('')

    print('Measuring scores')
    out('Average score: %d  ' % average(x.score for x in submissions_total))
    out('Average score of living: %d  ' % average(x.score for x in submissions_living))
    out('Average score of deleted: %d  ' % average(x.score for x in submissions_nonliving))
    out('')

    print('Measuring reposts')
    reposts_total = findduplicates(submissions_total, 'url')
    reposts_living = findduplicates(submissions_living, 'url')
    reposts_nonliving = findduplicates(submissions_nonliving, 'url')
    repost_count_total = sum(len(holders) for holders in reposts_total.values())
    repost_count_living = sum(len(holders) for holders in reposts_living.values())
    repost_count_nonliving = sum(len(holders) for holders in reposts_nonliving.values())
    out('&nbsp;\n\n# reposts\n')
    out('Submissions with the same link as another: %d  ' % repost_count_total)
    out('Submissions living with the same link as another living: %d  ' % repost_count_living)
    out('Submissions deleted with the same link as another deleted: %d  ' % repost_count_nonliving)
    out('Submissions deleted with the same link as another living: %d  ' % (repost_count_total - (repost_count_living+repost_count_nonliving)))
    out('')

    print('Drawing repost table')
    # Minimum of 3 reposts to keep the table shorter and more interesting.
    reposts_total = {attribute:holders for (attribute, holders) in reposts_total.items() if len(holders) > 2}
    for (key, holders) in reposts_total.items():
        holders = ['[`{i}{d}`](http://redd.it/{i})'.format(d=i.dot, i=i.id) for i in holders]
        reposts_total[key] = holders
    out('&nbsp;\n')
    out('Only URLs with 3+ reposts are shown in this table.\n')
    out('`+` : submission is alive\n')
    out('`-` : submission is deleted')
    out('')
    out('url | karma farmas')
    out('----- | -----')
    out(dictformat(reposts_total))
    out('')

    print('Measuring subreddits')
    subreddits_total = frequencydict(x.subreddit.display_name for x in submissions_total)
    subreddits_living = frequencydict(x.subreddit.display_name for x in submissions_living)
    subreddits_nonliving = frequencydict(x.subreddit.display_name for x in submissions_nonliving)
    subreddits_allliving = set(subreddits_total).difference(set(subreddits_nonliving))
    subreddits_alldead = set(subreddits_total).difference(set(subreddits_living))
    out('&nbsp;\n\n# subreddits\n')
    out('Subreddits posted to: %d  ' % len(subreddits_total))
    out('Subreddits with living submissions: %d  ' % len(subreddits_living))
    out('Subreddits with deleted submissions: %d  ' % len(subreddits_nonliving))
    out('Subreddits where all submissions living: %d  ' % len(subreddits_allliving))
    out('Subreddits where all submissions deleted: %d  ' % len(subreddits_alldead))
    out('')

    for subreddit in subreddits_total:
        karma = 0
        deletions = 0
        for post in submissions_total:
            if post.subreddit.display_name == subreddit:
                karma += post.score
                if post.author is None:
                    deletions += 1
        subreddits_total[subreddit] = {
            'posts_made': subreddits_total[subreddit],
            'posts_deleted': deletions,
            'total_karma': karma,
        }

    print('Drawing subreddit table')
    out('subreddit | posts made | posts deleted | score total')
    out(':-------- | ---------: | ------------: | ----------:')
    out(dictformat(subreddits_total, joiner=' | '))
    out('')
    out('&nbsp;\n\n# living\n')
    out(listblock([x.id for x in submissions_living]))
    out('')
    out('&nbsp;\n\n# deleted\n')
    out(listblock([x.id for x in submissions_nonliving]))
    out('')
    out('&nbsp;\n\n# archives\n')
    out(FOOTER)

main()
outfile.close()
