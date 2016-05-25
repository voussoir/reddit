import datetime
import markdown
import os
import re
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

HTML_FOLDER = 'html'


class DBEntry:
    def __init__(self, fetch):
        self.id = fetch[SQL_IDSTR]
        self.author = fetch[SQL_AUTHOR]
        self.created = fetch[SQL_CREATED]
        self.score = fetch[SQL_SCORE]
        self.text = fetch[SQL_SELFTEXT]
        self.subreddit = fetch[SQL_SUBREDDIT]
        self.distinguished = fetch[SQL_DISTINGUISHED]
        if 't1_' in self.id:
            self.object_type = 'comment'
            self.parent = fetch[SQL_TITLE]
            self.submission = fetch[SQL_URL]
        else:
            self.title = fetch[SQL_TITLE]
            self.url = fetch[SQL_URL]
            self.object_type = 'submission'

    def __repr__(self):
        return 'DBEntry(\'%s\')' % self.id


class TreeNode:
    def __init__(self, identifier, data, parent=None):
        assert isinstance(identifier, str)
        assert '\\' not in identifier
        self.identifier = identifier
        self.data = data
        self.parent = parent
        self.children = {}

    def __getitem__(self, key):
        return self.children[key]

    def __repr__(self):
        return 'TreeNode %s' % self.abspath()

    def abspath(self):
        node = self
        nodes = [node]
        while node.parent is not None:
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
            raise Exception('Only roots may have a colon')
        if identifier in self.children:
            raise Exception('Node %s already has child %s' % (self.identifier, identifier))

    def detach(self):
        del self.parent.children[self.identifier]
        self.parent = None

    def listnodes(self, customsort=None):
        items = list(self.children.items())
        if customsort is None:
            items.sort(key=lambda x: x[0].lower())
        else:
            items.sort(key=customsort)
        return [item[1] for item in items]

    def merge_other(self, othertree, otherroot=None):
        newroot = None
        if ':' in othertree.identifier:
            if otherroot is None:
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
            #print(child)
            #print(child.listnodes())
            yield from child.walk(customsort=customsort)


def fetchgenerator(cursor):
    while True:
        item = cursor.fetchone()
        if item is None:
            break
        yield item

def html_format_comment(comment):
    text = '''
    <div class="comment"
        id="{id}" 
        style="
        padding-left: 20px;
        margin-top: 4px;
        margin-right: 4px;
        margin-bottom: 4px;
        border: 2px #000 solid;
    ">
        <p class="userinfo">
            {usernamelink}
            <span class="score"> | {score} points</span>
            <span class="timestamp"> | {human}</span>
        </p>

        <p>{text}</p>

        <p class="toolbar">
            {permalink}
        </p>
    {children}
    </div>
    '''.format(
        id = comment.id,
        text = sanitize_braces(render_markdown(comment.text)),
        usernamelink = html_helper_userlink(comment),
        score = comment.score,
        human = human(comment.created),
        permalink = html_helper_permalink(comment),
        children = '{children}',
    )
    return text

def html_format_submission(submission):
    text = '''
    <div class="submission"
        id="{id}" 
        style="
        border: 4px #00f solid;
        padding-left: 20px;
    ">

        <p class="userinfo">
            {usernamelink}
            <span class="score"> | {score} points</span>
            <span class="timestamp"> | {human}</span>
        </p>

        <strong>{title}</strong>
        <p>{url_or_text}</p>

        <p class="toolbar">
            {permalink}
        </p>
    </div>
    {children}
    '''.format(
        id = submission.id,
        title = sanitize_braces(submission.title),
        usernamelink = html_helper_userlink(submission),
        score = submission.score,
        human = human(submission.created),
        permalink = html_helper_permalink(submission),
        url_or_text = html_helper_urlortext(submission),
        children = '{children}',
    )
    return text

def html_from_database(databasename, specific_submission=None):
    '''
    Given a timesearch database filename, produce .html files for each
    of the submissions it contains (or one particular submission fullname)
    '''
    submission_trees = trees_from_database(databasename, specific_submission)
    for submission_tree in submission_trees:
        page = html_from_tree(submission_tree, sort=lambda x: x.data.score * -1)
        if not os.path.exists(HTML_FOLDER):
            os.makedirs(HTML_FOLDER)
        html_basename = '%s.html' % submission_tree.identifier
        html_filename = os.path.join(HTML_FOLDER, html_basename)
        html_handle = open(html_filename, 'w', encoding='utf-8')
        html_handle.write('<html><body><meta charset="UTF-8">')
        html_handle.write(page)
        html_handle.write('</body></html>')
        html_handle.close()

