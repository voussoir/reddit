#/u/GoldenSights
import traceback
import praw
import time

'''USER CONFIGURATION'''

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does.
#For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub for which flair will be distributed.
#Must only be a single subreddit
WAIT = 30
#This is how many seconds you will wait between cycles.
#The bot is completely inactive during this time.

SUBJECTLINE = ["flair", "re: flair"]
#This is the text that must match the message subject for the bot to take
#action. Leave this emtpy [] if you want to act on *any* mail.
CHARACTER_MAX = 48
#The maximum number of characters the user can have in his flair
#THE REDDIT MAXIMUM IS 64. ANY NUMBER HIGHER THAN 64 IS USELESS.
MESSAGE_SUCCESS = """
Your flair has been set to

    _newflair_
"""
#This is what the bot will send back to the user when the flair is successful
#You can include "_newflair_" to have the message include the flair. Optional.
MESSAGE_TOOLONG = """
That flair is too long. It contains {length}/{maximum} characters. This
maximum is enforced by the moderators.
"""
MESSAGE_TOOLONG_SITE = """
That flair is too long. It contains {length}/64 characters. This maximum is
enforced by reddit site-wide.
"""

''' All done! '''


try:
    import bot
    USERAGENT = bot.aG
except ImportError:
    pass

print('Logging in...')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def flairmail():
	print('Getting unread messages')
	unreads = list(r.get_unread(limit=None))
	for message in unreads:
		try:
			mauthor = message.author.name
			msubject = message.subject.lower()
			mbody = message.body
			mlength = len(mbody)
			if any(trigger.lower() == msubject for trigger in SUBJECTLINE) or SUBJECTLINE==[]:
				print('%s has requested flair: %s' % (mauthor, mbody))

				if mlength > 64:
					print('\tFlair is too long, sitewide')
					message.reply(MESSAGE_TOOLONG_SITE.format(length=mlength))
				elif mlength > CHARACTER_MAX:
					print('\tFlair is too long, modrules')
					message.reply(MESSAGE_TOOLONG.format(length=mlength, maximum=CHARACTER_MAX))
				else:
					print('\tSetting flair')
					mbody = mbody.replace('\n', '')
					r.set_flair(SUBREDDIT, mauthor, mbody)
					reply = MESSAGE_SUCCESS
					reply = reply.replace("_newflair_", mbody)
					print('\tWriting reply')
					message.reply(reply)

				message.mark_as_read()
		except AttributeError:
			# Author does not exist
			# Or this is a comment
			pass

while True:
	flairmail()
	print('Sleeping %d seconds...\n' % WAIT)
	time.sleep(WAIT)