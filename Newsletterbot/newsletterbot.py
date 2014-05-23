import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import os
import sys
import sqlite3

'''USER CONFIGURATION'''
USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "Newsletter bot"
SUBREDDIT = "recordthis"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
MAXPOSTS = 10
#This is how many posts you want to retreieve all at once. Max 100, but your subs probably don't get 100 posts per minute.
WAIT = 600
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

'''All done!'''





try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getu()
    PASSWORD = bot.getp()
    USERAGENT = bot.geta()
except ImportError:
    pass
WAITS = str(WAIT)


sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded Completed table')

cur.execute('CREATE TABLE IF NOT EXISTS subscribers(Subscriber TEXT)')
print('Loaded Subscriber table')

sql.commit()


r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 


def countTable(table):
    cur.execute("SELECT * FROM '%s'" % table)
    c = 0
    while True:
        row = cur.fetchone()
        if row == None:
            break
        else:
            c += 1
    return c

filters = ['recordthis', 'gifs']
def scanSub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_new(limit=MAXPOSTS)
    for post in posts:
        cur.execute('SELECT * FROM oldposts WHERE ID="%s"' % post.id)
        if not cur.fetchone():
            try:
                print('Found new thread: ' + post.id)
                cur.execute('INSERT INTO oldposts VALUES("%s")' % post.id)

                cur.execute('SELECT * FROM subscribers')
                subscriberlist = cur.fetchall()
                for m in subscriberlist:
                    subscriber = m[0]
                    print('Messaging subscribers')
                    r.send_message(subscriber, 'Your ' + SUBREDDIT + ' newsletter', SUBREDDIT + ' has had a new post! Find it [here](' + post.permalink + ') \n\n Send a message containing "Unsubscribe" to be unsubscribed from the newsletter', captcha=None)
            
            except IndexError:
                pass
    sql.commit()

def scanPM():
    print('Searhing Inbox.')
    pms = r.get_unread(unset_has_mail=True, update_user=True)
    for pm in pms:
        author = pm.author.name
        bodysplit = pm.body.lower().split()
        if bodysplit[0] == 'subscribe':
            cur.execute('SELECT * FROM subscribers WHERE Subscriber="%s"' % author)
            if not cur.fetchone():
                print('New Subscriber: ' + author)
                cur.execute('INSERT INTO subscribers VALUES("%s")' % author)


        if bodysplit[0] == 'unsubscribe':
            print('Lost Subscriber: ' + author)
            cur.execute('DELETE FROM subscribers WHERE Subscriber == "%s"' % author)
        pm.mark_as_read()
    sql.commit()


while True:
    scanPM()
    scanSub()
    print(str(countTable('subscribers')) + ' subscribers.')
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)
