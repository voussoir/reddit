import os
import requests

from . import common
from . import tsdb


def getstyles(subreddit):
    (database, subreddit) = tsdb.TSDB.for_subreddit(subreddit, fix_name=True)

    print('Getting styles for /r/%s' % subreddit)
    subreddit = common.r.subreddit(subreddit)
    styles = subreddit.stylesheet()

    os.makedirs(database.styles_dir.absolute_path, exist_ok=True)

    stylesheet_filepath = database.styles_dir.with_child('stylesheet.css')
    print('Downloading %s' % stylesheet_filepath.relative_path)
    with open(stylesheet_filepath.absolute_path, 'w', encoding='utf-8') as stylesheet:
        stylesheet.write(styles.stylesheet)

    for image in styles.images:
        image_basename = image['name'] + '.' + image['url'].split('.')[-1]
        image_filepath = database.styles_dir.with_child(image_basename)
        print('Downloading %s' % image_filepath.relative_path)
        with open(image_filepath.absolute_path, 'wb') as image_file:
            response = requests.get(image['url'])
            image_file.write(response.content)

def getstyles_argparse(args):
    return getstyles(args.subreddit)
