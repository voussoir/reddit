import os
import sqlite3
import types

from . import common
from . import exceptions

from voussoirkit import pathclass


# For backwards compatibility reasons, this list of format strings will help
# timesearch find databases that are using the old filename style.
# The final element will be used if none of the previous ones were found.
DB_FORMATS_SUBREDDIT = [
    '.\\{name}.db',
    '.\\subreddits\\{name}\\{name}.db',
    '.\\{name}\\{name}.db',
    '.\\databases\\{name}.db',
    '.\\subreddits\\{name}\\{name}.db',
]
DB_FORMATS_USER = [
    '.\\@{name}.db',
    '.\\users\\@{name}\\@{name}.db',
    '.\\@{name}\\@{name}.db',
    '.\\databases\\@{name}.db',
    '.\\users\\@{name}\\@{name}.db',
]

DB_INIT = '''
CREATE TABLE IF NOT EXISTS submissions(
    idint INT,
    idstr TEXT,
    created INT,
    self INT,
    nsfw INT,
    author TEXT,
    title TEXT,
    url TEXT,
    selftext TEXT,
    score INT,
    subreddit TEXT,
    distinguish INT,
    textlen INT,
    num_comments INT,
    flair_text TEXT,
    flair_css_class TEXT,
    augmented_at INT,
    augmented_count INT
);
CREATE INDEX IF NOT EXISTS submission_index ON submissions(idstr);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comments(
    idint INT,
    idstr TEXT,
    created INT,
    author TEXT,
    parent TEXT,
    submission TEXT,
    body TEXT,
    score INT,
    subreddit TEXT,
    distinguish TEXT,
    textlen INT
);
CREATE INDEX IF NOT EXISTS comment_index ON comments(idstr);
'''.strip()

SQL_SUBMISSION_COLUMNS = [
    'idint',
    'idstr',
    'created',
    'self',
    'nsfw',
    'author',
    'title',
    'url',
    'selftext',
    'score',
    'subreddit',
    'distinguish',
    'textlen',
    'num_comments',
    'flair_text',
    'flair_css_class',
    'augmented_at',
    'augmented_count',
]

SQL_COMMENT_COLUMNS = [
    'idint',
    'idstr',
    'created',
    'author',
    'parent',
    'submission',
    'body',
    'score',
    'subreddit',
    'distinguish',
    'textlen',
]

SQL_SUBMISSION = {key:index for (index, key) in enumerate(SQL_SUBMISSION_COLUMNS)}
SQL_COMMENT = {key:index for (index, key) in enumerate(SQL_COMMENT_COLUMNS)}


