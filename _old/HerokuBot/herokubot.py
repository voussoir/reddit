import praw
import time

print('Logging in.')
r = praw.Reddit('Testing praw api usage over Heroku')
r.login('qQGusVuAHezHxhYTiYGm', 'qQGusVuAHezHxhYTiYGm')

print('Getting subreddit info.')
sub = r.get_subreddit('Goldtesting')
print('/r/Goldtesting')
print('\tCreated at: %d' % sub.created_utc)
print('\tSubscribers: %d' % sub.subscribers)

print('All done!')
while True:
	time.sleep(60)