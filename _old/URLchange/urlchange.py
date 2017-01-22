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
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
HEADER = "I have detected some ship designs in your comment. Here are the viewing links:\n\n"
#This will be at the top of the comment above the results
PARENTSTRING = "http://jundroo.com/ViewShip.html?id="
#These are the words you are looking for
REPLACESTRING = "http://sr.5of0.com/ViewShip.html?id="
#This is what parentstring gets replaced with.
MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 10
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''



PLEN = len(PARENTSTRING)
WAITS = str(WAIT)
try:
    import bot
    USERAGENT = bot.getaG()
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS oldpost_index ON oldposts(id)')
print('Loaded Completed table')

sql.commit()

r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def scanSub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_comments(limit=MAXPOSTS)
    for post in posts:
        result = []
        pid = post.id
        pbody = post.body
        if PARENTSTRING.lower() in pbody.lower():
            cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
            if not cur.fetchone():
                pbodysplit = pbody.split()
                print(pid)
                for sent in pbodysplit:
                    if PARENTSTRING.lower() in sent.lower():
                        try:
                            url = sent.replace(PARENTSTRING, REPLACESTRING)
                            if '(' in url:
                                url = url[url.index('(')+1:]
                                url = url.replace(')', '')                            
                            int(url[PLEN:-1])
                            pauthor = post.author.name
                            if pauthor != r.user.name:
                                result.append(url)
                        except ValueError:
                            print('Not a valid url')
                        except AttributeError:
                            print('Comment author does not exist')
                        except Exception:
                            print('Error.')
                if len(result) > 0:
                    final = HEADER + '\n\n'.join(result)
                    post.reply(final)
                cur.execute('INSERT INTO oldposts VALUES(?)', [pid])    
    sql.commit()

while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', str(e))
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)
 