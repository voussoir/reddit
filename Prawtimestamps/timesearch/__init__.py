import argparse
import sys

from . import exceptions

# NOTE: Originally I wanted the docstring for each module to be within their
# file. However, this means that composing the global helptext would require
# importing those modules, which will subsequently import PRAW and a whole lot
# of other things. This made TS very slow to load which is okay when you're
# actually using it but really terrible when you're just viewing the help text.
DOCSTRING = '''
Timesearch
The subreddit archiver

The basics:
1. Collect a subreddit's submissions
    > timesearch.py timesearch -r subredditname

2. Collect the comments for those submissions
    > timesearch.py commentaugment -r subredditname

3. Stay up-to-date
    > timesearch.py livestream -r subredditname


Commands for collecting:
{timesearch}
{commentaugment}
{livestream}
{getstyles}
{getwiki}

Commands for processing:
{offline_reading}
{redmash}
{breakdown}
{mergedb}

TO SEE DETAILS ON EACH COMMAND, RUN
> timesearch.py <command>
'''

MODULE_DOCSTRINGS = {
    'breakdown': '''
breakdown:
    Give the comment / submission counts for users in a subreddit, or
    the subreddits that a user posts to.

    Automatically dumps into a <database>_breakdown.json file
    in the same directory as the database.

    > timesearch.py breakdown -r subredditname
    > timesearch.py breakdown -u username

    flags:
    -r "test" | --subreddit "test":
        The subreddit database to break down.

    -u "test" | --username "test":
        The username database to break down.

    --sort "name" | "submissions" | "comments" | "total_posts"
        Sort the output.
''',

    'commentaugment': '''
commentaugment:
    Collect comments for the submissions in the database.
    NOTE - if you did a timesearch scan on a username, this function is
    mostly useless. It collects comments that were made on OP's submissions
    but it does not find OP's comments on other people's submissions which
    is what you probably wanted. Unfortunately that's not possible.

    > timesearch.py commentaugment -r subredditname <flags>
    > timesearch.py commentaugment -u username <flags>

    flags:
    -l 18 | --limit 18:
        The number of MoreComments objects to replace.
        Default: No limit

    -t 5 | --threshold 5:
        The number of comments a MoreComments object must claim to have
        for us to open it.
        Actual number received may be lower.
        Default: >= 0

    -n 4 | --num_thresh 4:
        The number of comments a submission must claim to have for us to
        scan it at all.
        Actual number received may be lower.
        Default: >= 1

    -s "t3_xxxxxx" | --specific "t3_xxxxxx":
        Given a submission ID, t3_xxxxxx, scan only that submission.

    -v | --verbose:
        If provided, print more stuff while working.
''',

    'getstyles': '''
getstyles:
    Collect the stylesheet, and css images.

    > timesearch.py getstyles -r subredditname
''',

    'getwiki': '''
getwiki:
    Collect all available wiki pages.

    > timesearch.py getwiki -r subredditname
''',

    'mergedb': '''
mergedb:
    Copy all new posts from one timesearch database into another.

    > timesearch mergedb --from redditdev1.db --to redditdev2.db

    flags:
    --from:
        The database file containing the posts you wish to copy.

    --to:
        The database file to which you will copy the posts.
        The database is modified in-place.
        Existing posts will be ignored and not updated.
''',

    'livestream': '''
livestream:
    Continously collect submissions and/or comments.

    > timesearch.py livestream -r subredditname <flags>
    > timesearch.py livestream -u username <flags>

    flags:
    -r "test" | --subreddit "test":
        The subreddit to collect from.

    -u "test" | --username "test":
        The redditor to collect from.

    -s | --submissions:
        If provided, do collect submissions. Otherwise don't.

    -c | --comments:
        If provided, do collect comments. Otherwise don't.

    If submissions and comments are BOTH left unspecified, then they will
    BOTH be collected.

    -v | --verbose:
        If provided, print extra information to the screen.

    -w 30 | --wait 30:
        The number of seconds to wait between cycles.

    -1 | --once:
        If provided, only do a single loop. Otherwise go forever.
''',

    'offline_reading': '''
offline_reading:
    Render submissions and comment threads to HTML via Markdown.

    > timesearch.py offline_reading -r subredditname <flags>
    > timesearch.py offline_reading -u username <flags>

    flags:
    -s "t3_xxxxxx" | --specific "t3_xxxxxx":
        Given a submission ID, t3_xxxxxx, render only that submission.
        Otherwise render every submission in the database.
''',

    'redmash': '''
redmash:
    Dump submission listings to a plaintext or HTML file.

    > timesearch.py redmash -r subredditname <flags>
    > timesearch.py redmash -u username <flags>

    flags:
    -r "test" | --subreddit "test":
        The subreddit database to dump

    -u "test" | --username "test":
        The username database to dump

    --html:
        Write HTML files instead of plain text.

    -st 50 | --score_threshold 50:
        Only mash posts with at least this many points.
        Applies to ALL mashes!

    --all:
        Perform all of the mashes listed below.

    --date:
        Perform a mash sorted by date.

    --title:
        Perform a mash sorted by title.

    --score:
        Perform a mash sorted by score.

    --author:
        For subreddit databases only.
        Perform a mash sorted by author.

    --sub:
        For username databases only.
        Perform a mash sorted by subreddit.

    --flair:
        Perform a mash sorted by flair.

    examples:
        `timesearch redmash -r botwatch --date`
        does only the date file.

        `timesearch redmash -r botwatch --score --title`
        does both the score and title files.

        `timesearch redmash -r botwatch --score --score_threshold 50`
        only shows submissions with >= 50 points.

        `timesearch redmash -r botwatch --all`
        performs all of the different mashes.
''',

    'timesearch': '''
timesearch:
    Collect submissions from the subreddit across all of history, or
    Collect submissions by a user (as many as possible).

    > timesearch.py timesearch -r subredditname <flags>
    > timesearch.py timesearch -u username <flags>

    -r "test" | --subreddit "test":
        The subreddit to scan. Mutually exclusive with username.

    -u "test" | --username "test":
        The user to scan. Mutually exclusive with subreddit.

    -l "update" | --lower "update":
        If a number - the unix timestamp to start at.
        If "update" - continue from latest submission in db.
        Default: update

    -up 1467460221 | --upper 1467460221:
        If a number - the unix timestamp to stop at.
        If not provided - stop at current time.
        Default: current time

    -i 86400 | --interval 86400:
        The initial interval for the scanning window, in seconds.
        This is only a starting value. The window will shrink and stretch
        as necessary based on received submission counts.
        Default: 86400
''',
}


