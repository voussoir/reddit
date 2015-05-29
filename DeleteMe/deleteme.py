#/u/GoldenSights
import praw
import time
import getpass

print('Logging in to reddit')
print('Your password will be hidden while typing')
USERNAME = input('U: ')
PASSWORD = getpass.getpass('P: ')

USERAGENT = 'DeleteMe tool written by /u/Goldensights, being used by /u/' + USERNAME + \
	'. Will pace through users comments and submissions, and delete those below a certain score threshold. ' + \
	'The code for this tool can be found at https://github.com/voussoir/reddit/tree/master/DeleteMe. ' + \
	'/u/Goldensights does not have any control over how the tool is being used.'
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)

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