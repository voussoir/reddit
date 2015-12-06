#/u/GoldenSights
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
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
TITLE = "Newsletterly"
#This is the title of every message sent by the bot.
FOOTER = "[In operating Newsletterly](http://redd.it/26xset)"
#This will be the footer of every message sent by the bot.
MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 30
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
ADMIN = "GoldenSights"
'''All done!'''





try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getuN()
    PASSWORD = bot.getpN()
    USERAGENT = bot.getaN()
except ImportError:
    pass
WAITS = str(WAIT)


sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded Completed table')

cur.execute('CREATE TABLE IF NOT EXISTS subscribers(name TEXT, reddit TEXT)')
print('Loaded Subscriber table')

sql.commit()


r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

def updateSubs():
    print('Updating subscriptions.')
    global SUBREDDIT
    sublist = []
    cur.execute('SELECT * FROM subscribers')
    for sub in cur.fetchall():
        if sub[1] not in sublist:
            sublist.append(sub[1])
    if len(sublist) > 0:
        SUBREDDIT = '+'.join(sublist)
    return SUBREDDIT

def updateUsers():
    print('Updating users.')
    ulist = []
    cur.execute('SELECT * FROM subscribers')
    for sub in cur.fetchall():
        if sub[0] not in ulist:
            ulist.append(sub[0])
    if len(ulist) > 0:
        ustring = '\n\n/u/'.join(ulist)
        ustring = '/u/' + ustring
    else:
        ustring = 'None!'
    return ustring

def countTable(table):
    cur.execute("SELECT * FROM '%s'" % table)
    c = 0
    while True:
        row = cur.fetchone()
        if row is None:
            break
        else:
            c += 1
    return c

def scanSub():
    print('Searching Subreddits.')
    subreddit = r.get_subreddit(SUBREDDIT)
    userlist = []
    cur.execute('SELECT * FROM subscribers')
    for user in cur.fetchall():
        if user[0] not in userlist:
            userlist.append(user[0])
    for user in userlist:
        print('Finding posts for ' + user)
        usersubs = []
        result = []
        cur.execute('SELECT * FROM subscribers WHERE name=?', [user])
        f = cur.fetchall()
        for m in f:
            usersubs.append(m[1])
        for post in subreddit.get_new(limit=MAXPOSTS):
            cur.execute('SELECT * FROM oldposts WHERE ID=?', [post.id])
            if not cur.fetchone():
                if post.subreddit.display_name.lower() in usersubs:
                    print('\t' + post.id)
                    try:
                        pauthor = ' /u/' + post.author.name
                    except:
                        pauthor = ' DELETED'
                    f= '[/r/' + post.subreddit.display_name + pauthor + ': ' + post.title + '](' + post.permalink + ')'
                    result.append(f)

        if len(result) > 0:
            final = 'Your subscribed subreddits have had some new posts: \n\n' + '\n\n'.join(result)
            final = final[:9900]
            final = final + '\n\n___\n\n' + FOOTER
            r.send_message(user, TITLE, final, captcha=None)
        else:
            print('\tNone')
    for post in subreddit.get_new(limit=MAXPOSTS):
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [post.id])
        if not cur.fetchone():
            cur.execute('INSERT INTO oldposts VALUES(?)', [post.id])
    sql.commit()