def docstring_preview(text):
    '''
    Return the brief description at the top of the text.
    User can get full text by looking at each specifically.
    '''
    return text.split('\n\n')[0]

def listget(li, index, fallback=None):
    try:
        return li[index]
    except IndexError:
        return fallback

def indent(text, spaces=4):
    spaces = ' ' * spaces
    return '\n'.join(spaces + line if line.strip() != '' else line for line in text.split('\n'))

docstring_headers = {
    key: indent(docstring_preview(value))
    for (key, value) in MODULE_DOCSTRINGS.items()
}

DOCSTRING = DOCSTRING.format(**docstring_headers)

####################################################################################################
####################################################################################################

def breakdown_gateway(args):
    from . import breakdown
    breakdown.breakdown_argparse(args)

def commentaugment_gateway(args):
    from . import commentaugment
    commentaugment.commentaugment_argparse(args)

def getstyles_gateway(args):
    from . import getstyles
    getstyles.getstyles_argparse(args)

def getwiki_gateway(args):
    from . import getwiki
    getwiki.getwiki_argparse(args)

def livestream_gateway(args):
    from . import livestream
    livestream.livestream_argparse(args)

def mergedb_gateway(args):
    from . import mergedb
    mergedb.mergedb_argparse(args)

def offline_reading_gateway(args):
    from . import offline_reading
    offline_reading.offline_reading_argparse(args)

def redmash_gateway(args):
    from . import redmash
    redmash.redmash_argparse(args)

def timesearch_gateway(args):
    from . import timesearch
    timesearch.timesearch_argparse(args)


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

p_breakdown = subparsers.add_parser('breakdown')
p_breakdown.add_argument('--sort', dest='sort', default=None)
p_breakdown.add_argument('-r', '--subreddit', dest='subreddit', default=None)
p_breakdown.add_argument('-u', '--user', dest='username', default=None)
p_breakdown.set_defaults(func=breakdown_gateway)

p_commentaugment = subparsers.add_parser('commentaugment')
p_commentaugment.add_argument('-l', '--limit', dest='limit', default=None)
p_commentaugment.add_argument('-n', '--num_thresh', dest='num_thresh', default=1)
p_commentaugment.add_argument('-r', '--subreddit', dest='subreddit', default=None)
p_commentaugment.add_argument('-s', '--specific', dest='specific_submission', default=None)
p_commentaugment.add_argument('-t', '--threshold', dest='threshold', default=0)
p_commentaugment.add_argument('-u', '--user', dest='username', default=None)
p_commentaugment.add_argument('-v', '--verbose', dest='verbose', action='store_true')
p_commentaugment.set_defaults(func=commentaugment_gateway)

