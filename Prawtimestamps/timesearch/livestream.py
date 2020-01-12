import copy
import time
import traceback

from . import common
from . import exceptions
from . import tsdb


def generator_printer(generator):
    for step in generator:
        newtext = '%ds, %dc' % (step['new_submissions'], step['new_comments'])
        totalnew = step['new_submissions'] + step['new_comments']
        status = '{now} +{new}'.format(now=common.human(common.get_now()), new=newtext)
        print(status, end='')
        if totalnew == 0 and common.log.level != common.logging.DEBUG:
            # Since there were no news, allow the next line to overwrite status
            print('\r', end='', flush=True)
        else:
            print()
        yield None

def livestream(
        subreddit=None,
        username=None,
        as_a_generator=False,
        do_submissions=True,
        do_comments=True,
        limit=100,
        only_once=False,
        sleepy=30,
    ):
    '''
    Continuously get posts from this source and insert them into the database.

    as_a_generator:
        return a generator where every iteration does a single livestream loop.
        This is good if you want to manage multiple livestreams yourself by
        calling `next` on each of them, instead of getting stuck in here.
    '''

    generator = _livestream_as_a_generator(
        subreddit=subreddit,
        username=username,
        do_submissions=do_submissions,
        do_comments=do_comments,
        limit=limit,
        params={'show': 'all'},
    )
    if as_a_generator:
        return generator

    generator = generator_printer(generator)

    while True:
        try:
            step = next(generator)
            if only_once:
                break
            time.sleep(sleepy)

        except KeyboardInterrupt:
            print()
            return

hangman = lambda: livestream(
    username='gallowboob',
    do_submissions=True,
    do_comments=True,
    sleepy=60,
)

def _livestream_as_a_generator(
        subreddit,
        username,
        do_submissions,
        do_comments,
        limit,
        params,
    ):

    if not common.is_xor(subreddit, username):
        raise exceptions.NotExclusive(['subreddit', 'username'])

    if not any([do_submissions, do_comments]):
        raise TypeError('Required do_submissions and/or do_comments parameter')
    common.bot.login(common.r)

    if subreddit:
        common.log.debug('Getting subreddit %s', subreddit)
        (database, subreddit) = tsdb.TSDB.for_subreddit(subreddit, fix_name=True)
        subreddit = common.r.subreddit(subreddit)
        submission_function = subreddit.new if do_submissions else None
        comment_function = subreddit.comments if do_comments else None
    else:
        common.log.debug('Getting redditor %s', username)
        (database, username) = tsdb.TSDB.for_user(username, fix_name=True)
        user = common.r.redditor(username)
        submission_function = user.submissions.new if do_submissions else None
        comment_function = user.comments.new if do_comments else None

    while True:
        try:
            items = _livestream_helper(
                submission_function=submission_function,
                comment_function=comment_function,
                limit=limit,
                params=params,
            )
            newitems = database.insert(items)
            yield newitems
        except Exception:
            traceback.print_exc()
            print('Retrying in 5...')
            time.sleep(5)

def _livestream_helper(
        submission_function=None,
        comment_function=None,
        *args,
        **kwargs,
    ):
    '''
    Given a submission-retrieving function and/or a comment-retrieving function,
    collect submissions and comments in a list together and return that.

    args and kwargs go into the collecting functions.
    '''
    if not any([submission_function, comment_function]):
        raise TypeError('Required submissions and/or comments parameter')
    results = []

    if submission_function:
        common.log.debug('Getting submissions %s %s', args, kwargs)
        this_kwargs = copy.deepcopy(kwargs)
        submission_batch = submission_function(*args, **this_kwargs)
        results.extend(submission_batch)
    if comment_function:
        common.log.debug('Getting comments %s %s', args, kwargs)
        this_kwargs = copy.deepcopy(kwargs)
        comment_batch = comment_function(*args, **this_kwargs)
        results.extend(comment_batch)
    common.log.debug('Got %d posts', len(results))
    return results

def livestream_argparse(args):
    if args.verbose:
        common.log.setLevel(common.logging.DEBUG)

    if args.submissions is args.comments is False:
        args.submissions = True
        args.comments = True
    if args.limit is None:
        limit = 100
    else:
        limit = int(args.limit)

    return livestream(
        subreddit=args.subreddit,
        username=args.username,
        do_comments=args.comments,
        do_submissions=args.submissions,
        limit=limit,
        only_once=args.once,
        sleepy=int(args.sleepy),
    )
