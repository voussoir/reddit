#/u/Goldensights

import praw
import time
import sqlite3
import datetime

'''USER CONFIG'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
MAXPOSTS = 2000
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 30
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
VERBOSE = False
#IF Verbose is set to true, the console will spit out a lot more information. Use True or False (Use capitals! No quotations!)
PRINTFILE = 'messages.txt'
#This is the file, in the same directory as the .py file, where the messages are stored
ITEMTYPE = 't4'
#The type of item to gather. t4 is a PM
'''All done!'''



clistfile = open(PRINTFILE, "a+")
clistfile.close()
#This is a hackjob way of creating the file if it does not exist

WAITS = str(WAIT)
try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getuG()
    PASSWORD = bot.getpG()
    USERAGENT = bot.getaG()
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded Completed table')

sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)

def scanInbox():
	print('Scanning Received')
	inbox = r.get_inbox(limit=MAXPOSTS)
	listo = []
	for item in inbox:
		iid = item.fullname
		cur.execute('SELECT * FROM oldposts WHERE id=?', [iid])
		if not cur.fetchone():
			if ITEMTYPE in iid:
				print('\tIn ' + iid)
				listo.append(item)
			cur.execute('INSERT INTO oldposts VALUES(?)', [iid])
	sql.commit()
	return listo

def scanSent():
	print('Scanning Sent')
	sent = r.get_sent(limit=MAXPOSTS)
	listo = []
	for item in sent:
		iid = item.fullname
		cur.execute('SELECT * FROM oldposts WHERE id=?', [iid])
		if not cur.fetchone():
			if ITEMTYPE in iid:
				print('\tOut ' + iid)
				listo.append(item)
			cur.execute('INSERT INTO oldposts VALUES(?)', [iid])
	sql.commit()
	return listo


def work():

	listi = scanInbox()
	listo = scanSent()
	lista = listi + listo
	lista.sort(key=lambda x: x.created_utc, reverse=False)
	mcur = 0
	mlen = len(lista)
	for item in lista:
		mcur += 1
		messagefile = open(PRINTFILE, 'r+')
		messagelist = []
		for line in messagefile:
			messagelist.append(line.strip())
		messagefile.close()
		messagefile = open(PRINTFILE, 'w')
		print(("%06d" % mcur) + '/' + ("%06d" % mlen) + ': Writing item ' + item.id, end='')
		try:
			try:
				pauthor = item.author.name
			except Exception:
				pauthor = '[DELETED]'
			if item.parent_id == None:
				print(' <= Root')
				messagelist.append('======================================================')
				messagelist.append(item.id)
				messagelist.append(datetime.datetime.fromtimestamp(int(item.created_utc)).strftime("%B %d %Y %H:%M UTC"))
				if pauthor.lower() == USERNAME.lower():
					messagelist.append('To ' + item.dest)
				else:
					messagelist.append('From ' + pauthor)
				messagelist.append('Subject: ' + item.subject)
				messagelist.append(item.body.replace('\n', '//'))
	
			else:
				print()
				for m in range(len(messagelist)):
					if item.parent_id[3:] in messagelist[m]:
	
						count = '| '
						tline = messagelist[m]
						while tline[:2] == '| ':
							count += '| '
							tline = tline[2:]
	
						messagelist[m+4] += '\n\n' + count + item.id + '\n'
						messagelist[m+4] += count + datetime.datetime.fromtimestamp(int(item.created_utc)).strftime("%B %d %Y %H:%M UTC") + '\n' + count
						if pauthor.lower() == USERNAME.lower():
							messagelist[m+4] += 'To ' + item.dest + '\n'
						else:
							messagelist[m+4] +='From ' + pauthor + '\n'
						messagelist[m+4] += count + 'Subject: ' + item.subject + '\n'
						messagelist[m+4] += count + item.body.replace('\n', '//')
		except Exception:
			print("Emergency save!")
			for m in messagelist:
				print(m, file=messagefile)
				messagefile.close()
				time.sleep(0.1)


		for m in messagelist:
			print(m, file=messagefile)
		messagefile.close()
		time.sleep(0.1)



while True:
    try:
        work()
    except Exception as e:
        print('An error has occured:', str(e))
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)