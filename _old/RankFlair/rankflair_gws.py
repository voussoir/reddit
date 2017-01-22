#/u/GoldenSights
from PIL import Image
import io
import urllib.request
import praw
import time
import traceback

''' USER CONFIGURATION ''' 

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does.
#For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "gonewildsmiles"
#This is the sub or list of subs to scan for new posts.
#For a single sub, use "sub1".
#For multiple subreddits, use "sub1+sub2+sub3"
WAIT = 30
#The number of seconds between cycles. Bot is completely inactive during
#this time.

MULTI_SUBREDDIT_RANK = False
#If you entered a single subreddit in SUBREDDIT, you can ignore this.
#If you entered multiple:
#   True = Posts are ranked relative to all the subreddits combined
#   False = Each subreddit is managed individually

IGNORE_UNKNOWN = True
#If a post has a flair that is not part of the rank system, should
# we just leave the post alone?
#If False, that post's flair will be overwritten with a rank!

RANKINGS = {   1: "Ultra Smile!!!!!",
              10: "Killer Smile!!!!",
              25: "Awesome Smile!!!",
              50: "Super Smile!!",
             100: "Great Smile!"
           }
#Flair text

RANKINGCSS = {}
#Flair CSS class. Use empty quotes or nothing if you don't have any.

SEND_MODMAIL = True
#Send subreddit modmail when a post achieves a rank
MODMAIL_SUBJECT = "Automated post ranking system"
#The subjectline for the sent modmail
MODMAIL_BODY = """
_username_ has just earned rank _ranktext_ on their
post ["_posttitle_"](_postlink_)
"""
#This is the modmail message
#Post information can be insterted into the message with these injectors
# _posttitle_ : Post title
# _postid_    : Post ID number
# _postlink_  : Post permalink
# _ranktext_  : Rank text
# _rankvalue_ : Rank value
# _username_  : Post author
#If you would like more injectors, please message me.

''' All done! '''

# Automatic preparation
RANKINGS_REVERSE = {}
for key in RANKINGS:
    val = RANKINGS[key].lower()
    RANKINGS_REVERSE[val] = key

RANKKEYS = sorted(list(RANKINGS.keys()))
MAXRANK = RANKKEYS[-1]

if MULTI_SUBREDDIT_RANK or '+' not in SUBREDDIT:
    SUBREDDIT_L = [SUBREDDIT]
else:
    SUBREDDIT_L = SUBREDDIT.split('+')

try:
    import bot
    USERAGENT = bot.aG
except ImportError:
    pass
# /Automatic preparation

try:
    import bot
    USERAGENT = bot.aG
    APP_ID = bot.oG_id
    APP_SECRET = bot.oG_secret
    APP_URI = bot.oG_uri
    APP_REFRESH = bot.oG_scopes['all']
except ImportError:
    pass

print('Logging in')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def manageranks():
    ''' Ties it all together. '''
    for subreddit in SUBREDDIT_L:
        print('Getting posts from /r/%s' % subreddit)
        subreddit = r.get_subreddit(subreddit)
        topall = subreddit.get_top_from_all(limit=MAXRANK)
        topall = list(topall)
        for position in range(len(topall)):
            post = topall[position]
            position += 1
            # Add 1 because indices start at 0 and humans start at 1

            print(post.id, "Position: %d" % position)
            
            actual_flair = post.link_flair_text
            suggested = get_rank_from_pos(position)
            suggested_rank = suggested[0]
            suggested_flair = suggested[1]
            suggested_css = RANKINGCSS.get(suggested_rank, "")
            # Tries to get the CSS class and uses "" if it can't find it.

            if flair_is_better(new=suggested_flair, old=actual_flair):
                print('\tNew flair: %s' % suggested_flair)
                post.set_flair(flair_text=suggested_flair, flair_css_class=suggested_css)
                rankjump = calculate_rankjump(suggested_rank, actual_flair)
                try:
                    pauthor = post.author.name
                except:
                    print('\tAuthor is deleted. Removing post.\n')
                    post.remove()
                    continue
                print('\tAwarding %d points to %s' % (rankjump, pauthor))

                try:
                    userflair = subreddit.get_flair(pauthor)
                    userflaircss = userflair['flair_css_class']
                    userflairtext = userflair['flair_text']
                    # "But why don't you use the author_flair_text attribute of the post?"
                    # This method ensures that if a users earns two flairs during this run, 
                    # we increment their flair twice properly, instead of adding x+y=z twice.
                except:
                    userflaircss = post.author_flair_css_class
                    userflairtext = post.author_flair_text
                    # Fallback for testing, etc.

                newflair = incrementflair(userflaircss, rankjump)
                subreddit.set_flair(pauthor, flair_css_class=newflair, flair_text=userflairtext)
                print('\told: css: %s, text: %s' % (userflaircss, userflairtext))
                print('\tnew: css: %s, text: %s' % (newflair, userflairtext))
                commenttext = "%s +%d Point%s" % (suggested_flair, rankjump, "s!" if rankjump > 1 else "!")
                try:
                    starcomment = post.add_comment(commenttext)
                    starcomment.distinguish()
                except:
                    pass
                print("\tWriting comment:", commenttext)

                if SEND_MODMAIL:
                    compose_modmail(post, suggested_flair, suggested_rank)
                    pass
            print()