p_getstyles = subparsers.add_parser('getstyles')
p_getstyles.add_argument('-r', '--subreddit', dest='subreddit')
p_getstyles.set_defaults(func=getstyles_gateway)

p_getwiki = subparsers.add_parser('getwiki')
p_getwiki.add_argument('-r', '--subreddit', dest='subreddit')
p_getwiki.set_defaults(func=getwiki_gateway)

p_livestream = subparsers.add_parser('livestream')
p_livestream.add_argument('-1', '--once', dest='once', action='store_true')
p_livestream.add_argument('-c', '--comments', dest='comments', action='store_true')
p_livestream.add_argument('-l', '--limit', dest='limit', default=None)
p_livestream.add_argument('-r', '--subreddit', dest='subreddit', default=None)
p_livestream.add_argument('-s', '--submissions', dest='submissions', action='store_true')
p_livestream.add_argument('-u', '--user', dest='username', default=None)
p_livestream.add_argument('-v', '--verbose', dest='verbose', action='store_true')
p_livestream.add_argument('-w', '--wait', dest='sleepy', default=30)
p_livestream.set_defaults(func=livestream_gateway)

p_mergedb = subparsers.add_parser('mergedb')
p_mergedb.add_argument('--from', dest='from_db_path', required=True)
p_mergedb.add_argument('--to', dest='to_db_path', required=True)
p_mergedb.set_defaults(func=mergedb_gateway)

p_offline_reading = subparsers.add_parser('offline_reading')
p_offline_reading.add_argument('-r', '--subreddit', dest='subreddit', default=None)
p_offline_reading.add_argument('-s', '--specific', dest='specific_submission', default=None)
p_offline_reading.add_argument('-u', '--user', dest='username', default=None)
p_offline_reading.set_defaults(func=offline_reading_gateway)

p_redmash = subparsers.add_parser('redmash')
p_redmash.add_argument('--all', dest='do_all', action='store_true')
p_redmash.add_argument('--author', dest='do_author', action='store_true')
p_redmash.add_argument('--date', dest='do_date', action='store_true')
p_redmash.add_argument('--flair', dest='do_flair', action='store_true')
p_redmash.add_argument('--html', dest='html', action='store_true')
p_redmash.add_argument('--score', dest='do_score', action='store_true')
p_redmash.add_argument('--sub', dest='do_subreddit', action='store_true')
p_redmash.add_argument('--title', dest='do_title', action='store_true')
p_redmash.add_argument('-r', '--subreddit', dest='subreddit', default=None)
p_redmash.add_argument('-st', '--score_threshold', dest='score_threshold', default=0)
p_redmash.add_argument('-u', '--user', dest='username', default=None)
p_redmash.set_defaults(func=redmash_gateway)

p_timesearch = subparsers.add_parser('timesearch')
p_timesearch.add_argument('-i', '--interval', dest='interval', default=86400)
p_timesearch.add_argument('-l', '--lower', dest='lower', default='update')
p_timesearch.add_argument('-r', '--subreddit', dest='subreddit', default=None)
p_timesearch.add_argument('-u', '--user', dest='username', default=None)
p_timesearch.add_argument('-up', '--upper', dest='upper', default=None)
p_timesearch.set_defaults(func=timesearch_gateway)

def main(argv):
    helpstrings = {'', 'help', '-h', '--help'}

    command = listget(argv, 0, '').lower()

    # The user did not enter a command, or entered something unrecognized.
    if command not in MODULE_DOCSTRINGS:
        print(DOCSTRING)
        if command == '':
            print('You are seeing the default help text because you did not choose a command.')
        elif command not in helpstrings:
            print('You are seeing the default help text because "%s" was not recognized' % command)
        return 1

    # The user entered a command, but no further arguments, or just help.
    argument = listget(argv, 1, '').lower()
    if argument in helpstrings:
        print(MODULE_DOCSTRINGS[command])
        return 1

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except exceptions.DBNotFound as e:
        message = '"%s" is not an existing database.'
        message += '\nHave you used any of the other utilities to collect data?'
        message = message % e.path.absolute_path
        print(message)
        return 1

    return 0

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
