#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import winsound
import os
import getpass

'''USER CONFIGURATION'''

USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "findareddit+nostupidquestions+outoftheloop+tipofmytongue+tooafraidtoask+whatstheword"
#The sub or subs to scan
WAIT = 10
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''



lastid = ''
WAITS = str(WAIT)
try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERAGENT = bot.getaG()
except ImportError:
    pass

print('Connecting to reddit')
r = praw.Reddit(USERAGENT)


playedSound = False
def scan():
	global lastid
	subreddit = r.get_subreddit(SUBREDDIT)
	new = subreddit.get_new(limit=1)
	for item in new:
		pid = item.id
		if pid != lastid:
			lastid = pid
			winsound.PlaySound('pop.wav', winsound.SND_FILENAME)
	print('\r' + lastid, end='')


def clear():
	os.system(['clear','cls'][os.name == 'nt'])

while True:
	try:
		scan()
	except Exception as e:
		print('An error has occured:', e)
	time.sleep(WAIT)