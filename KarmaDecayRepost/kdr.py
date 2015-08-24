import praw
import requests
import re
import sqlite3
import time
import traceback

USERAGENT = ""
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/

KARMADECAY_URL = 'http://karmadecay.com/r/%s/comments/%s/'
REPATTERN = 'href="/r/.* title='
HEADERS = {
'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
}
SUBREDDIT = 'pics'
# how long to wait between re-runs
WAIT = 30

try:
    import bot
    USERAGENT = bot.aG
    APP_ID = bot.oG_id
    APP_SECRET = bot.oG_secret
    APP_URI = bot.oG_uri
    APP_REFRESH = bot.oG_scopes['all']
except ImportError:
    pass

sql = sqlite3.connect('kdr.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')

print('logging in')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def get_karmadecay(subreddit, iid):
    '''
    retrieve the HTML for the karmadecay page for this post
    '''
    url = KARMADECAY_URL % (subreddit, iid)
    page = requests.get(url, headers=HEADERS, timeout=60)
    page.raise_for_status()
    return page.text

def extract_reddit_ids(karmadecay):
    '''
    given the HTML from karmadecay, regex the ids of any "very similar"
    image matches
    '''
    if 'Unable to find an image at' in karmadecay:
        print('unable to find any images')
        return []
    if 'No very similar images were found' in karmadecay:
        print('no very similar images')
        return []
    if 'very similar image' not in karmadecay:
        print('expected "very similar" is missing')
        return []

    karmadecay = karmadecay.split('Less similar images')[0]
    karmadecay = karmadecay.split('very similar image')[1]

    matches = re.findall(REPATTERN, karmadecay)
    matches = [m.split('"')[1] for m in matches]
    matches = [m.split('/comments/')[1].split('/')[0] for m in matches]
    matches = ['t3_' + m for m in matches]

    return matches

def kdr():
    subreddit = r.get_subreddit(SUBREDDIT)
    print('getting submissions')
    submissions = subreddit.get_hot(limit=50)
    for submission in submissions:
        cur.execute('SELECT * FROM oldposts WHERE id=?', [submission.id])
        if cur.fetchone() is not None:
            continue

        cur.execute('INSERT INTO oldposts VALUES(?)', [submission.id])
        sql.commit()

        print(submission.id)
        kd = get_karmadecay(submission.subreddit.display_name, submission.id)
        # regex the reddit links out of that html
        matches = extract_reddit_ids(kd)
        # convert the ids to fullnames and get those submission objects
        if len(matches) == 0:
            print('found no matches []')
            continue
        matchposts = r.get_info(thing_id=matches)
        if matchposts is None:
            print('found no submissions for', matches)
            continue
        for match in matchposts:
            # check if any match was within the last 30 days    
            agediff = submission.created_utc - match.created_utc
            if agediff <= (30 * 24 * 60 * 60):
                print('matched with', match.fullname)
                print('dont forget to un-comment the remove() line when youre ready')
                #submission.remove()
                break

if __name__ == '__main__':
    while True:
        try:
            kdr()
        except:
            traceback.print_exc()
        print('running again in %d seconds\n' % WAIT)
        time.sleep(WAIT)
'''
SAMPLES = [
('pics', '3i4gjy'), # valid submission with matches
('goldtesting', '26wkzi'), # valid submission with no matches
('goldtesting', '3cychc'), # selfpost, should fail
]
for sample in SAMPLES:
    print(sample)
    a = get_karmadecay(*sample)
    a = extract_reddit_ids(a)
    if len(a) == 0:
        print('Got no items')
        continue
    print(a)
    submissions = r.get_info(thing_id=a)
    for submission in submissions:
        print(submission.id, submission.created_utc, submission.title)
    print()
'''