#/u/GoldenSights
import traceback
import praw
import time
import sqlite3



USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
try:
	import bot 
	# This is a file in my python library which contains my
	# Bot's username and password.
	# I can push code to Git without showing credentials
	USERNAME = bot.uG
	PASSWORD = bot.pG
	USERAGENT = bot.aG
except ImportError:
	pass


class ReplyBot():
	def __init__(self, r, username, databasename='replybot.db'):
		self.r = r
		self.USERNAME = username

		self.SUBREDDIT = "GoldTesting"
		#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
		self.KEYWORDS = ["phrase 1", "phrase 2", "phrase 3", "phrase 4"]
		#These are the words you are looking for
		self.KEYAUTHORS = ["GoldenSights"]
		# These are the names of the authors you are looking for
		# Any authors not on this list will not be replied to.
		# Make empty to allow anybody
		self.REPLYSTRING = "Hi hungry, I'm dad."
		#This is the word you want to put in reply
		self.MAXPOSTS = 100
		#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
		self.WAIT = 20
		#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

		self.sql = sqlite3.connect(databasename)
		print('Loaded SQL Database: %s' % databasename)
		self.cur = self.sql.cursor()
		
		self.cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')
		self.cur.execute('CREATE INDEX IF NOT EXISTS index_oldposts on oldposts(id)')
		
		self.sql.commit()

	def replybot(self):
		print('Searching %s.' % self.SUBREDDIT)
		subreddit = r.get_subreddit(self.SUBREDDIT)
		posts = subreddit.get_comments(limit=self.MAXPOSTS)
		for post in posts:
			# Anything that needs to happen every loop goes here.
			pid = post.id

			try:
				pauthor = post.author.name
			except AttributeError:
				# Author is deleted and we don't care about this post
				continue

			self.cur.execute('SELECT * FROM oldposts WHERE id=?', [pid])
			if self.cur.fetchone():
				# Post is already in the database
				continue
			self.cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
			self.sql.commit()

			if self.KEYAUTHORS != [] and all(auth.lower() != pauthor.lower() for auth in self.KEYAUTHORS):
				# This post was not made by a keyauthor
				continue


			pbody = post.body.lower()
			if any(key.lower() in pbody for key in self.KEYWORDS):
				if pauthor.lower() == self.USERNAME.lower():
					print('%s: Will not reply to myself' % pid)
					continue
				print('Replying to %s by %s' % (pid, pauthor))
				post.reply(self.REPLYSTRING)

	def looponce(self):
		try:
			self.replybot()
		except Exception as e:
			traceback.print_exc()
		print('Running again in %d seconds \n' % self.WAIT)
		time.sleep(self.WAIT)

	def loopwhile(self):
		while True:
			self.looponce()

if __name__ == '__main__':
	print('Logging into reddit')
	r = praw.Reddit(USERAGENT)
	r.login(USERNAME, PASSWORD)
	replybot = ReplyBot(r, username=USERNAME)
	replybot.loopwhile()