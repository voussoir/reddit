#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
HEADER = "You have linked to a .gif file on GFYCat. Here are the webm links:\n\n"
#This will be at the top of the comment above the results
PARENTSTRING = ["http://giant.gfycat.com/", "http://fat.gfycat.com/", "http://zippy.gfycat.com/"]
#These are the words you are looking for
REPLACESTRING = "http://gfycat.com/"
#This is what parentstring gets replaced with.
MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 10
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
IGNORESELF = False
#Can the bot account reply to itself?


'''All done!'''



PLEN = len(PARENTSTRING)
WAITS = str(WAIT)
try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getuG()
    PASSWORD = bot.getpG()
    USERAGENT = bot.getaG()
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded Completed table')

sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

def scanPosts():
    print('Searching '+ SUBREDDIT + ' submissions.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_new(limit=MAXPOSTS)
    for post in posts:
        result = []
        pid = post.id
        purl = post.url
        if any (key.lower() in purl.lower() for key in PARENTSTRING):
            cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
            if not cur.fetchone():
                print(pid)
                try:
                    pauthor = post.author.name
                    if pauthor != USERNAME or IGNORESELF == False:
                        for key in PARENTSTRING:
                            if key in purl:
                                result.append(purl.replace(key, REPLACESTRING)[:-4])
                                break
                    else:
                        print('Will not reply to self.')
                except ValueError:
                    print('Not a valid url')
                except AttributeError:
                    print('Comment author does not exist')
                except Exception:
                    print('Error.')
                if len(result) > 0:
                    final = HEADER + '\n\n'.join(result)
                    print('\tCreating comment')
                    post.add_comment(final)
                cur.execute('INSERT INTO oldposts VALUES(?)', [pid])    
    sql.commit()

def scanComs():
    print('Searching '+ SUBREDDIT + ' comments.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_comments(limit=MAXPOSTS)
    for post in posts:
        result = []
        pid = post.id
        pbody = post.body
        if any (key.lower() in pbody.lower() for key in PARENTSTRING):
            cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
            if not cur.fetchone():
                pbodysplit = pbody.split()
                print(pid)
                for sent in pbodysplit:
                    if any(key.lower() in sent.lower() for key in PARENTSTRING):
                        try:
                            pauthor = post.author.name
                            if pauthor != USERNAME or IGNORESELF == False:
                                for key in PARENTSTRING:
                                    if key in sent:
                                        result.append(sent.replace(key, REPLACESTRING)[:-4])
                                        break
                            else:
                                print('Will not reply to self')
                        except ValueError:
                            print('Not a valid url')
                        except AttributeError:
                            print('Comment author does not exist')
                        except Exception:
                            print('Error.')
                if len(result) > 0:
                    final = HEADER + '\n\n'.join(result)
                    print('\tCreating comment')
                    post.reply(final)
                cur.execute('INSERT INTO oldposts VALUES(?)', [pid])    
    sql.commit()

while True:
    try:
        scanPosts()
        scanComs()
    except Exception as e:
        print('An error has occured:', str(e))
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)
 