def get_rank_from_pos(position):
    ''' Given a position in a listing, return the appropriate rank '''
    for rankkey in RANKKEYS:
        if rankkey >= position:
            return [rankkey, RANKINGS[rankkey]]

def calculate_rankjump(suggested_rank, actual_flair):
    '''
    Calculate how many points should be awarded based on how many ranks
    the user has moved up.
    '''
    suggested_index = RANKKEYS.index(suggested_rank)
    if actual_flair:
        # Remember that for the index of a rank, lower is better.
        # If the user moves to rank 25 (index 2) from rank 100 (index 4),
        # we move +2 for passing rank 50, and +3 for passing rank 25,
        # for a total of 5 points.
        # rank 50 = index 3 = 2nd from bottom = 2 points
        # rank 25 = index 2 = 3rd from bottom = 3 points
        actual_rank = RANKINGS_REVERSE[actual_flair.lower()]
        actual_index = RANKKEYS.index(actual_rank)
        rankjump = sum(range((len(RANKKEYS)-actual_index)+1, (len(RANKKEYS)-suggested_index)+1))
    else:
        # Sum the ranks below the suggested index
        rankjump = sum(range(1, (len(RANKKEYS)-suggested_index)+1))
    return rankjump

def flair_is_better(new, old):
    ''' Compare whether the newer flair is better than the older flair '''
    newrank = RANKINGS_REVERSE[new.lower()]

    if old == "" or old is None:
        print('\tNew:%d, Old: None!' % (newrank))
        #Post has no flair yet. Anything is better
        return True
    try:
        oldrank = RANKINGS_REVERSE[old.lower()]
    except KeyError:
        if IGNORE_UNKNOWN:
            print('\t"%s" is not a recognized rank. Ignoring' % old)
            return False
        print('\t"%s" is not a recognized rank. Overwriting' % old)
        return True

    print('\tNew:%d, Old:%d' % (newrank, oldrank))
    if newrank < oldrank:
        print('\tBetter')
        return True
    print('\tNot better')
    return False

def compose_modmail(post, new, newrank):
    print('\tWriting modmail')
    subreddit = '/r/' + post.subreddit.display_name
    try:
        author = post.author.name
    except AttributeError:
        author = "[deleted]"

    message = MODMAIL_BODY
    message = message.replace('_posttitle_', post.title)
    message = message.replace('_postid_', post.id)
    message = message.replace('_postlink_', post.short_link)
    message = message.replace('_ranktext_', new)
    message = message.replace('_rankvalue_', str(newrank))
    message = message.replace('_username_', author)

    r.send_message(subreddit, MODMAIL_SUBJECT, message)

def incrementflair(flair, jump=1):
    if not flair or flair == "":
        return "%02d" % jump
    try:
        star = "star" in flair
        f = flair.replace("star", "")
        f = int(f)
    except ValueError:
        print("\tNon-numerical:", flair)
        return flair
    f += jump
    f = "%02d" % f
    if star:
        f += "star"
    return f

def isdeletedimage(url):
        try:
                page = urllib.request.urlopen(url)
                image = Image.open(io.BytesIO(page.read()))
                if image.size == (161, 81) and image.getpixel((0,0)) == 0:
                        return True
                return False
        except urllib.error.HTTPError:
                return True
 
def checkfordeleted():
        for subreddit in SUBREDDIT_L:
                print('Checking for deletions in ' + subreddit)
                subreddit = r.get_subreddit(subreddit)
                topall = subreddit.get_top_from_all(limit=MAXRANK)
                topall = list(topall)
                for post in topall:
                    purl = post.url
                    if 'imgur.com' in purl and 'imgur.com/a/' not in purl:
                            if 'i.imgur.com' not in purl:
                                    purl = purl.replace('imgur', 'i.imgur')
                                    purl = purl.replace('gallery/', '') + '.jpg'
                            if isdeletedimage(purl):
                                    print(post.id, 'links to a deleted image. Removing.')
                                    post.remove()
                    if not post.author:
                        print(post.id, ' author is deleted. Removing.')
                        post.remove()
                                        

if __name__ == '__main__':
    deletion_check_counter = 0
    while True:
        try:
            manageranks()
            deletion_check_counter += 1
            if deletion_check_counter >= 50:
                checkfordeleted()
                deletion_check_counter = 0
        except Exception:
            traceback.print_exc()
        print('Sleeping %d seconds\n' % WAIT)
        time.sleep(WAIT)