#/u/GoldenSights
import praw
import time
import sqlite3


sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS users(NAME TEXT, COMMENTS INT, SUBMISSIONS INT, RATIO REAL)')
print('Loaded Completed table')
sql.commit()



print("Forcibly change a user's information")
def operate():
	username = input('/u/').lower()
	cur.execute('SELECT * FROM users WHERE lower(NAME)=?', [username.lower()])
	f = cur.fetchone()
	if not f:
		print('That user does not exist in the database')
	else:
		print(f[0] + ': ' +  str(f[1]) + ' comments, ' + str(f[2]) + ' submissions')
		print("Forcibly changing /u/" + username + "'s information. Is this correct? Y/N")
		confirm = input('>> ').lower()
		if confirm == 'y':
			name = f[0]
			comments = int(input('Comments: '))
			submissions = int(input('Submissions: '))
			denominator = (1 if submissions == 0 else submissions)
			ratio = "%0.2f" % (comments / denominator)
			print('Ratio: ' + ratio)
			ratio = float(ratio)
			cur.execute('UPDATE users SET COMMENTS=?, SUBMISSIONS=?, RATIO=? WHERE NAME=?', [comments, submissions, ratio, name])
			sql.commit()
			print('Success')


while True:
	operate()
	print()