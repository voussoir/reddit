import praw
import datetime

USERAGENT = "/u/Goldensights TimeInspector script. Scanning user's comments and submissions to determine their posting habits"
MAXPOSTS  = 1000

r = praw.Reddit(USERAGENT)

def start():
	lista=[]
	print('Who would you like to scan?')
	username = input('/u/')
	print('\n/u/' + username + '. Is this correct? y/n')
	if input('>').lower() == 'y':
		print('Fetching ' + username)
		redditor = r.get_redditor(username)
		m = 0
		submitted = redditor.get_submitted(limit=MAXPOSTS)
		for item in submitted:
			lista.append(item)
			m+=1
			print('\r%04d' % m + ' Submissions',end='')
		m=0
		print()
		comments = redditor.get_comments(limit=MAXPOSTS)
		for item in comments:
			lista.append(item)
			m+=1
			print('\r%04d' % m + ' Comments',end='')
		print()

		print('Sorting list')
		lista.sort(key=lambda x: x.created_utc, reverse=False)

		print('Creating files')
		userfile = open(username + '.txt', 'w')
		userfileb= open(username + '_tunix.txt', 'w')
		userfilec= open(username + '_thuman.txt', 'w')

		print('Writing files')
		for item in lista:
			dtime = datetime.datetime.utcfromtimestamp(item.created_utc)
			readable = datetime.datetime.strftime(dtime, "%B %d %Y %H:%M:%S")
			print(item.fullname + '\t' + str(item.created_utc) + '\t' + readable + ' UTC', file=userfile)
			print(str(item.created_utc), file=userfileb)
			print(readable, file=userfilec)

		userfile.close()
		userfileb.close()
		userfilec.close()
		print('Finished! Press Enter to play again\n\n')
		input()
	else:
		print()


while True:
	start()