def scanPM():
    print('Searhing Inbox.')
    pms = r.get_unread(unset_has_mail=True, update_user=True)
    for pm in pms:
        result = []
        author = pm.author.name
        bodysplit = pm.body.lower().split('\n\n')
        if len(bodysplit) <= 10:
            for line in bodysplit:
                linesplit = line.split()
                try:
                    command = linesplit[0]
                except Exception:
                    command = 'null'
                args = []
                try:
                    linesplit = linesplit[1:]
                    for string in linesplit:
                        args.append(string.replace(',',''))
                except Exception:
                    args.append('')
    
        
                if args:
                    for arg in args:
                        print(author + ': ' + command + ' ' + arg)
                        if command == 'subscribe':
                            try:
                                s = r.get_subreddit(arg, fetch=True)
                                cur.execute('SELECT * FROM subscribers WHERE name=? AND reddit=?', (author, arg))
                                if not cur.fetchone():
                                    cur.execute('INSERT INTO subscribers VALUES(?, ?)', (author, arg))
                                    result.append('You have registered in the Newsletter database to receive /r/' + arg)
                                else:
                                    print(author + ' is already subscribed to ' + arg)
                                    result.append('You are already registered in the Newsletter database to receive /r/' + arg)
                            except Exception:
                                result.append('Unable to find any subreddit by the name of /r/' + arg + '. Confirm that it is spelled correctly and is public.')
                
                        if command == 'unsubscribe':
                            if arg == 'all':
                                cur.execute('DELETE FROM subscribers WHERE name = ?', [author])
                                result.append('You have been removed from all subscriptions.')
                            else:
                                cur.execute('SELECT * FROM subscribers WHERE name=? AND reddit=?', (author, arg))
                                if cur.fetchone():
                                    cur.execute('DELETE FROM subscribers WHERE name = ? AND reddit = ?', (author, arg))
                                    result.append('You will no longer receive /r/' + arg)
                                else:
                                    result.append('You are not registered in the Newsletter database to receive /r/' + arg)

                        if command == 'reportall' and author == ADMIN:
                            s = ''
                            un = ''
                            try:
                                u = r.get_redditor(arg)
                                un = u.name
                            except Exception:
                                s += '\n\nUser does not exist!'
                            cur.execute('SELECT * FROM subscribers WHERE name=?', [un])
                            f = cur.fetchall()
                            for m in f:
                                s += '\n\n/r/' + m[1]
                            if s == '':
                                s += '\n\nNone!'
                            result.append('All active Newsletter subscriptions for /u/' + arg + ':' + s)
            
                elif command == 'report':
                    print(author + ': report')
                    s = ''
                    cur.execute('SELECT * FROM subscribers WHERE name=?', [author])
                    f = cur.fetchall()
                    for m in f:
                        s = s + '/r/' + m[1] + '\n\n'
                    if s == '':
                        s += 'None!'
                    result.append('You have requested a list of your Newsletter subscriptions.\n\n' + s)

                elif command == 'reportall' and author == ADMIN:
                    print(author + ': reportall')
                    s = updateSubs()
                    s = s.replace('+','\n\n/r/')
                    result.append('All active Newsletter subscriptions:\n\n/r/' + s)

                elif command == 'reportusers' and author == ADMIN:
                    print(author + ': reportusers')
                    s = updateUsers()
                    result.append('All active Newsletter users:\n\n' + s)
                
                elif command == 'null':
                    print(author + ': null')
                else:
                    print(author + ': ' + command + ' < Bad syntax')
                    result.append("The command '" + command + "' doesn't seem to comply with proper syntax")
                if command != 'null':
                    result.append('\n\n_____')
                sql.commit()
            final =  '\n\n'.join(result)
            final = final[:9900]
            final = final + '\n\n' + FOOTER

        else:
            final = 'Your message was too long. This measure is in place to prevent abuse. \
            When subscribing to multiple subreddits, use the comma syntax instead of making new lines\n\n_____\n\n' + FOOTER
            print(author + ': Message was too long')
        
        r.send_message(author, TITLE, final, captcha=None)
        pm.mark_as_read()
    sql.commit()
    print('')


while True:
    try:
        scanPM()
        updateSubs()
        scanSub()
    except Exception as e:
        print('ERROR: ' + str(e))
    print(str(countTable('subscribers')) + ' active subscriptions.')
    print('Running again in ' + WAITS + ' seconds \n_________\n')
    sql.commit()
    time.sleep(WAIT)
