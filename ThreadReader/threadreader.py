import praw
import textwrap
import time
import datetime


FALLBACKID = ''
try:
    pid=input('Thread ID: ')
except EOFError:
    if FALLBACKID == '':
        print('\nCannot run in this environment. Your device is not accepting input')
        print('You may run this program another way, or edit the FALLBACKID variable with the ID')
        time.sleep(999999)
    else:
        pid = FALLBACKID

print('Connecting to reddit')
r=praw.Reddit('/u/GoldenSights ThreadReader script. Downloads a comment thread and prints it to a txt file\
    Learn more at https://github.com/voussoir/reddit/tree/master/ThreadReader')

print('Getting post')
post = r.get_info(thing_id='t3_' + pid)
print('Getting all comments')
post.replace_more_comments(limit=None, threshold=1)
comments = post.comments

print('Creating file')
outfile = open('t3_' + pid + '.txt', 'w')

print('/r/' + post.subreddit.display_name, file=outfile)
print(post.title + '\n', file=outfile)

if post.selftext != "":
    pbody = post.selftext.replace('\n\n', '\n')
    pfinal = ''
    for paragraph in pbody.split('\n'):
        pfinal += '\n'.join(textwrap.wrap(paragraph))
        pfinal += '\n'    
    print(pfinal, file=outfile)
print(post.permalink + '\n\n\n', file=outfile)

DEPTHSYMBOL = "    "

def recursivereplies(inlist, depth):
    for reply in inlist:
        print(' ', file=outfile)
        try:
            cauthor = reply.author.name
        except AttributeError:
            cauthor = "[DELETED]"
        print(DEPTHSYMBOL * depth + '/u/' + cauthor + ', ' + reply.id + ', ' + humanize(reply.created_utc), file=outfile)
        cbody = reply.body
        cbody = DEPTHSYMBOL*depth + cbody
        cbody = cbody.replace('\n\n', '\n')
        cfinal = ''
        for paragraph in cbody.split('\n'):
            cfinal += ('\n').join(textwrap.wrap(paragraph))
            cfinal += '\n'
        cfinal = cfinal[:-1]

        cfinal = cfinal.replace('\n', '\n' + DEPTHSYMBOL*depth)
        print(cfinal, file=outfile)
        recursivereplies(reply.replies, depth+1)


def humanize(instamp):
    date = datetime.datetime.utcfromtimestamp(instamp)
    date = datetime.datetime.strftime(date, "%b %d %Y %H:%M:%S UTC")
    return date



for comment in comments:
    try:
        cauthor = comment.author.name
    except AttributeError:
        cauthor = "[DELETED]"
    print('/u/' + cauthor + ', ' + comment.id + ', ' + humanize(comment.created_utc), file=outfile)
    cbody = comment.body
    cbody = cbody.replace('\n\n', '\n')
    cbody = '\n'.join(textwrap.wrap(cbody))
    print(cbody, file=outfile)
    recursivereplies(comment.replies, 1)
    print('*'*50, file=outfile)


outfile.close()
print('Done')
input()