#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import os
import sys

'''USER CONFIGURATION'''
USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
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





try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getu7()
    PASSWORD = bot.getp7()
    USERAGENT = bot.geta7()
except ImportError:
    pass
WAITS = str(WAIT)

print('Logging in ' + USERNAME)
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 



def scanPM():
    print('Searhing Inbox.')
    pms = r.get_unread(unset_has_mail=True, update_user=True)
    for pm in pms:
        result = []
        try:
            author = pm.author.name
        except Exception:
            author = 'DELETED'
        pbody = pm.body.lower()
        print('Handling ' + pm.id + ' from ' + author)
        for item in RESPONSE:
            if item.lower() in pbody:
                result.append(RESPONSE[item.lower()])
                print('\t' + item)
        final = HEADER + '\n\n'
        final += '\n\n'.join(result)
        final += '\n\n' + FOOTER
        
        r.send_message(author, TITLE, final, captcha=None)
        pm.mark_as_read()
    print('')


while True:
    try:
        scanPM()
    except Exception as e:
        print('ERROR: ' + str(e))
    print('Running again in ' + WAITS + ' seconds \n_________\n')
    time.sleep(WAIT)
