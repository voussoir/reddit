import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import winsound
import os

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
WAIT = 30
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''




WAITS = str(WAIT)
try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getuG()
    PASSWORD = bot.getpG()
    USERAGENT = bot.getaG()
except ImportError:
    pass


r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

playedSound = False
def scan():
	global playedSound
	print('Starting new search')
	hasmail = False
	for msg in r.get_unread(limit=None):
	    hasmail = True
	
	if hasmail == True:
	    print("You've got mail!")
	    if playedSound == False:
	        winsound.PlaySound('pop.wav', winsound.SND_FILENAME)
	    playedSound = True
	if hasmail == False:
	    playedSound = False
	    print('No mail!')
	user = r.get_redditor(USERNAME)
	lkarma = str(user.link_karma)
	ckarma = str(user.comment_karma)
	lkarma = karmaRound(lkarma)
	ckarma = karmaRound(ckarma)
	karmastring = lkarma + ' | ' + ckarma
	print(karmastring)

def karmaRound(karma):
	if len(karma) > 4 and len(karma) < 7:
		tstring = karma[:-3]
		tstring2 = karma[-3:]
		karma = tstring + '.' + tstring2[:2] + 'K'
		return karma
	if len(karma) > 6:
		tstring = karma[:-6]
		tstring2 = karma[-6:]
		karma = tstring + '.' + tstring2[:2] + 'M'
		return karma
	else:
		return karma

def clear():
	os.system(['clear','cls'][os.name == 'nt'])

while True:
	try:
		clear()
		scan()
	except Exception as e:
		print('An error has occured:', e)
	print('Running again in ' + WAITS + ' seconds \n')
	time.sleep(WAIT)