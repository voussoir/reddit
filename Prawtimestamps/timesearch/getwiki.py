import os

from . import common
from . import tsdb


def getwiki(subreddit):
    (database, subreddit) = tsdb.TSDB.for_subreddit(subreddit, fix_name=True)

    print('Getting wiki pages for /r/%s' % subreddit)
    subreddit = common.r.subreddit(subreddit)

    for wikipage in subreddit.wiki:
        if wikipage.name == 'config/stylesheet':
            continue

        wikipage_path = database.wiki_dir.join(wikipage.name).replace_extension('md')
        os.makedirs(wikipage_path.parent.absolute_path, exist_ok=True)
        with open(wikipage_path.absolute_path, 'w', encoding='utf-8') as handle:
            handle.write(wikipage.content_md)
        print('Wrote', wikipage_path.relative_path)

def getwiki_argparse(args):
    return getwiki(args.subreddit)
