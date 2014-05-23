import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import os
import sys
import datetime
import sqlite3

'''USER CONFIGURATION'''
USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "karmaless"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
WAITS = str(WAIT)

'''All done!'''






try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getu()
    PASSWORD = bot.getp()
    USERAGENT = bot.geta()
except ImportError:
    pass



keywords = ['throowiebot']

timeNow = datetime.datetime.now(datetime.timezone.utc)
timeUnix = timeNow.timestamp()
print(timeUnix)

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS complete(Author TEXT, ID TEXT)')
print('Loaded Completed table')

cur.execute('CREATE TABLE IF NOT EXISTS waiting(Author TEXT, ID TEXT, Wait INT)')
print('Loaded Waiting table')

cur.execute('CREATE TABLE IF NOT EXISTS pm(Author TEXT, ID TEXT, Wait INT, Time REAL)')
print('Loaded PM table')
sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) # necessary if your bot will talk to people

def countTable(table):
    cur.execute("SELECT * FROM '%s'" % table)
    c = 0
    while True:
        row = cur.fetchone()
        if row == None:
            break
        c += 1
    return c
    
def scanCom():
    print('Searching Comments.')
    subreddit = r.get_subreddit(SUBREDDIT)
    comments = subreddit.get_comments(limit=200)
    for comment in comments:
        cur.execute('SELECT * FROM waiting WHERE ID="%s"' % comment.id)
        if not cur.fetchone():
            cur.execute('SELECT * FROM complete WHERE ID="%s"' % comment.id)
            if not cur.fetchone():
                try:
                    if comment.author.name != USERNAME:
                        cstring = 'New - ' + comment.author.name + ': ' + comment.id
                        if any(key in comment.body.lower() for key in keywords):
                            author = comment.author.name
                            bodysplit = comment.body.lower().split()
                            if bodysplit[0] == USERNAME:
                                wait = int(bodysplit[1])
                            else:
                                wait = 1
                            cstring += ' <--'
                            cur.execute('INSERT INTO waiting VALUES(?, ?, ?)', (comment.author.name, comment.id, wait))
                        else:
                            cur.execute('INSERT INTO complete VALUES(?, ?)', (comment.author.name, comment.id))
                        print(cstring)
                except AttributeError:
                    pass
    sql.commit()

def scanPM():
    print('Searhing PMs')
    pms = r.get_unread(unset_has_mail=True, update_user=True)
    for pm in pms:
        cur.execute('SELECT * FROM pm WHERE ID="%s"' % pm.id)
        if not cur.fetchone():
            author = pm.author.name
            idp = pm.id
            bodysplit = pm.body.lower().split()
            if bodysplit[0] == USERNAME:
                print('New: ' + pm.id)
                wait = int(bodysplit[1])
                cur.execute('INSERT INTO pm VALUES(?, ?, ?, ?)', (author, idp, wait, timeUnix))
            else:
                wait = 1
        pm.mark_as_read()
    sql.commit()


def redRem(table):
    timeNow = datetime.datetime.now(datetime.timezone.utc)
    timeUnix = timeNow.timestamp()
    count = countTable(table)
    if count > 30:
        count = 30
        print('Choose 30')
   
    for m in range(0, count):
        cur.execute("SELECT * FROM '%s'" % table)
        row = cur.fetchone()
        if row == None:
            print('Break.')
            break
        idd = row[1]
        waiter = row[2]
        waiter *= 60
        if table == 'waiting':
            print('Processing comment: ' + idd)
            comment = r.get_info(thing_id='t1_' + idd)
            try:
                if (timeUnix - comment.created_utc) > waiter:
                    cur.execute('DELETE FROM waiting WHERE ID == "%s"' % idd)
                    cur.execute('INSERT INTO complete VALUES("%s", "%s")' % (comment.author.name, comment.id))
                    print('Replying to ' + comment.author.name)
                    commstring = comment.body.lower()
                    lines = comment.body.lower().split('\n\n')
                    commstring = commstring.replace(lines[0], '')
                    commstring = commstring.replace('\n\n', '\n\n >')
                    comment.reply('You recently asked for a reminder: \n\n' + '>' + commstring + '\n\n - ' + comment.permalink + '\n\n ^You ^may ^summon ^this ^bot ^with ^"' + USERNAME + ' ^<minute ^delay>"" ^as ^your ^first ^line ^in ^Comment ^or ^PM')
                else:
                    print(comment.id + ' is below age threshold: ' + str(timeUnix - comment.created_utc) + ' / ' + str(waiter))
            except praw.errors.RateLimitExceeded:
                print('PRAW limit reached. Cycling')


        if table == 'pm':
            print('Processing pm: ' + idd)
            pm = r.get_info(thing_id='t4_' + idd)
            rtime = row[3]
            try:

                if (timeUnix - rtime) > waiter:
                    cur.execute('DELETE FROM pm WHERE ID == "%s"' % idd)
                    cur.execute('INSERT INTO complete VALUES("%s", "%s")' % (pm.author.name, pm.id))
                    print('Replying to ' + pm.author.name)
                    commstring = pm.body.lower()
                    lines = pm.body.lower().split('\n\n')
                    commstring = commstring.replace(lines[0], '')
                    commstring = commstring.replace('\n\n', '\n\n >')
                    r.send_message(pm.author.name, 'Reminder!', 'You recently asked for a reminder: \n\n' + '>' + commstring + '\n\n - ' + '\n\n ^You ^may ^summon ^this ^bot ^with ^"' + USERNAME + ' ^<minute ^delay>"" ^as ^your ^first ^line ^in ^Comment ^or ^PM')
                else:
                    print(pm.id + ' is below age threshold: ' + str(timeUnix - rtime) + ' / ' + str(waiter))
            except praw.errors.RateLimitExceeded:
                print('PRAW limit reached. Cycling')

    
def save():
    print('Complete: ' + str(countTable('complete')))
    print('Waiting: ' + str(countTable('waiting')))
    print('PMs: ' + str(countTable('pm')))
    print('Running again in ' + WAITS + ' seconds. \n')
    sql.commit()

while True:
    scanCom()
    print('Finished Comments.')
    scanPM()
    print('Finished PMs')
    print('Operating on Waitlist.')
    redRem('waiting')
    print('Finished Waitlist.')
    print('Operating on PMs.')
    redRem('pm')
    print('Finished PMs.')
    save()
    time.sleep(WAIT)
