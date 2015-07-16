#/u/GoldenSights
import traceback
import praw
import getpass

""" USER CONFIGURATION """

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter Bot".

SUBREDDIT = input("Subreddit: /r/")
FILENAME = input('File: ')
# You can replace these with strings if you want it hardcoded.

""" That's all! """

try:
    import bot
    USERAGENT = bot.aG
except ImportError:
    pass

print('Logging in...')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def contributorfile():
	subreddit = r.get_subreddit(SUBREDDIT)
	print("Finding existing contributors...")
	contributors = subreddit.get_contributors(limit=None)
	contributors = list(contributors)
	for x in range(len(contributors)):
		contributors[x] = contributors[x].name.lower()
	print("Reading file...")
	contributorfile = open(FILENAME)
	names = []
	for line in contributorfile:
		if line[0] != "#":
			line = line.strip()
			line = line.replace('/u/', '')
			names.append(line.lower())
	names = set(names)
	duplicates = True
	while duplicates:
		duplicates = False
		for username in names:
			if username in contributors:
				print(username + " is already a contributor")
				names.remove(username)
				duplicates = True
				break

	for username in names:
		print("Adding " + username)
		try:
			subreddit.add_contributor(username)
		except:
			traceback.print_exc()
	print('Finished.')
	input()


contributorfile()