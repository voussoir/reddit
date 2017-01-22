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
SUBREDDIT = "pkmntcgreferences"
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
cur.execute('CREATE INDEX IF NOT EXISTS idindex on oldposts(id)')
sql.commit()

print('Logging in')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def create_alphabet_headers(names):
    finals = []
    # This section is treated differently than the rest
    # because we don't want to break them up by their
    # initial character
    finals.append('**0-9 and others**\n\n_____\n\n')
    for (itemindex, item) in enumerate(names):
        if item[1] not in string.ascii_letters:
            finals.append(item + '\n\n')
        else:
            # Now the rest of the list contains alphabetic items only
            names = names[itemindex:]
            break

    # Go through each item in the names list and place
    # it into the proper bucket
    alphasections = {}
    for item in names:
        # [1] because we have a markdown bracket at 0
        initial = item[1].upper()
        item += '\n\n'
        if initial in alphasections:
            alphasections[initial].append(item)
        else:
            alphasections[initial] = [item]

    # Go through each bucket and add their content to the final
    for letter in string.ascii_uppercase:
        finals.append('**' + letter + '**\n\n_____\n\n')
        if letter not in alphasections:
            continue
        finals += alphasections[letter]

    return finals

def scan():
    print('Scanning ' + SUBREDDIT)
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = list(subreddit.get_new(limit=MAXPOSTS))
    # Place newest submissions at the end
    posts.reverse()
    names = {}
    for post in posts[:]:
        pid = post.id
        cur.execute('SELECT * FROM oldposts WHERE id=?', [pid])
        if cur.fetchone():
            # removing from the list is okay because it's a slice copy
            posts.remove(post)
            continue
        try:
            print('%s: %s' % (pid, post.author.name))
            names[post.author.name] = post.permalink
        except AttributeError:
            print(pid + ': Post deleted')
            posts.remove(post)
        cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
        sql.commit()

    if len(posts) == 0:
        print('No new posts')
        return

    print('Reading Wiki')
    wikipage = r.get_wiki_page(WIKISUBREDDIT, WIKIPAGE)
    pagecontent = wikipage.content_md

    print('Formatting names')
    pcontentsplit = pagecontent.split('\n')
    for item in pcontentsplit:
        if 'reddit.com' not in item:
            continue
        # [name](hyperlink)
        item = item.replace('\r','')
        item = item.replace('\\_', '_')
        item = item.split('](')
        username = item[0].split('[')[1]
        lastsubmission = item[1].split(')')[0]
        # Names set by the posts above will not be overwritten
        # because those ones are new.
        names.setdefault(username, lastsubmission)

    names = ['[%s](%s)' % (username, names[username]) for username in names]
    names.sort(key=str.lower)
    names = [item.replace('_', '\_') for item in names]

    if VERBOSE:
        print(names)

    finals = create_alphabet_headers(names)

    if VERBOSE is True:
        print(finals)
    print('Saving wiki page')
    wikipage.edit(''.join(finals))

if __name__ == '__main__':
    while True:
        try:
            scan()
            sql.commit()
        except Exception:
            traceback.print_exc()
        print('Running again in %d seconds.\n' % WAIT)
        time.sleep(WAIT)