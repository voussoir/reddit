#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import os
import sys
import sqlite3

'''USER CONFIGURATION'''
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
TITLE = "AutoMail"
#This is the title of every message sent by the bot.
HEADER = "This is the top of the PM"
#This will be the header of every message
FOOTER = "This is the bottom of the PM"
#This will be the footer of every message sent by the bot.
RESPONSE = {'paypal':'Paypal message', 'bitcoin':'Bitcoin message', 'google wallet':'Google Wallet message'}
#Reponse for each message. Entries and their response are separated by colons (:). Separate entries are separated by commas (,)
WAIT = 30
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
'''All done!'''


sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(name TEXT)')
print('Loaded Users table')

sql.commit()


try:
    import bot
    USERAGENT = bot.geta7()
except ImportError:
    pass
WAITS = str(WAIT)

print('Logging in')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)


def scanPM():
    print('Searhing Inbox.')
    pms = r.get_unread(update_user=True)
    for pm in pms:
        alreadysent = False
        result = []
        try:
            author = pm.author.name
            print('Handling ' + pm.id + ' from ' + author)
            cur.execute('SELECT * FROM oldposts WHERE name=?', [author])
            if not cur.fetchone():
                pbody = pm.body.lower()
                for item in RESPONSE:
                    if item.lower() in pbody:
                        result.append(RESPONSE[item])
                        print('\t' + item)
                if len(result) > 0:
                    final = HEADER + '\n\n'
                    final += '\n\n'.join(result)
                    final += '\n\n' + FOOTER
                    r.send_message(author, TITLE, final, captcha=None)
                    cur.execute('INSERT INTO oldposts VALUES(?)', [author])
                    pm.mark_as_read()
                else:
                    print('\tNo results')
            else:
                print('\tAlready sent to ' + author)
        except Exception as e:
            print(e)
        sql.commit()
        
    print('')


while True:
    try:
        scanPM()
    except Exception as e:
        print('ERROR: ' + str(e))
    sql.commit()
    print('Running again in ' + WAITS + ' seconds \n_________\n')
    time.sleep(WAIT)