def html_from_tree(tree, sort=None):
    '''
    Given a tree *whose root is the submission*, return
    HTML-formatted text representing each submission's comment page.
    '''
    if tree.data.object_type == 'submission':
        page = html_format_submission(tree.data)
    elif tree.data.object_type == 'comment':
        page = html_format_comment(tree.data)
    children = tree.listnodes()
    if sort is not None:
        children.sort(key=sort)
    children = [html_from_tree(child, sort) for child in children]
    if len(children) == 0:
        children = ''
    else:
        children = '\n\n'.join(children)
    try:
        page = page.format(children=children)
    except IndexError:
        print(page)
        raise
    return page

def html_helper_permalink(item):
    link = 'https://www.reddit.com/r/%s/comments/' % item.subreddit
    if item.object_type == 'submission':
        link += item.id[3:]
    elif item.object_type == 'comment':
        link += '%s/_/%s' % (item.submission[3:], item.id[3:])
    link = '<a href="%s">permalink</a>' % link
    return link

def html_helper_urlortext(submission):
    if submission.url:
        text = '<a href="{url}">{url}</a>'.format(url=submission.url)
    elif submission.text:
        text = render_markdown(submission.text)
    else:
        text = ''
    text = sanitize_braces(text)
    return text

def html_helper_userlink(item):
    name = item.author
    if name.lower() == '[deleted]':
        return '[deleted]'
    link = 'https://www.reddit.com/u/{name}'
    link = '<a href="%s">{name}</a>' % link
    link = link.format(name=name)
    return link

def human(timestamp):
    x = datetime.datetime.utcfromtimestamp(timestamp)
    x = datetime.datetime.strftime(x, "%b %d %Y %H:%M:%S")
    return x

def render_markdown(text):
    text = markdown.markdown(text, output_format='html5')
    return text

def sanitize_braces(text):
    text = text.replace('{', '{{')
    text = text.replace('}', '}}')
    return text

def trees_from_database(databasename, specific_submission=None):
    '''
    Given a timesearch database filename, take all of the submission
    ids, take all of the comments for each submission id, and run them
    through `tree_from_submission_comments`.

    Yield each submission's tree as it is generated.
    '''
    sql = sqlite3.connect(databasename)
    cur = sql.cursor()
    cur2 = sql.cursor()
    if specific_submission is not None:
        if specific_submission[:3] != 't3_':
            specific_submission = 't3_' + specific_submission
        submission_ids = [specific_submission]
        generated = False
    else:
        cur2.execute('SELECT * FROM posts WHERE idstr LIKE "t3_%" ORDER BY created ASC')
        submission_ids = fetchgenerator(cur2)
        generated = True

    found_some_posts = False
    for submission_id in submission_ids:
        found_some_posts = True
        if generated:
            submission = submission_id
            submission_id = submission_id[1]
        else:
            cur.execute('SELECT * FROM posts WHERE idstr==?', [submission_id])
            submission = cur.fetchone()
        cur.execute('SELECT * FROM posts WHERE url==?', [submission_id])
        fetched_comments = cur.fetchall()
        submission_tree = tree_from_submission_comments(submission, fetched_comments)
        yield submission_tree
    if found_some_posts is False:
        raise Exception('Found no submissions!')

def tree_from_submission_comments(submission, commentpool):
    '''
    Given the sqlite data for a submission and all of its comments,
    return a tree with the submission id as the root
    '''
    submission = DBEntry(submission)
    commentpool = [DBEntry(c) for c in commentpool]
    commentpool.sort(key=lambda x: x.created)
    
    print('Building tree for %s (%d comments)' % (submission.id, len(commentpool)))
    tree = TreeNode(submission.id, submission)
    while len(commentpool) > 0:
        removals = []
        for comment in commentpool:
            foundparent = False
            for node in tree.walk():
                if comment.parent == node.data.id:
                    node.addchild(comment.id, comment)
                    removals.append(comment)
                    foundparent = True
                    break
            if foundparent is False:
                removals.append(comment)
                continue
        for removal in removals:
            commentpool.remove(removal)
    return tree

if __name__ == '__main__':
    databasename = sys.argv[1]
    try:
        specific_submission = sys.argv[2]
    except IndexError:
        specific_submission = None
    html_from_database(databasename, specific_submission)