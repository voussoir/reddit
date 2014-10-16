#/u/Goldensights

import praw
import time
import datetime

'''USER CONFIG'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
MAXPOSTS = 1000
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 30
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
PRINTFILE = 'messages.txt'
#This is the file, in the same directory as the .py file, where the messages are stored
SUBJECTLINE = "Newsletterly"
ITEMTYPE = 't4'
#The type of item to gather. t4 is a PM
'''All done!'''


WAITS = str(WAIT)
try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.uG
    PASSWORD = bot.pG
    USERAGENT = bot.aG
except ImportError:
    pass

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)


def work():
	unread = r.get_unread(limit=MAXPOSTS)
	results = []
	for message in unread:
		if ITEMTYPE in message.fullname:
			print(message.id, message.subject, end=" ")
			if SUBJECTLINE.lower() in message.subject.lower():
				print(message.body)
				messagedate = datetime.datetime.utcfromtimestamp(message.created_utc)
				messagedate = datetime.datetime.strftime(messagedate, "%B %d %Y %H:%M UTC")
				results += [message.fullname + " : " + message.author.name, messagedate, message.body, "\n\n"]
			else:
				print()
		message.mark_as_read()
	logfile = open(PRINTFILE, "a")	
	for result in results:
		print(result, file=logfile)
	logfile.close()


while True:
    try:
        work()
    except Exception as e:
        print('An error has occured:', str(e))
    print('Running again in ' + WAITS + ' seconds \n')
    time.sleep(WAIT)