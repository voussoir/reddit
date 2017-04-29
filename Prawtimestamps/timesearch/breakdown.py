import os
import json

from . import common
from . import tsdb


def breakdown_database(subreddit=None, username=None):
    '''
    Given a database, return a json dict breaking down the submission / comment count for
    users (if a subreddit database) or subreddits (if a user database).
    '''
    if (subreddit is None) == (username is None):
        raise Exception('Enter subreddit or username but not both')

    breakdown_results = {}
    def _ingest(names, subkey):
        for name in names:
            breakdown_results.setdefault(name, {})
            breakdown_results[name].setdefault(subkey, 0)
            breakdown_results[name][subkey] += 1

    if subreddit:
        database = tsdb.TSDB.for_subreddit(subreddit, do_create=False)
    else:
        database = tsdb.TSDB.for_user(username, do_create=False)
    cur = database.sql.cursor()

    for table in ['submissions', 'comments']:
        if subreddit:
            cur.execute('SELECT author FROM %s' % table)
        elif username:
            cur.execute('SELECT subreddit FROM %s' % table)

        names = (row[0] for row in common.fetchgenerator(cur))
        _ingest(names, table)

    for name in breakdown_results:
        breakdown_results[name].setdefault('submissions', 0)
        breakdown_results[name].setdefault('comments', 0)

    return breakdown_results

def breakdown_argparse(args):
    if args.subreddit:
        database = tsdb.TSDB.for_subreddit(args.subreddit, do_create=False)
    else:
        database = tsdb.TSDB.for_user(args.username, do_create=False)

    breakdown_results = breakdown_database(
        subreddit=args.subreddit,
        username=args.username,
    )

    def sort_name(name):
        return name.lower()
    def sort_submissions(name):
        invert_score = -1 * breakdown_results[name]['submissions']
        return (invert_score, name.lower())
    def sort_comments(name):
        invert_score = -1 * breakdown_results[name]['comments']
        return (invert_score, name.lower())
    def sort_total_posts(name):
        invert_score = breakdown_results[name]['submissions'] + breakdown_results[name]['comments']
        invert_score = -1 * invert_score
        return (invert_score, name.lower())
    breakdown_sorters = {
        'name': sort_name,
        'submissions': sort_submissions,
        'comments': sort_comments,
        'total_posts': sort_total_posts,
    }

    breakdown_names = list(breakdown_results.keys())
    if args.sort is not None:
        try:
            sorter = breakdown_sorters[args.sort.lower()]
        except KeyError:
            message = '{sorter} is not a sorter. Choose from {options}'
            message = message.format(sorter=args.sort, options=list(breakdown_sorters.keys()))
            raise KeyError(message)
        breakdown_names.sort(key=sorter)
        dump = '    "{name}": {{"submissions": {submissions}, "comments": {comments}}}'
        dump = [dump.format(name=name, **breakdown_results[name]) for name in breakdown_names]
        dump = ',\n'.join(dump)
        dump = '{\n' + dump + '\n}\n'
    else:
        dump = json.dumps(breakdown_results)

    if args.sort is None:
        breakdown_basename = '%s_breakdown.json'
    else:
        breakdown_basename = '%%s_breakdown_%s.json' % args.sort

    breakdown_basename = breakdown_basename % database.filepath.replace_extension('').basename
    breakdown_filepath = database.breakdown_dir.with_child(breakdown_basename)
    os.makedirs(breakdown_filepath.parent.absolute_path, exist_ok=True)
    breakdown_file = open(breakdown_filepath.absolute_path, 'w')
    with breakdown_file:
        breakdown_file.write(dump)
    print('Wrote', breakdown_filepath.relative_path)

    return breakdown_results