class TSDB:
    def __init__(self, filepath, do_create=True):
        self.filepath = pathclass.Path(filepath)
        if not self.filepath.is_file:
            if not do_create:
                raise exceptions.DBNotFound(self.filepath)
            print('New database', self.filepath.relative_path)

        os.makedirs(self.filepath.parent.absolute_path, exist_ok=True)

        self.breakdown_dir = self.filepath.parent.with_child('breakdown')
        self.offline_reading_dir = self.filepath.parent.with_child('offline_reading')
        self.redmash_dir = self.filepath.parent.with_child('redmash')
        self.styles_dir = self.filepath.parent.with_child('styles')
        self.wiki_dir = self.filepath.parent.with_child('wiki')

        self.sql = sqlite3.connect(self.filepath.absolute_path)
        self.cur = self.sql.cursor()
        statements = DB_INIT.split(';')
        for statement in statements:
            self.cur.execute(statement)
        self.sql.commit()

    def __repr__(self):
        return 'TSDB(%s)' % self.filepath

    @staticmethod
    def _pick_filepath(formats, name):
        '''
        Starting with the most specific and preferred filename format, check
        if there is an existing database that matches the name we're looking
        for, and return that path. If none of them exist, then use the most
        preferred filepath.
        '''
        paths = [pathclass.Path(format.format(name=name)) for format in formats]
        for path in paths:
            if path.is_file:
                return path
        return paths[-1]

    @classmethod
    def for_subreddit(cls, name, do_create=True):
        if isinstance(name, common.praw.models.Subreddit):
            name = name.display_name
        elif not isinstance(name, str):
            raise TypeError(name, 'should be str or Subreddit.')

        filepath = cls._pick_filepath(formats=DB_FORMATS_SUBREDDIT, name=name)
        return cls(filepath=filepath, do_create=do_create)

    @classmethod
    def for_user(cls, name, do_create=True):
        if isinstance(name, common.praw.models.Redditor):
            name = name.name
        elif not isinstance(name, str):
            raise TypeError(name, 'should be str or Redditor.')

        filepath = cls._pick_filepath(formats=DB_FORMATS_USER, name=name)
        return cls(filepath=filepath, do_create=do_create)

    def insert(self, objects, commit=True):
        if not isinstance(objects, (list, tuple, types.GeneratorType)):
            objects = [objects]

        new_values = {
            'new_submissions': 0,
            'new_comments': 0,
        }
        methods = {
            common.praw.models.Submission: (self.insert_submission, 'new_submissions'),
            common.praw.models.Comment: (self.insert_comment, 'new_comments'),
        }
        for obj in objects:
            (method, key) = methods.get(type(obj), (None, None))
            if method is None:
                raise TypeError('Unsupported', type(obj), obj)
            status = method(obj)
            new_values[key] += status

        if commit:
            self.sql.commit()

        return new_values

    def insert_submission(self, submission):
        cur = self.sql.cursor()
        cur.execute('SELECT * FROM submissions WHERE idstr == ?', [submission.fullname])
        existing_entry = cur.fetchone()

        if submission.author is None:
            author = '[DELETED]'
        else:
            author = submission.author.name

        if not existing_entry:
            if submission.is_self:
                # Selfpost's URL leads back to itself, so just ignore it.
                url = None
            else:
                url = submission.url

            postdata = {
                'idint': common.b36(submission.id),
                'idstr': submission.fullname,
                'created': submission.created_utc,
                'self': submission.is_self,
                'nsfw': submission.over_18,
                'author': author,
                'title': submission.title,
                'url': url,
                'selftext': submission.selftext,
                'score': submission.score,
                'subreddit': submission.subreddit.display_name,
                'distinguish': submission.distinguished,
                'textlen': len(submission.selftext),
                'num_comments': submission.num_comments,
                'flair_text': submission.link_flair_text,
                'flair_css_class': submission.link_flair_css_class,
                'augmented_at': None,
                'augmented_count': None,
            }
            (qmarks, bindings) = binding_filler(SQL_SUBMISSION_COLUMNS, postdata, require_all=True)
            query = 'INSERT INTO submissions VALUES(%s)' % qmarks
            cur.execute(query, bindings)

        else:
            if submission.author is None:
                # This post is deleted, therefore its text probably says [deleted] or [removed].
                # Discard that, and keep the data we already had here.
                selftext = existing_entry[SQL_SUBMISSION['selftext']]
            else:
                selftext = submission.selftext

            query = '''
                UPDATE submissions SET
                nsfw = coalesce(?, nsfw),
                score = coalesce(?, score),
                selftext = coalesce(?, selftext),
                distinguish = coalesce(?, distinguish),
                num_comments = coalesce(?, num_comments),
                flair_text = coalesce(?, flair_text),
                flair_css_class = coalesce(?, flair_css_class)
                WHERE idstr == ?
            '''
            bindings = [
                submission.over_18,
                submission.score,
                selftext,
                submission.distinguished,
                submission.num_comments,
                submission.link_flair_text,
                submission.link_flair_css_class,
                submission.fullname
            ]
            cur.execute(query, bindings)

        return existing_entry is None

    def insert_comment(self, comment):
        cur = self.sql.cursor()
        cur.execute('SELECT * FROM comments WHERE idstr == ?', [comment.fullname])
        existing_entry = cur.fetchone()

        if comment.author is None:
            author = '[DELETED]'
        else:
            author = comment.author.name

        if not existing_entry:
            postdata = {
                'idint': common.b36(comment.id),
                'idstr': comment.fullname,
                'created': comment.created_utc,
                'author': author,
                'parent': comment.parent_id,
                'submission': comment.link_id,
                'body': comment.body,
                'score': comment.score,
                'subreddit': comment.subreddit.display_name,
                'distinguish': comment.distinguished,
                'textlen': len(comment.body),
            }
            (qmarks, bindings) = binding_filler(SQL_COMMENT_COLUMNS, postdata, require_all=True)
            query = 'INSERT INTO comments VALUES(%s)' % qmarks
            cur.execute(query, bindings)

        else:
            greasy = ['has been overwritten', 'pastebin.com/64GuVi2F']
            if comment.author is None or any(grease in comment.body for grease in greasy):
                body = existing_entry[SQL_COMMENT['body']]
            else:
                body = comment.body

            query = '''
                UPDATE comments SET
                score = coalesce(?, score),
                body = coalesce(?, body),
                distinguish = coalesce(?, distinguish)
                WHERE idstr == ?
            '''
            bindings = [
                comment.score,
                body,
                comment.distinguished,
                comment.fullname
            ]
            cur.execute(query, bindings)

        return existing_entry is None


def binding_filler(column_names, values, require_all=True):
    '''
    Manually aligning question marks and bindings is annoying.
    Given the table's column names and a dictionary of {column: value},
    return the question marks and the list of bindings in the right order.
    '''
    values = values.copy()
    for column in column_names:
        if column in values:
            continue
        if require_all:
            raise ValueError('Missing column "%s"' % column)
        else:
            values.setdefault(column, None)
    qmarks = '?' * len(column_names)
    qmarks = ', '.join(qmarks)
    bindings = [values[column] for column in column_names]
    return (qmarks, bindings)
