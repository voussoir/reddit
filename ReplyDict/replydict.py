#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import json

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."

COMMENTHEADER = "This is at the top of the comment"
COMMENTFOOTER = "This is at the bottom of the comment"
#These can be blank if you don't want them.

DICTFILE = 'snakes.txt'
#The file with the Questions/Answers

RESULTFORM = "[_key_](_value_)"
#This is the form that the result will take
#You may use _key_ and _value_ to inject the key/value from the dict.
#This preset will create a link where the text is the snake name and the url is the wiki link
#You may delete one or both of these injectors.

MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''




WAITS = str(WAIT)
try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.uG
    PASSWORD = bot.pG
    USERAGENT = bot.aG
except ImportError:
    pass


with open(DICTFILE, 'r') as f:
    DICT = json.loads(f.read())

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded Completed table')

sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

def scanSub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_comments(limit=MAXPOSTS)
    for post in posts:
        results = []
        pid = post.id
        try:
            pauthor = post.author.name
        except AttributeError:
            pauthor = '[DELETED]'
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if not cur.fetchone():
            pbody = post.body.lower()
            for item in DICT:
                if item.lower() in pbody:
                    result = RESULTFORM
                    result = result.replace('_key_', item)
                    result = result.replace('_value_', DICT[item])
                    results.append(result)

            if len(results) > 0:
                if pauthor.lower() != USERNAME.lower():
                    newcomment = COMMENTHEADER
                    newcomment += '\n\n' + '\n\n'.join(results) + '\n\n'
                    newcomment += COMMENTFOOTER
                    print('Replying to ' + pid + ' by ' + pauthor + ' with ' + str(len(results)) + ' items')
                    post.reply(newcomment)
                else:
                    print('Will not reply to self')
            cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
    sql.commit()


while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', e)
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)