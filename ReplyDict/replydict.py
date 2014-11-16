#/u/GoldenSights
import traceback
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
#The file with the Keys/Values

RESULTFORM = "[_key_](_value_)"
#This is the form that the result will take
#You may use _key_ and _value_ to inject the key/value from the dict.
#This preset will create a link where the text is the snake name and the url is the wiki link
#You may delete one or both of these injectors.

LEVENMODE = True
#If this is True it will use a function that is slow but can find misspelled keys
#If this is False it will use a simple function that is very fast but can only find keys which are spelled exactly

MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 30
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


def levenshtein(s1, s2):
    #Levenshtein algorithm to figure out how close two strings are two each other
    #Courtesy http://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
 
    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)
 
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
 
    return previous_row[-1]



def findsuper(comment, tolerance= 3):
    results = []
    used = []
    for itemname in DICT:
        itemlength = len(itemname.split())
        pos = 0
        commentsplit = comment.split()
        #print(commentsplit)
        end = False
        while not end:
            try:
                gram = commentsplit[pos:pos+itemlength]
                gramjoin = ' '.join(gram)
                lev = levenshtein(itemname, gramjoin)
                #print(snakename, gramjoin)
                #print(lev)
                if lev <= tolerance:
                    if itemname not in used:
                        used.append(itemname)
                        result = RESULTFORM
                        result = result.replace('_key_', itemname)
                        result = result.replace('_value_', DICT[itemname])
                        results.append(result)
                pos += 1
                if pos > len(commentsplit):
                    end = True
            except IndexError:
                end = True
    return results

def findsimple(comment):
    results = []
    for itemname in DICT:
        if itemname.lower() in comment.lower():
            result = RESULTFORM
            result = result.replace('_key_', itemname)
            result = result.replace('_value_', DICT[itemname])
            results.append(result)
    return results

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
            if pauthor.lower() != USERNAME.lower():
                pbody = post.body.lower()
            
                if LEVENMODE == True:
                    results = findsuper(pbody)
                else:
                    results = findsimple(pbody)

                if len(results) > 0:
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
        traceback.print_exc()
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)