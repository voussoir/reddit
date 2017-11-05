import copy
import time
import traceback

from . import common
from . import tsdb


def livestream(
        subreddit=None,
        username=None,
        verbose=False,
        as_a_generator=False,
        do_submissions=True,
        do_comments=True,
        limit=100,
        only_once=False,
        sleepy=30,
    ):
    '''
    Continuously get posts from this source
    and insert them into the database

    as_a_generator:
        return a generator where every iteration does a single livestream loop.
        This is good if you want to manage multiple livestreams yourself by
        calling `next` on each of them, instead of getting stuck in here.
    '''
    if bool(subreddit) == bool(username):
        raise Exception('Require either username / subreddit parameter, but not both')
    if bool(do_submissions) is bool(do_comments) is False:
        raise Exception('Require do_submissions and/or do_comments parameter')
    common.bot.login(common.r)

    if subreddit:
        print('Getting subreddit %s' % subreddit)
        database = tsdb.TSDB.for_subreddit(subreddit)
        subreddit = common.r.subreddit(subreddit)
        submissions = subreddit.new if do_submissions else None
        comments = subreddit.comments if do_comments else None
    else:
        print('Getting redditor %s' % username)
        database = tsdb.TSDB.for_user(username)
        user = common.r.redditor(username)
        submissions = user.submissions.new if do_submissions else None
        comments = user.comments.new if do_comments else None

    generator = _livestream_as_a_generator(
        database,
        submission_function=submissions,
        comment_function=comments,
        limit=limit,
        params={'show': 'all'},
        verbose=verbose,
    )
    if as_a_generator:
        return generator

    while True:
        try:
            step = next(generator)
            newtext = '%ds, %dc' % (step['new_submissions'], step['new_comments'])
            totalnew = step['new_submissions'] + step['new_comments']
            status = '{now} +{new}'.format(now=common.human(common.get_now()), new=newtext)
            print(status, end='', flush=True)
            if totalnew == 0 and verbose is False:
                # Since there were no news, allow the next line to overwrite status
                print('\r', end='')
            else:
                print()

            if verbose:
                print('Loop finished.')
            if only_once:
                break
            time.sleep(sleepy)

        except KeyboardInterrupt:
            print()
            return

        except Exception:
            traceback.print_exc()
            print('Retrying in 5...')
            time.sleep(5)

hangman = lambda: livestream(
    username='gallowboob',
    do_submissions=True,
    do_comments=True,
    sleepy=60,
)

def _livestream_as_a_generator(
        database,
        submission_function,
        comment_function,
        limit,
        params,
        verbose,
    ):
    while True:
        #common.r.handler.clear_cache()
        try:
            items = _livestream_helper(
                submission_function=submission_function,
                comment_function=comment_function,
                limit=limit,
                params=params,
                verbose=verbose,
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
        verbose=False,
        *args,
        **kwargs,
    ):
    '''
    Given a submission-retrieving function and/or a comment-retrieving function,
    collect submissions and comments in a list together and return that.

    args and kwargs go into the collecting functions.
    '''
    if bool(submission_function) is bool(comment_function) is False:
        raise Exception('Require submissions and/or comments parameter')
    results = []

    if submission_function:
        if verbose:
            print('Getting submissions', args, kwargs)
        this_kwargs = copy.deepcopy(kwargs)
        submission_batch = submission_function(*args, **this_kwargs)
        results.extend(submission_batch)
    if comment_function:
        if verbose:
            print('Getting comments', args, kwargs)
        this_kwargs = copy.deepcopy(kwargs)
        comment_batch = comment_function(*args, **this_kwargs)
        results.extend(comment_batch)
    if verbose:
        print('Collected. Saving...')
    return results

def livestream_argparse(args):
    if args.submissions is args.comments is False:
        args.submissions = True
        args.comments = True
    if args.limit is None:
        limit = 100
    else:
        limit = int(args.limit)

    if args.submissions is False and args.comments is False:
        args.submissions = True
        args.comments = True

    return livestream(
        subreddit=args.subreddit,
        username=args.username,
        do_comments=args.comments,
        do_submissions=args.submissions,
        limit=limit,
        verbose=args.verbose,
        only_once=args.once,
        sleepy=common.int_none(args.sleepy),
    )
