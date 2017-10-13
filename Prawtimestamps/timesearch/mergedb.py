import os
import requests

from . import common
from . import tsdb


MIGRATE_QUERY = '''
INSERT INTO {tablename}
SELECT othertable.* FROM other.{tablename} othertable
LEFT JOIN {tablename} mytable ON mytable.idint == othertable.idint
WHERE mytable.idint IS NULL;
'''

def _migrate_helper(db, tablename):
    oldcount = db.cur.execute('SELECT count(*) FROM %s' % tablename).fetchone()[0]

    query = MIGRATE_QUERY.format(tablename=tablename)
    print(query)
    db.cur.execute(query)
    db.sql.commit()

    newcount = db.cur.execute('SELECT count(*) FROM %s' % tablename).fetchone()[0]
    print('Gained %d items.' % (newcount - oldcount))

def mergedb(from_db_path, to_db_path):
    to_db = tsdb.TSDB(to_db_path)
    from_db = tsdb.TSDB(from_db_path)

    to_db.cur.execute('ATTACH DATABASE "%s" AS other' % from_db_path)
    _migrate_helper(to_db, 'submissions')
    _migrate_helper(to_db, 'comments')

def mergedb_argparse(args):
    return mergedb(args.from_db_path, args.to_db_path)
