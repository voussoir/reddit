#/u/GoldenSights
import praw
import time
import pytz
from datetime import datetime

'''USER CONFIGURATION'''
USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
TITLE = "Country of the day for %B %d: _country_"
#This is the title of the submission to your subreddit. _country_ will be replaced by the country
#%B and %d will be interpreted by time.strftime()
SUBMISSION = "http://www.google.com/search?q=site:wikipedia.org%20_country_%20country&btnI"
#This is the link that will be submitted. _country_ will be replaced by the country
TIMEZONE = 'utc'
#What timezone are you using?
#http://stackoverflow.com/questions/13866926/python-pytz-list-of-timezones
WAIT = 30
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
PRINTFILE = "country_list.txt"
#This is the file, in the same directory as the .py file, where the names are stored
WEEKEND = ["Saturday", "Sunday"]
#These are days that you don't want the bot to run. You can have anything you want in here. Use proper capitalisation.

'''All done!'''




clistfile = open(PRINTFILE, "a+")
clistfile.close()
#This is a hackjob way of creating the file if it does not exist

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


def scanSub():
	print('Scanning')
	clistfile = open(PRINTFILE, "r+")
	clist = []
	currentday = datetime.now(pytz.timezone(TIMEZONE))
	currentdaystr = str(currentday)
	currentdaystr = currentdaystr[:19]
	print('Current day: ' + currentdaystr)
	for line in clistfile:
		clist.append(line.strip())

	if len(clist) > 0:
		for m in range(len(clist)):
			if clist[m][0] != '*':
				current = clist[m]
				currentm = m
				
				break

		if datetime.strftime(currentday, "%A") not in WEEKEND:

			if clist[0] == '*' + currentdaystr[:10]:
				print('Same day')
	
			else:
				clistfile.close()
				print('New day')
				print('Posting ' + current)
				try:
					r.submit(SUBREDDIT, str(datetime.strftime(currentday, TITLE.replace('_country_', current))), \
					url=SUBMISSION.replace('_country_', current.replace(' ', '%20')), captcha=None)
				except praw.errors.AlreadySubmitted:
					print("\tThis has already been submitted.")
				clist[0] = '*' + currentdaystr[:10]
				clist[currentm] = '*' + current
				currentm += 1
				current = clist[currentm]

				clistfile = open(PRINTFILE, "w")
				for item in clist:
					print(item, file=clistfile)
				print('Wrote file.')

		else:
			print('Weekend. Will not operate.')
		print('Next country: ' + str(currentm) + ', ' + current)

	else:
		print('The file is empty.')

	clistfile.close()

while True:
	try:
		scanSub()
	except Exception as e:
		print('There has been an error: ' + e)
	print('Running again in ' + WAITS + ' seconds.\n')
	time.sleep(WAIT)