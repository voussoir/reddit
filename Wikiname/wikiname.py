#/u/GoldenSights
import praw
import sqlite3
import time
import traceback
import string


APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "all"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
WIKISUBREDDIT = "GoldTesting"
#This is the subreddit which owns the wikipage. Perhaps you wish to document posts on subs other than your own.
WIKIPAGE = "Gold"
#This is the page of the wiki that you will be editing
MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 31
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
VERBOSE = False
#IF Verbose is set to true, the console will spit out a lot more information. Use True or False (Use capitals! No quotations!)


'''All done!'''

try:
    import bot
    USERAGENT = bot.aG
    APP_ID = bot.oG_id
    APP_SECRET = bot.oG_secret
    APP_URI = bot.oG_uri
    APP_REFRESH = bot.oG_scopes['all']
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')
print('Loaded Oldposts')
sql.commit()

r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def scan():
    print('Reading Wiki')
    names = {}
    finals = []
    wikisubreddit = r.get_subreddit(WIKISUBREDDIT)
    wikipage = r.get_wiki_page(wikisubreddit, WIKIPAGE)
    pcontent = wikipage.content_md
    print('Gathering names')
    pcontentsplit = pcontent.split('\n')
    for item in pcontentsplit:
        if 'http' not in item:
            continue
        item = item.replace('\r','')
        item = item.replace('\\_', '_')
        item = item.split('](')
        username = item[0].split('[')[1]
        lastsubmission = item[1].split(')')[0]
        names[username] = lastsubmission

    print('Scanning ' + SUBREDDIT)
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = list(subreddit.get_new(limit=MAXPOSTS))
    # Place newest submissions at the end
    posts.reverse()
    for post in posts:
        pid = post.id

        cur.execute('SELECT * FROM oldposts WHERE id=?', [pid])

        if cur.fetchone():
            continue

        try:
            pauthor = post.author.name
        except AttributeError:
            print(pid + ': Post deleted')
            continue

        print('%s: %s' % (pid, pauthor))
        names[pauthor] = post.permalink
        cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
        sql.commit()

    names = ['[%s](%s)' % (username, names[username]) for username in names]
    names.sort(key=str.lower)
    names = [item.replace('_', '\_') for item in names]

    if VERBOSE:
        print(names)

    finals.append('**0-9 and others**\n\n_____\n\n')
    for (itemindex, item) in enumerate(names):
        if item[1] not in string.ascii_letters:
            finals.append(item + '\n\n')
        else:
            names = names[itemindex:]
            break

    alphasections = {}
    for item in names:
        initial = item[1].upper()
        item += '\n\n'
        if initial in alphasections:
            alphasections[initial].append(item)
        else:
            alphasections[initial] = [item]

    for letter in string.ascii_uppercase:
        finals.append('**' + letter + '**\n\n_____\n\n')
        if letter not in alphasections:
            continue
        finals += alphasections[letter]

        #for (itemindex, item) in enumerate(names):
        #    print(letter, item[:20])
        #    if item[1].upper() == letter:
        #        finals.append(item + '\n\n')
    if VERBOSE == True:
        print(finals)
    print('Saving wiki page')
    wikipage.edit(''.join(finals))





while True:
    try:
        scan()
        sql.commit()
    except Exception:
        traceback.print_exc()
    print('Running again in %d seconds.\n' % WAIT)
    time.sleep(WAIT)