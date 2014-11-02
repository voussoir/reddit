#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import datetime
import sys

'''USER CONFIGURATION'''

USERNAME = ""
PASSWORD = ""
USERAGENT = ""
#This is a short description of what the bot is doing

FILE = "imaginary.txt"
#Your network

POSTTOSUBREDDIT = ""
#This is the subreddit the table will be posted to
#Fill here to make it automatic
#Leave blank to be prompted at run time

'''ALL DONE!'''


try:
	import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
	USERNAME = bot.uG
	PASSWORD = bot.pG
	USERAGENT = bot.aG
except ImportError:
    pass

print('Logging in')
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)

def getTime(bool):
	timeNow = datetime.datetime.now(datetime.timezone.utc)
	timeUnix = timeNow.timestamp()
	if bool == False:
		return timeNow
	else:
		return timeUnix

def linesfromfile(filename):
	try:
		with open(filename, 'r') as filea:
			lines = filea.read()
		lines = lines.split('\n')
		while '' in lines:
			lines.remove('')
		return lines
	except:
		filea = open(filename, 'w')
		filea.close()
		print('File ' + filename + ' was not found and has been created')
		return []

def listtofile(inputlist, filename):
	with open(filename, 'w') as filea:
		for item in inputlist:
			print(item, file=filea)

def operate():
	userinput = input('> ')
	userinput = userinput.lower()
	userinput = userinput.split()
	if userinput[0] == 'add':
		try:
			sub = userinput[1]
			try:
				sub = sub.replace('/r/', '')
				filelines = linesfromfile(FILE)
				if not any(sub == subname.lower() for subname in filelines):
					subreddit = r.get_subreddit(sub, fetch=True)
					filelines.append(sub)
					listtofile(filelines, FILE)
					print('Added ' + sub + ' and saved file.')
				else:
					print(sub + ' is already in the list')
			except praw.requests.exceptions.HTTPError:
				print('Could not fetch subreddit ' + sub)
		except IndexError:
			print('Command syntax incorrect. Ex:')
			print('add botwatch')


	elif userinput[0] == 'drop':
		try:
			sub = userinput[1]
			sub = sub.replace('/r/', '')
			filelines = linesfromfile(FILE)
			found = False
			for subname in filelines:
				if subname.lower() == sub:
					found = True
					filelines.remove(subname)
					listtofile(filelines, FILE)
					print('Dropped ' + subname + ' and saved file')
			if not found:
				print(sub + ' is not in the file')
		except IndexError:
			print('Command syntax incorrect. Ex:')
			print('drop botwatch')

	elif userinput[0] == 'start':
		now = getTime(False)
		nowshort = datetime.datetime.strftime(now, "%d%b%Y-%H-%M-%S")
		now = datetime.datetime.strftime(now, "%B %d %Y, %H:%M:%S UTC")
		subreddits = []
		filelines = linesfromfile(FILE)
		print('Found ' + str(len(filelines)) + ' subreddits in file ' + FILE)
		totalsubs = 0
		pos = 1
		for sub in filelines:
			print(sub + ': ', end='')
			sys.stdout.flush()
			subreddit = r.get_subreddit(sub)
			subname = subreddit.url[3:-1]
			subscribers = str(subreddit.subscribers)
			print('\r' + subname + ': ' + subscribers)
			#This is done to maintain perfect casing
			#Praw returns display_name as whatever is inputted, 
			#which may not be the right casing
			subreddits.append([subname, subscribers])
		print('Sorting subreddits')
		subreddits.sort(key=lambda x:int(x[1]))
		subreddits.reverse()
		output = []
		output.append(now + '\n')
		output.append('Rank | Subreddit | Subscribers')
		output.append('-: | :- | -:')
		pos = 1
		for sub in subreddits:
			output.append(str(pos) + ' | /r/' + sub[0] + ' | ' + sub[1])
			pos += 1
		outputstr = '\n'.join(output)
		filea = open(nowshort+'.txt', 'w')
		print(outputstr, file=filea)
		filea.close()
		print('Output file created')
		if POSTTOSUBREDDIT == "":
			posttosubreddit = input('Post to subreddit: /r/')
		else:
			posttosubreddit = POSTTOSUBREDDIT
		print('Posting to ' + POSTTOSUBREDDIT)
		r.submit(posttosubreddit, "State Of The Network " + now, text=outputstr)
		print('Finished')
	print()

print('Using file: ' + FILE)
print('Commands:')
print('\tadd subreddit')
print('\tdrop subreddit')
print('\tstart')
while True:
	operate()