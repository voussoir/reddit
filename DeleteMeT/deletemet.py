#/u/GoldenSights
import praw
import time
import getpass
import datetime

USERAGENT = ""
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/

print('Logging in to reddit')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

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