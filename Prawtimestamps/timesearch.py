import urllib.request
import json
import time
import praw
import sys
import datetime
import bot


print('Starting r')
r = bot.rG()

def timesearch(lower, upper, subreddit):
    url = 'http://api.reddit.com/r/' + subreddit + '/search?sort=new&q=timestamp%3A' + str(lower) + '..' + str(upper) +'&restrict_sr=on&syntax=cloudsearch'
    print(url)
    web = urllib.request.urlopen(url)
    webresponse = web.read()
    webresponse = webresponse.decode('utf-8', 'ignore')
    js = json.loads(webresponse)
    print(js)
    results = []
    for postjson in js['data']['children']:
        postdata = postjson['data']
        print(postdata)
        results.append(postdata)
    return results

dtformat = "%d %B %Y %H:%M UTC"
def get_all_posts(subredditname, intt):
    interval = intt
    now = datetime.datetime.now(datetime.timezone.utc).timestamp() 
    print('Now: ' + str(now))
    subreddit = r.get_subreddit(subredditname)
    screated = subreddit.created_utc
    stime = datetime.datetime.utcfromtimestamp(screated)
    stime = datetime.datetime.strftime(stime, dtformat)
    print('/r/' + subredditname)
    print('Created: ' + str(screated) + ', ' + stime)

    lowerbound = screated
    upperbound = lowerbound + interval

    results = []
    print('Interval: ' + str(interval) + ' seconds')
    while lowerbound < now:
        lowerbound = int(lowerbound)
        upperbound = int(upperbound)
        #I was having float problems earlier.

        lowert = datetime.datetime.utcfromtimestamp(lowerbound)
        uppert = datetime.datetime.utcfromtimestamp(upperbound)
        print("Lower: " + str(lowerbound) + ", " + datetime.datetime.strftime(lowert, dtformat))
        print("Upper: " + str(upperbound) + ", " + datetime.datetime.strftime(uppert, dtformat))
        try:
            moreresults = timesearch(lowerbound, upperbound, subredditname)
            moreresults.sort(key=lambda x:x['created_utc'])
            results += moreresults

            if len(moreresults) < 5:
                interval *= 2
                print('Doubling interval to ' + str(interval))
                lowerbound = upperbound
                upperbound = lowerbound + interval

            elif len(moreresults) >= 24:
                interval /= 2
                print('Halving interval to ' + str(interval))
                lowerbound = results[-1]['created_utc']
                upperbound = lowerbound + interval
                print('Resetting bounds to ' + str(lowerbound) + ', ' + str(upperbound))

            else:
                lowerbound += interval
                upperbound += interval

            print("Items this round: " + str(len(moreresults)))
        except urllib.error.HTTPError as e:
            print('Caught HTTPError')
            print(e)
            print('Dumping results:')
            for result in results:
                print(result)
            quit()
        print("Items total: " + str(len(results)))
        print('Sleeping 20\n')
        time.sleep(20)
    return results


results = get_all_posts('GoldTesting', 86400)
filea = open('timesearching.txt', 'w')
for result in results:
    print(str(result), file=filea)
filea.close()