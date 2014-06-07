#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import random


'''USER CONFIGURATION'''
USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot".
SUBREDDIT = "reddithitman"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."


'''All done!'''







try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getu()
    PASSWORD = bot.getp()
    USERAGENT = bot.geta()
except ImportError:
    pass


r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 


def scanThread():
    users = []
    try:
        url=input('URL: ')
    except EOFError:
        url = ''
        print('')
    urlsplit = url.split('/')
    for m in range(len(urlsplit)):
        if urlsplit[m] == 'comments' or urlsplit[m] == 'redd.it':
            idd = urlsplit[m+1]
    if idd != None:
        post = r.get_submission(submission_id=idd)
        perma = post.short_link
        comments = post.comments
        for comment in comments:
            if comment.is_root and comment.author.name not in users:
                users.append(comment.author.name)
                print(comment.author.name + ' has joined.')
        usercount = len(users)
        print('\nThe game has ' + str(usercount) + ' players.\n')
        random.shuffle(users)
        for m in range(usercount):
            try:
                player = users[m]
                target = users[m+1]
            except IndexError:
                player = users[m]
                target = users[0]
            print(player + "'s target is " + target)
            r.send_message(player, 'Your /r/RedditHitman registration', 'You have registered for a game of RedditHitman by entering a top-level comment [here](' + perma + ')\n\nYour target is /u/' + target + '!')

scanThread()