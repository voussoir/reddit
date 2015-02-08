import traceback
import praw
import time
import datetime

print('Connecting to reddit')
r = praw.Reddit('/u/GoldenSights automatic timestamp search program')

def get_all_posts(subreddit, lower=None, maxupper=None, interval=86400):
    offset = -time.timezone
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
        
    outfile = open('%s-%d-%d.txt'%(subname, lower, maxupper), 'w', encoding='utf-8')
    #lower -= offset
    maxupper -= offset
    cutlower = lower
    cutupper = maxupper
    upper = lower + interval

    allresults = []
    try:
        while lower < maxupper:
            print('\nCurrent interval:', interval, 'seconds')
            print('Lower', datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(lower), "%b %d %Y %H:%M:%S"), lower)
            print('Upper', datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(upper), "%b %d %Y %H:%M:%S"), upper)
            timestamps = [lower, upper]
            while True:
                try:
                    searchresults = list(r.search('', subreddit=subreddit, sort='new', timestamps=timestamps))
                    break
                except:
                    traceback.print_exc()
                    print('resuming in 5...')
                    time.sleep(5)
            print([i.id for i in searchresults])
            allresults += searchresults
    
            print('Found', len(searchresults), ' items')
            if len(searchresults) < 5:
                print('Too few results, doubling interval', end='')
                interval *= 2


            if len(searchresults) > 23:
                print('Too many results, halving interval', end='')
                interval /= 2
                upper = lower + interval

            else:
                lower = upper
                upper = lower + interval
            print()
    
        print('Collected', len(allresults), 'items')
        print('Please wait...')
    except Exception as e:
        print("ERROR:", e)
        print('File will be printed and list returned')

    outlist = []
    for item in allresults:
        if item not in outlist:
            if item.created_utc >= cutlower and item.created_utc <= cutupper:
                outlist.append(item)
            else:
                print(item.created_utc, cutlower)
    print("Removed", len(allresults) - len(outlist), "bad items.")
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
        outstr = '[%d: %s %s - %s - %s](http://redd.it/%s)  \n' % (pos, o.id, itemtime, author, o.title, o.id)
        outfile.write(outstr)
        pos += 1
    outfile.close()

print("Get posts from subreddit: /r/", end='')
sub = input()
print('Lower bound (Leave blank to get ALL POSTS)\n]: ', end='')
lower  = input()
if lower == '':
    x = get_all_posts(sub)
else:
    print('Maximum upper bound\n]: ', end='')
    maxupper = input()
    print('Starting interval (Leave blank for standard)\n]: ', end='')
    interval = input()
    if interval == '':
        interval = 84600
    try:
        maxupper = int(maxupper)
        lower = int(lower)
        interval = int(interval)
        x = get_all_posts(sub, lower, maxupper, interval)
    except ValueError:
        print("lower and upper bounds must be unix timestamps")
        input()
print("Done. Press Enter to close window")
input()