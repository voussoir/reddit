import sqlite3
import sys

SQL_IDINT = 0
SQL_IDSTR = 1
SQL_CREATED = 2
SQL_SELF = 3
SQL_NSFW = 4
SQL_AUTHOR = 5
SQL_TITLE = 6
SQL_URL = 7
SQL_SELFTEXT = 8
SQL_SCORE = 9
SQL_SUBREDDIT = 10
SQL_DISTINGUISHED = 11
SQL_TEXTLEN = 12
SQL_NUM_COMMENTS = 13
SQL_FLAIR_TEXT = 14
SQL_FLAIR_CSS_CLASS = 15

class Generic:
    pass


class TreeNode:
    def __init__(self, identifier, data, parent=None):
        assert isinstance(identifier, str)
        self.identifier = identifier
        self.data = data
        self.parent = parent
        self.children = {}

    def __getitem__(self, key):
        return self.children[key]

    def abspath(self):
        node = self
        nodes = [node]
        while node.parent != None:
            node = node.parent
            nodes.append(node)
        nodes.reverse()
        nodes = [node.identifier for node in nodes]
        return '\\'.join(nodes)

    def addchild(self, identifier, value):
        self.check_child_availability(identifier)
        child = TreeNode(identifier, data=value, parent=self)
        self.children[identifier] = child
        return child

    def check_child_availability(self, identifier):
        if ':' in identifier:
            raise Exception('Only roots may have a colon ')
        if identifier in self.children:
            raise Exception('Node %s already has child %s' % (self.identifier, identifier))

    def listnodes(self, customsort=None):
        items = list(self.children.items())
        if customsort == None:
            items.sort(key=lambda x: x[0].lower())
        else:
            items.sort(key=customsort)
        return [item[1] for item in items]

    def merge_other(self, othertree, otherroot=None):
        newroot = None
        if ':' in othertree.identifier:
            if otherroot == None:
                raise Exception('Must specify a new name for the other tree\'s root')
            else:
                newroot = otherroot
        else:
            newroot = othertree.identifier
        othertree.identifier = newroot
        othertree.parent = self
        self.check_child_availability(newroot)
        self.children[newroot] = othertree

    def printtree(self, customsort=None):
        for node in self.walk(customsort):
            print(node.abspath())

    def walk(self, customsort=None):
        yield self
        for child in self.listnodes(customsort=customsort):
            yield from child.walk()


def fetchgenerator(cursor):
    while True:
        item = cursor.fetchone()
        if item == None:
            break
        yield item

def generic_from_fetch(fetch):
    generic = Generic()
    generic.id = fetch[SQL_IDSTR]
    generic.author = fetch[SQL_AUTHOR]
    generic.created = fetch[SQL_CREATED]
    generic.score = fetch[SQL_SCORE]
    generic.text = fetch[SQL_SELFTEXT]
    if 't1_' in generic.id:
        generic.parent = fetch[SQL_TITLE]
    return generic

def tree_from_submission_comments(submission, commentpool):
    submission = generic_from_fetch(submission)
    commentpool = [generic_from_fetch(c) for c in commentpool]
    commentpool.sort(key=lambda x: x.created)
    
    print('Building tree for %s (%d comments)' % (submission.id, len(commentpool)))
    tree = TreeNode(submission.id, submission)
    while len(commentpool) > 0:
        removals = []
        for comment in commentpool:
            for node in tree.walk():
                if comment.parent == node.data.id:
                    node.addchild(comment.id, comment)
                    removals.append(comment)
                    break
        for removal in removals:
            commentpool.remove(removal)
    return tree

def tree_from_database(databasename, specific_submission=None):
    sql = sqlite3.connect(databasename)
    cur = sql.cursor()
    cur2 = sql.cursor()
    if specific_submission != None:
        if specific_submission[:3] != 't3_':
            specific_submission = 't3_' + specific_submission
        submission_ids = [specific_submission]
        generated = False
    else:
        cur2.execute('SELECT * FROM posts WHERE idstr LIKE "t3_%" ORDER BY created ASC')
        submission_ids = fetchgenerator(cur2)
        generated = True

    totaltree = TreeNode(':', None)
    for submission_id in submission_ids:
        if generated:
            submission = submission_id
            submission_id = submission_id[1]
        else:
            cur.execute('SELECT * FROM posts WHERE idstr==?', [submission_id])
            submission = cur.fetchone()
        cur.execute('SELECT * FROM posts WHERE url==?', [submission_id])
        fetched_comments = cur.fetchall()
        submissiontree = tree_from_submission_comments(submission, fetched_comments)        
        totaltree.merge_other(submissiontree)
    return totaltree

#totaltree = tree_from_database('databases\\botwatch.db')
#totaltree.printtree(customsort=lambda x: int(x[1].data.created, 36))
if __name__ == '__main__':
    databasename = sys.argv[1]
    try:
        specific_submission = sys.argv[2]
    except IndexError:
        specific_submission = None
    t = tree_from_database(databasename, specific_submission)
    t.printtree()