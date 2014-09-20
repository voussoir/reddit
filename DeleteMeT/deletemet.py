#/u/GoldenSights
import praw
import time
import getpass
import datetime

print('Logging in to reddit')
print('Your password will be hidden while typing')
USERNAME = input('U: ')
PASSWORD = getpass.getpass('P: ')

USERAGENT = 'DeleteMe-Time tool written by /u/Goldensights, being used by /u/' + USERNAME + \
	'. Will pace through users comments and submissions, and delete those older than a certain Threshold. ' + \
	'The code for this tool can be found at https://github.com/voussoir/reddit/tree/master/DeleteMeT. ' + \
	'/u/Goldensights does not have any control over how the tool is being used.'
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)

def tprint(thing):
	#Having a whole bunch of text appear at once can be jarring
	print(thing)
	time.sleep(0.1)

def getTime(bool):
	timeNow = datetime.datetime.now(datetime.timezone.utc)
	timeUnix = timeNow.timestamp()
	if bool == False:
		return timeNow
	else:
		return timeUnix

def create():
	fail = False
	tprint('\nEnter a time threshold. Use a number followed by "days", "hours", or "minutes"')
	tprint('All submissions and comments older than this will be DELETED.')
	t = input('>> ').lower()
	tsplit = t.split()
	try:
		THRESHOLD = float(tsplit[0])
		if tsplit[1] not in ['days', 'day', 'hours', 'hour', 'minutes', 'minute']:
			print('You entered an improper time. "days", "hours", "minutes"')
			input()
			fail = True
	except ValueError:
		print('Could not understand that number')
		input()
		fail = True
	except IndexError:
		print('Please enter something.')
		input()
		fail = True

	if fail == False:
		if tsplit[1] == 'days' or tsplit[1] == 'day':
			THRESHOLD *= 86400
		elif tsplit[1] == 'hours' or tsplit[1] == 'hour':
			THRESHOLD *= 3600
		elif tsplit[1] == 'minutes' or tsplit[1] == 'minute':
			THRESHOLD *= 60

		tprint(t)
		tprint(str(THRESHOLD) + ' seconds.')
		tprint('Is this correct? Y/N')
		confirm = input('>> ').lower()
		if confirm == 'y':
			user = r.user
			
			deletion(user, THRESHOLD, lim=1000)

			tprint('\nWould you like this program to continue running?')
			tprint('Y/N')
			confirm = input('>> ').lower()
			if confirm == 'y':
				while True:
					deletion(user, THRESHOLD, lim=100)
					tprint('\nSleeping 60 seconds')
					time.sleep(60)


def deletion(user, THRESHOLD, lim=1000):
	allitems = []

	now = getTime(True)

	tprint('\nGathering submissions. Please be patient')
	allitems += list(user.get_submitted(limit=lim))

	tprint('Gathering comments. Please be patient')
	allitems += list(user.get_comments(limit=lim))

	allitems.sort(key=lambda x:x.created_utc)

	tprint('Found ' + str(len(allitems)) + ' total.')

	for item in allitems:
		diff = now - item.created_utc
		if diff > THRESHOLD:
			print('Deleting item ' + item.fullname + ' from ' + ("%0.0f" % diff) + ' seconds ago.')
			item.delete()
			time.sleep(2)
		else:
			tprint('Keeping item ' + item.fullname + ' from ' + ("%0.0f" % diff) + ' seconds ago.')


while True:
	create()