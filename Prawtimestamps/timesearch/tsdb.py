import os
import sqlite3
import time
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

DATABASE_VERSION = 1
DB_INIT = '''
PRAGMA user_version = {user_version};
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS config(
    key TEXT,
    value TEXT
);
----------------------------------------------------------------------------------------------------
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
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS submission_edits(
    idstr TEXT,
    previous_selftext TEXT,
    replaced_at INT
);
CREATE INDEX IF NOT EXISTS submission_edits_index ON submission_edits(idstr);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comment_edits(
    idstr TEXT,
    previous_body TEXT,
    replaced_at INT
);
CREATE INDEX IF NOT EXISTS comment_edits_index ON comment_edits(idstr);
'''.format(user_version=DATABASE_VERSION)

DEFAULT_CONFIG = {
    'store_edits': True,
}

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

SQL_EDITS_COLUMNS = [
    'idstr',
    'text',
    'replaced_at',
]

SQL_SUBMISSION = {key:index for (index, key) in enumerate(SQL_SUBMISSION_COLUMNS)}
SQL_COMMENT = {key:index for (index, key) in enumerate(SQL_COMMENT_COLUMNS)}


class TSDB:
    def __init__(self, filepath, do_create=True):
        self.filepath = pathclass.Path(filepath)
        if not self.filepath.is_file:
            if not do_create:
                raise exceptions.DatabaseNotFound(self.filepath)
            print('New database', self.filepath.relative_path)

        os.makedirs(self.filepath.parent.absolute_path, exist_ok=True)

        self.breakdown_dir = self.filepath.parent.with_child('breakdown')
        self.offline_reading_dir = self.filepath.parent.with_child('offline_reading')
        self.redmash_dir = self.filepath.parent.with_child('redmash')
        self.styles_dir = self.filepath.parent.with_child('styles')
        self.wiki_dir = self.filepath.parent.with_child('wiki')

        existing_database = self.filepath.exists
        self.sql = sqlite3.connect(self.filepath.absolute_path)
        self.cur = self.sql.cursor()

        if existing_database:
            self.cur.execute('PRAGMA user_version')
            existing_version = self.cur.fetchone()[0]
            if existing_version > 0 and existing_version != DATABASE_VERSION:
                raise exceptions.DatabaseOutOfDate(current=existing_version, new=DATABASE_VERSION)

        statements = DB_INIT.split(';')
        for statement in statements:
            self.cur.execute(statement)
        self.sql.commit()

        self.config = {}
        for (key, default_value) in DEFAULT_CONFIG.items():
            self.cur.execute('SELECT value FROM config WHERE key == ?', [key])
            existing_value = self.cur.fetchone()
            if existing_value is None:
                self.cur.execute('INSERT INTO config VALUES(?, ?)', [key, default_value])
                self.config[key] = default_value
            else:
                existing_value = existing_value[0]
                if isinstance(default_value, int):
                    existing_value = int(existing_value)
                self.config[key] = existing_value

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
        for form in formats:
            path = form.format(name=name)
            if os.path.isfile(path):
                break
        return pathclass.Path(path)

    @classmethod
    def _for_object_helper(cls, name, path_formats, do_create=True, fix_name=False):
        if name != os.path.basename(name):
            filepath = pathclass.Path(name)

        else:
            filepath = cls._pick_filepath(formats=path_formats, name=name)

        database = cls(filepath=filepath, do_create=do_create)
        if fix_name:
            return (database, name_from_path(name))
        return database

    @classmethod
    def for_subreddit(cls, name, do_create=True, fix_name=False):
        if isinstance(name, common.praw.models.Subreddit):
            name = name.display_name
        elif not isinstance(name, str):
            raise TypeError(name, 'should be str or Subreddit.')
        return cls._for_object_helper(
            name,
            do_create=do_create,
            fix_name=fix_name,
            path_formats=DB_FORMATS_SUBREDDIT,
        )

    @classmethod
    def for_user(cls, name, do_create=True, fix_name=False):
        if isinstance(name, common.praw.models.Redditor):
            name = name.name
        elif not isinstance(name, str):
            raise TypeError(name, 'should be str or Redditor.')

        return cls._for_object_helper(
            name,
            do_create=do_create,
            fix_name=fix_name,
            path_formats=DB_FORMATS_USER,
        )

    def check_for_edits(self, obj, existing_entry):
        '''
        If the item's current text doesn't match the stored text, decide what
        to do.

        Firstly, make sure to ignore deleted comments.
        Then, if the database is configured to store edited text, do so.
        Finally, return the body that we want to store in the main table.
        '''
        if isinstance(obj, common.praw.models.Submission):
            existing_body = existing_entry[SQL_SUBMISSION['selftext']]
            body = obj.selftext
        else:
            existing_body = existing_entry[SQL_COMMENT['body']]
            body = obj.body

        if body != existing_body:
            if should_keep_existing_text(obj):
                body = existing_body
            elif self.config['store_edits']:
                self.insert_edited(obj, old_text=existing_body)
        return body

    def insert(self, objects, commit=True):
        if not isinstance(objects, (list, tuple, types.GeneratorType)):
            objects = [objects]
        common.log.debug('Trying to insert %d objects.', len(objects))

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
            common.log.debug('Committing insert')
            self.sql.commit()

        common.log.debug('Done inserting.')
        return new_values

    def insert_edited(self, obj, old_text):
        '''
        Having already detected that the item has been edited, add a record to
        the appropriate *_edits table containing the text that is being
        replaced.
        '''
        if isinstance(obj, common.praw.models.Submission):
            table = 'submission_edits'
        else:
            table = 'comment_edits'

        if obj.edited is False:
            replaced_at = int(time.time())
        else:
            replaced_at = int(obj.edited)

        postdata = {
            'idstr': obj.fullname,
            'text': old_text,
            'replaced_at': replaced_at,
        }
        cur = self.sql.cursor()
        (qmarks, bindings) = binding_filler(SQL_EDITS_COLUMNS, postdata, require_all=True)
        query = 'INSERT INTO %s VALUES(%s)' % (table, qmarks)
        cur.execute(query, bindings)

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
            selftext = self.check_for_edits(submission, existing_entry=existing_entry)

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
            body = self.check_for_edits(comment, existing_entry=existing_entry)

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

def name_from_path(filepath):
    '''
    In order to support usage like
    > timesearch livestream -r D:\\some\\other\\filepath\\learnpython.db
    this function extracts the subreddit name / username based on the given
    path, so that we can pass it into `r.subreddit` / `r.redditor` properly.
    '''
    if isinstance(filepath, pathclass.Path):
        filepath = filepath.basename
    else:
        filepath = os.path.basename(filepath)
    name = os.path.splitext(filepath)[0]
    name = name.strip('@')
    return name

def should_keep_existing_text(obj):
    '''
    Under certain conditions we do not want to update the entry in the db
    with the most recent copy of the text. For example, if the post has
    been deleted and the text now shows '[deleted]' we would prefer to
    keep whatever we already have.

    This function puts away the work I would otherwise have to duplicate
    for both submissions and comments.
    '''
    body = obj.selftext if isinstance(obj, common.praw.models.Submission) else obj.body
    if obj.author is None and body in ['[removed]', '[deleted]']:
        return True

    greasy = ['has been overwritten', 'pastebin.com/64GuVi2F']
    if any(grease in body for grease in greasy):
        return True

    return False
