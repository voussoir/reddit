#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import bot
from tkinter import Tk
import random

'''USER CONFIGURATION'''

USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
PRINTFILE = "result.txt"
#This is the file where the results will go. In the same folder as this py file

'''All done!'''



try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    #USERNAME = bot.getu()
    #PASSWORD = bot.getp()
    USERAGENT = bot.getaG()
except ImportError:
    pass


r = praw.Reddit(USERAGENT)

printfile = open(PRINTFILE, 'a+')
printfile.close()
#Hackjob method of creating file if it does not exist.

print('Permalink to thread\nLeave empty to paste from clipboard')
i = input('>')
pid = ''
if i == '':
    t = Tk()
    t.withdraw()
    link = t.selection_get(selection = "CLIPBOARD")
elif len(i) == 6:
    pid = i
    link = ''
else:
    link = i
if 'www.reddit.com/r/' in link and '/comments/' in link:
    pid = link.split('/comments/')[1].split('/')[0]
if 'http://redd.it/' in link:
    pid = link.split('redd.it/')[1]
print('\nThread ID: ' + pid)
print('Grabbing Thread')
try:
    post = r.get_info(thing_id='t3_' + pid)
    print('Pulling Root comments.')
    post.replace_more_comments(limit=None, threshold=0)
    comments = praw.helpers.flatten_tree(post.comments)
except:
    print('[ERR] Failed')
    input()
    quit()
clist = []
nlist = []
for comment in comments:
    if comment.is_root:
        try:
            author = comment.author.name
            if author not in nlist:
                nlist.append(author)
                clist.append(comment)
        except:
            pass
print('Sorting.')
clist.sort(key=lambda x: x.created_utc)
printfile = open(PRINTFILE, 'w')
m = 1
rand = random.randint(1,len(clist))
print('Thread: ' + pid + '\n\n' + str(len(clist)) + ' comments\n\nRandom Number: ' + str(rand) + ' : ' + clist[rand-1].author.name + '\n', file=printfile)
for name in clist:
    print(str(m) + ' : ' + name.author.name, file=printfile)
    m+=1
printfile.close()
print('Done.')
input()