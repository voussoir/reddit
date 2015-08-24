import bot
import datetime
import praw
import warnings
warnings.filterwarnings('ignore')
print('logging in')
r=bot.oG()

FLAIR_UNSOLVED = 'unsolved'
MAX_ROOT_COMMENTS = 1
MAX_TOTAL_COMMENTS = 24
IGNORE_DELETED_AUTHORS = True
SAVE_TO_TXT = 'results_%Y%b%d.txt'

MINIMUM_AGE = 60 * 60 * 24
MAXIMUM_AGE = 7 * 60 * 60 * 24

now = datetime.datetime.now(datetime.timezone.utc)
nowstamp = now.timestamp()
outfile = now.strftime(SAVE_TO_TXT)

print('getting new')
subreddit = r.get_subreddit('excel')
new = subreddit.get_new(limit=1000)
results = []
old_in_a_row = 0
for submissionindex, submission in enumerate(new):
    print('Checked %d submissions\r' % (submissionindex), end='')
    age = nowstamp - submission.created_utc
    if age < MINIMUM_AGE:
        continue

    if age > MAXIMUM_AGE:
        old_in_a_row += 1
        if old_in_a_row >= 10:
            break
        continue
    old_in_a_row = 0
    if submission.link_flair_text != FLAIR_UNSOLVED:
        continue

    if IGNORE_DELETED_AUTHORS and submission.author is None:
        continue

    # make sure to perform this part AS LATE AS POSSIBLE to avoid
    # api calls.
    submission.replace_more_comments(limit=None, threshold=1)
    roots = submission.comments[:]
    total = praw.helpers.flatten_tree(submission.comments)

    if len(total) > MAX_TOTAL_COMMENTS:
        continue
    
    # only counts roots
    if len(roots) > MAX_ROOT_COMMENTS:
        continue

    results.append(submission)
print()
results.sort(key=lambda s: (s.created_utc, s.num_comments))
for (submissionindex, submission) in enumerate(results):
    author = '/u/'+submission.author.name if submission.author else '[deleted]'
    timeformat = datetime.datetime.utcfromtimestamp(submission.created_utc)
    timeformat = timeformat.strftime('%d %b %Y %H:%M:%S')

    formatted = '[%s](%s) | %s | %s | %d' % (submission.title, submission.short_link, author, timeformat, submission.num_comments)
    results[submissionindex] = formatted

table = 'title | author | time | comments\n'
table += ':- | :- | -: | -:\n'
table += '\n'.join(results)

outfile = open(outfile, 'w')
print(table, file=outfile)
outfile.close()
