import traceback

from . import common
from . import tsdb


def commentaugment(
        subreddit=None,
        username=None,
        limit=0,
        num_thresh=0,
        specific_submission=None,
        threshold=0,
        verbose=0,
    ):
    '''
    Take the IDs of collected submissions, and gather comments from those threads.
    Please see the global DOCSTRING_COMMENTAUGMENT variable.
    '''
    common.bot.login(common.r)
    if specific_submission is not None:
        if not specific_submission.startswith('t3_'):
            specific_submission = 't3_' + specific_submission
        specific_submission_obj = common.r.submission(specific_submission[3:])
        subreddit = specific_submission_obj.subreddit.display_name

    if (subreddit is None) == (username is None):
        raise Exception('Enter subreddit or username but not both')

    if subreddit:
        if specific_submission is None:
            database = tsdb.TSDB.for_subreddit(subreddit, do_create=False)
        else:
            database = tsdb.TSDB.for_subreddit(subreddit, do_create=True)
    else:
        database = tsdb.TSDB.for_user(username, do_create=False)
    cur = database.sql.cursor()

    if limit == 0:
        limit = None

    if specific_submission is None:
        query = '''
            SELECT idstr FROM submissions
            WHERE idstr IS NOT NULL
            AND augmented_at IS NULL
            AND num_comments >= ?
            ORDER BY num_comments DESC
        '''
        bindings = [num_thresh]
        cur.execute(query, bindings)
        fetchall = [item[0] for item in cur.fetchall()]
    else:
        # Make sure the object we're augmenting is in the table too!
        database.insert(specific_submission_obj)
        fetchall = [specific_submission]

    totalthreads = len(fetchall)

    if verbose:
        spacer = '\n\t'
    else:
        spacer = ' '

    scannedthreads = 0
    get_submission = common.nofailrequest(get_submission_immediately)
    while len(fetchall) > 0:
        id_batch = fetchall[:100]
        fetchall = fetchall[100:]

        for submission in id_batch:
            submission = get_submission(submission.split('_')[-1])
            message = 'Processing {fullname}{spacer}expecting {num_comments} | '
            message = message.format(
                fullname=submission.fullname,
                spacer=spacer,
                num_comments=submission.num_comments,
            )

            print(message, end='', flush=True)
            if verbose:
                print()

            comments = get_comments_for_thread(submission, limit, threshold, verbose)

            database.insert(comments, commit=False)
            query = '''
                UPDATE submissions
                set augmented_at = ?,
                augmented_count = ?
                WHERE idstr == ?
            '''
            bindings = [common.get_now(), len(comments), submission.fullname]
            cur.execute(query, bindings)
            database.sql.commit()

            scannedthreads += 1
            if verbose:
                print('\t', end='')
            message = 'Found {count} |{spacer}{scannedthreads} / {totalthreads}'
            message = message.format(
                count=len(comments),
                spacer=spacer,
                scannedthreads=scannedthreads,
                totalthreads=totalthreads,
            )
            print(message)

def get_comments_for_thread(submission, limit, threshold, verbose):
    comments = common.nofailrequest(lambda x: x.comments)(submission)
    # PRAW4 flatten is just list().
    comments = manually_replace_comments(comments, limit, threshold, verbose)
    return comments

def get_submission_immediately(submission_id):
    submission = common.r.submission(submission_id)
    # force the lazyloader
    submission.title = submission.title
    return submission

def manually_replace_comments(incomments, limit=None, threshold=0, verbose=False):
    '''
    PRAW's replace_more_comments method cannot continue
    where it left off in the case of an Ow! screen.
    So I'm writing my own function to get each MoreComments item individually

    Furthermore, this function will maximize the number of retrieved comments by
    sorting the MoreComments objects and getting the big chunks before worrying
    about the tail ends.
    '''
    incomments = incomments.list()
    comments = []
    morecomments = []
    while len(incomments) > 0:
        item = incomments.pop()
        if isinstance(item, common.praw.models.MoreComments) and item.count >= threshold:
            morecomments.append(item)
        elif isinstance(item, common.praw.models.Comment):
            comments.append(item)

    while True:
        try:
            if limit is not None and limit <= 0:
                break
            if len(morecomments) == 0:
                break
            morecomments.sort(key=lambda x: x.count)
            mc = morecomments.pop()
            additional = common.nofailrequest(mc.comments)()
            additionals = 0
            if limit is not None:
                limit -= 1
            for item in additional:
                if isinstance(item, common.praw.models.MoreComments) and item.count >= threshold:
                    morecomments.append(item)
                elif isinstance(item, common.praw.models.Comment):
                    comments.append(item)
                    additionals += 1
            if verbose:
                s = '\tGot %d more, %d so far.' % (additionals, len(comments))
                if limit is not None:
                    s += ' Can perform %d more replacements' % limit
                print(s)
        except KeyboardInterrupt:
            raise
        except Exception:
            traceback.print_exc()
    return comments

def commentaugment_argparse(args):
    return commentaugment(
        subreddit=args.subreddit,
        username=args.username,
        limit=common.int_none(args.limit),
        threshold=common.int_none(args.threshold),
        num_thresh=common.int_none(args.num_thresh),
        verbose=args.verbose,
        specific_submission=args.specific_submission,
    )
