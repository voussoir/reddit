#/u/GoldenSights
import praw
import time
import getpass

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
	# Slows down the printouts
	print(thing)
	time.sleep(0.1)

def create():
	tprint('\nEnter a score threshold. All comments and submissions below will be deleted')
	THRESHOLD = int(input('>> '))
	tprint('\nDeleting all comments and submissions with a score less than ' + str(THRESHOLD) + '.')
	tprint('Is this correct? Y/N')
	confirm = input('>> ').lower()
	if confirm == 'y':
		user = r.user

		deletion(user, THRESHOLD)

		tprint('\nWould you like this program to continue running?')
		tprint('Y/N')
		confirm = input('>> ').lower()
		if confirm == 'y':
			while True:
				deletion(user, THRESHOLD)
				tprint('\nSleeping 120 seconds')
				time.sleep(120)

def deletion(user, THRESHOLD):
	tprint('\nGathering submissions. Please be patient')
	submitted = list(user.get_submitted(limit=1000))
	tprint('Found ' + str(len(submitted)) + ' total.')
	for item in submitted:
		if item.score < THRESHOLD:
			print('Deleting item ' + item.fullname + ' with score ' + str(item.score))
			item.delete()
			time.sleep(2)
		else:
			tprint('Keeping item ' + item.fullname + ' with score ' + str(item.score))

	tprint('\nGathering comments. Please be patient')
	comments = list(user.get_comments(limit=1000))
	tprint('Found ' + str(len(comments)) + ' total.')
	for item in comments:
		if item.score < THRESHOLD:
			print('Deleting item ' + item.fullname + ' with score ' + str(item.score))
			item.delete()
			time.sleep(2)
		else:
			tprint('Keeping item ' + item.fullname + ' with score ' + str(item.score))

while True:
	create()