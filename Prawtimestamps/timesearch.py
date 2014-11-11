import praw
import time
import datetime

print('Connecting to reddit')
r = praw.Reddit('/u/GoldenSights automatic timestamp search program')

def get_all_posts(subreddit, lower=None, maxupper=None):
    subname = subreddit if type(subreddit)==str else subreddit.display_name
    if lower==None or maxupper==None:
        if isinstance(subreddit, praw.objects.Subreddit):
            creation = subreddit.created_utc
        else:
            subreddit = r.get_subreddit(subreddit)
            creation = subreddit.created_utc
    
        nowstamp = datetime.datetime.now(datetime.timezone.utc).timestamp()
        lower = creation
        maxupper = nowstamp
        
    interval = 86400
    upper = lower + interval


    allresults = []
    outfile = open('%s-%d-%d.txt'%(subname, lower, maxupper), 'w')
    try:
        while lower < maxupper:
            print('\nCurrent interval:', interval, 'seconds')
            print('Lower', datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(lower), "%b %d %Y %H:%M:%S"))
            print('Upper', datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(upper), "%b %d %Y %H:%M:%S"))
            timestamps = [lower, upper]
            searchresults = list(r.search('', subreddit=subreddit, sort='new', timestamps=timestamps))
            print([i.id for i in searchresults])
            allresults += searchresults
    
            print('Found', len(searchresults), ' items')
            if len(searchresults) < 5:
                print('Too few results, doubling interval')
                interval *= 2


            if len(searchresults) > 22:
                print('Too many results, halving interval')
                interval /= 2
                upper = lower + interval

            else:
                lower = upper
                upper = lower + interval
    
        print('Finished with', len(allresults), 'items')
    except Exception as e:
        print("ERROR:", e)
        print('File will be printed and list returned')

    outlist = []
    for item in allresults:
        if item not in outlist:
            outlist.append(item)
    print("Removed", len(allresults) - len(outlist), "duplicates")
    print('Finished with', len(outlist), 'items')
    outlist.sort(key=lambda x: x.created_utc)
    outtofile(outlist, outfile)
    return outlist

def outtofile(outlist, outfile):
    pos = 0
    for o in outlist:
        try:
            author = o.author.name
        except AttributeError:
            author = "[deleted]"
        itemtime = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(o.created_utc), "%b %d %Y %H:%M:%S")
        print('[' + str(pos) + ':' + o.id, itemtime + ' - ' + author + ' - ' + o.title + '](http://redd.it/'+o.id + ')  ', file=outfile)
        pos += 1
    outfile.close()


print("Get posts from subreddit: /r/", end='')
sub = input()
print('Lower bound (Leave blank to get ALL POSTS)\n]: ', end='')
lower  = input()
if lower == '':
    get_all_posts(sub)
else:
    print('Maximum upper bound\n]: ', end='')
    maxupper = input()
    try:
        int(maxupper)
        int(lower)
    except ValueError:
        print("lower and upper bounds must be unix timestamps")
        input()
input()