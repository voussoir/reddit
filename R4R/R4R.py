import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import os
import sys


'''USER CONFIGURATION'''
USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "penpals+dirtypenpals+kikpals+dirtykikpals+r4r+dirtyr4r+MakeNewFriendsHere"
SUBLIST = ['penpals','dirtypenpals','r4r','dirtyr4r','kikpals','dirtykikpals','makenewfriendshere','needafriend']
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
MAXPOSTS = 1000
#This is how many posts you want to retreieve all at once. PRAW will download 100 at a time.
WAIT = 600
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''



try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getu()
    PASSWORD = bot.getp()
    USERAGENT = bot.geta()
except ImportError:
    pass

WAITS = str(WAIT)
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

results = []

outputfile = open('results.txt','w')
    
def scanSub(listedsub):
    current = 0
    malePosts = 0
    maleComments = 0
    maleAverage = 0
    maleScore= 0
    maleScoreAverage = 0
    femalePosts = 0
    femaleComments = 0
    femaleAverage = 0
    femaleScore = 0
    femaleScoreAverage = 0

    print('\nScraping '+ listedsub + '.')
    subreddit = r.get_subreddit(listedsub)
    posts = subreddit.get_new(limit=MAXPOSTS)
    for post in posts:
        current += 1
        try:
            title = post.title.lower()
            if 'f4' in title or '/f/' in title:
                comments = post.comments
                femalePosts += 1
                c = len(comments)
                femaleComments += c
                s = post.score - 1
                femaleScore += s
                sr = post.subreddit.display_name
                rstring=str(current) + '\t' + '\t\tFemale \t\t' + str(femalePosts) + '\t\t' + str(c) + ' coms,\t' + str(femaleComments) + ' total. \t\t' + str(s) + ' points, ' + str(femaleScore) + ' total.\t' + sr
                print(rstring)
                print(rstring, file=outputfile)
    
            if 'm4' in title or '/m/' in title:
                comments = post.comments
                malePosts += 1
                c = len(comments)
                maleComments += c
                s = post.score - 1
                maleScore += s
                sr = post.subreddit.display_name
                rstring=str(current) + '\t' + '\t\tMale \t\t' + str(malePosts) + '\t\t' + str(c) + ' coms,\t' + str(maleComments) + ' total. \t\t' + str(s) + ' points, ' + str(maleScore) + ' total.\t' + sr
                print(rstring)
                print(rstring, file=outputfile)

                
        except:
            print(str(current) + ' had a problem.')
            pass
    print('-')
    try:
        maleAverage = '%.3f' % (maleComments / malePosts)
        maleScoreAverage = '%.3f' % (maleScore / malePosts)
    except ZeroDivisionError:
        maleAverage = 0
        maleScoreAverage = 0
    try:
        femaleAverage = '%.3f' % (femaleComments / femalePosts)
        femaleScoreAverage = '%.3f' % (femaleScore / femalePosts)
    except ZeroDivisionError:
        femaleAverage = 0
        femaleScoreAverage = 0

    rstring=listedsub + '\t' + str(malePosts) + ' male posts, \t' + str(maleComments) + ' comments total, ' + str(maleAverage) + ' average \t' + str(maleScore) + ' points total, ' + str(maleScoreAverage) + ' average'
    print(rstring)
    results.append(rstring)

    rstring=listedsub + '\t' + str(femalePosts) + ' female posts, \t' + str(femaleComments) + ' comments total, ' + str(femaleAverage) + ' average \t' + str(femaleScore) + ' points total, ' + str(femaleScoreAverage) + ' average'
    print(rstring)
    results.append(rstring)


for s in SUBLIST:
    scanSub(s)

print('\n')
for m in results:
    print(m)
    print(m,file=outputfile)

outputfile.close()