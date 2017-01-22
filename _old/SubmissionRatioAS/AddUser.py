#/u/GoldenSights
import praw
import time
import sqlite3

'''USER CONFIGURATION'''
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "goldtesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
'''All done!'''




submissions = 0
comments = 0


try:
	import bot
	USERAGENT = bot.aG
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS users(NAME TEXT, COMMENTS INT, SUBMISSIONS INT, RATIO REAL, FLAIR TEXT)')
print('Loaded Completed table')
sql.commit()

r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)


def work(l, user):
	global submissions
	global comments
	m=0
	added = 0
	for post in l:
		cur.execute('SELECT * FROM oldposts WHERE ID=?', [post.fullname])
		if not cur.fetchone():
			try:
				pauthor = post.author.name
				if post.subreddit.display_name.lower() == SUBREDDIT.lower() and pauthor.lower() == user.name.lower():
					if type(post) == praw.objects.Comment:
						comments += 1
						added += 1
					if type(post) == praw.objects.Submission:
						submissions += 1
						added += 1
			except:
				pass
			cur.execute('INSERT INTO oldposts VALUES(?)', [post.fullname])
		m+=1
		print('\r' + str(m) + '\t' + str(added), end='')
	print()


def operate():
	global submissions
	global comments

	submissions = 0
	comments = 0

	print('Subreddit: ' + SUBREDDIT)
	print("Add a user's information to the database")
	username = input('/u/')
	print("Adding /u/" + username + ". Is this correct? Y/N")
	confirm = input('>> ').lower()
	if confirm == 'y':
		subreddit = r.get_subreddit(SUBREDDIT)
		userflair = subreddit.get_flair(username)['flair_text']
		if userflair != '' and userflair is not None:
			try:
				user = r.get_redditor(username, fetch=True)
				cur.execute('SELECT * FROM users WHERE NAME=?', [user.name])
				fetched = cur.fetchone()
				if not fetched:
					print('New user')
					cur.execute('INSERT INTO users VALUES(?, ?, ?, ?, ?)', [user.name, 0, 0, 0, userflair])
					fetched = [user.name, 0, 0, 0]

				comments = fetched[1]
				submissions = fetched[2]


				print('Gathering /new')
				new = subreddit.get_new(limit=1000)
				work(new, user)

				print('Gathering /comments')
				coms = subreddit.get_comments(limit=1000)
				work(coms, user)

				print('Gathering user submissions')
				submitted = user.get_submitted(limit=1000)
				work(submitted, user)

				print('Gathering user comments')
				coms = user.get_comments(limit=1000)
				work(coms, user)

				denominator = (1 if submissions == 0 else submissions)
				ratio = "%0.2f" % (comments / denominator)
				print('\t' + user.name)
				print('\t' + str(comments) + 'c / ' + str(denominator) + 's = ' + str((comments / denominator))[:3])
				ratio = float(ratio)
				cur.execute('UPDATE users SET COMMENTS=?, SUBMISSIONS=?, RATIO=?, FLAIR=? WHERE NAME=?', [comments, submissions, ratio, userflair, user.name])

			except praw.requests.exceptions.HTTPError:
				print('Could not fetch user')
		else:
			print('User has no flair')

	sql.commit()


while True:
	operate()
	print()