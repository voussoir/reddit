import os
import markdown

from . import common
from . import exceptions
from . import tsdb


HTML_HEADER = '''
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>

<style>
.comment
{
    padding-left: 20px;
    margin-top: 4px;
    margin-right: 4px;
    margin-bottom: 4px;
    border: 2px #000 solid;
}
.submission
{
    border: 4px #00f solid;
    padding-left: 20px;
}
.hidden
{
    display: none;
}
</style>
</head>
<body>
'''.strip()
HTML_FOOTER = '''
</body>

<script>
function toggle_collapse(comment_div)
{
    var button = comment_div.getElementsByClassName("toggle_hide_button")[0];
    var collapsible = comment_div.getElementsByClassName("collapsible")[0];
    if (collapsible.classList.contains("hidden"))
    {
        collapsible.classList.remove("hidden");
        button.innerText = "[-]";
    }
    else
    {
        collapsible.classList.add("hidden");
        button.innerText = "[+]";
    }
}
</script>
</html>
'''

HTML_COMMENT = '''
<div class="comment" id="{id}">
    <p class="userinfo">
        <a
        class="toggle_hide_button"
        href="javascript:void(0)"
        onclick="toggle_collapse(this.parentElement.parentElement)">[-]
        </a>
        {usernamelink}
        <span class="score"> | {score} points</span>
        <span class="timestamp"> | {human}</span>
    </p>
    <div class="collapsible">
        {body}
        <p class="toolbar">
            {permalink}
        </p>
        {{children}}
    </div>
</div>
'''.strip()

HTML_SUBMISSION = '''
<div class="submission" id="{id}">
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
{{children}}
'''.strip()


class DBEntry:
    def __init__(self, fetch):
        if fetch[1].startswith('t3_'):
            columns = tsdb.SQL_SUBMISSION_COLUMNS
            self.object_type = 'submission'
        else:
            columns = tsdb.SQL_COMMENT_COLUMNS
            self.object_type = 'comment'

        self.id = None
        self.idstr = None
        for (index, attribute) in enumerate(columns):
            setattr(self, attribute, fetch[index])

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

    def add_child(self, other_node, overwrite_parent=False):
        self.check_child_availability(other_node.identifier)
        if other_node.parent is not None and not overwrite_parent:
            raise ValueError('That node already has a parent. Try `overwrite_parent=True`')

        other_node.parent = self
        self.children[other_node.identifier] = other_node
        return other_node

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

def html_format_comment(comment):
    text = HTML_COMMENT.format(
        id=comment.idstr,
        body=sanitize_braces(render_markdown(comment.body)),
        usernamelink=html_helper_userlink(comment),
        score=comment.score,
        human=common.human(comment.created),
        permalink=html_helper_permalink(comment),
    )
    return text

def html_format_submission(submission):
    text = HTML_SUBMISSION.format(
        id=submission.idstr,
        title=sanitize_braces(submission.title),
        usernamelink=html_helper_userlink(submission),
        score=submission.score,
        human=common.human(submission.created),
        permalink=html_helper_permalink(submission),
        url_or_text=html_helper_urlortext(submission),
    )
    return text

def html_from_database(subreddit=None, username=None, specific_submission=None):
    '''
    Given a timesearch database filename, produce .html files for each
    of the submissions it contains (or one particular submission fullname)
    '''
    if markdown is None:
        raise ImportError('Page cannot be rendered without the markdown module')

    if not common.is_xor(subreddit, username):
        raise exceptions.NotExclusive(['subreddit', 'username'])

    if subreddit:
        database = tsdb.TSDB.for_subreddit(subreddit, do_create=False)
    else:
        database = tsdb.TSDB.for_user(username, do_create=False)

    submission_trees = trees_from_database(database, specific_submission)
    for submission_tree in submission_trees:
        page = html_from_tree(submission_tree, sort=lambda x: x.data.score * -1)
        os.makedirs(database.offline_reading_dir.absolute_path, exist_ok=True)
        html_basename = '%s.html' % submission_tree.identifier
        html_filepath = database.offline_reading_dir.with_child(html_basename)
        html_handle = open(html_filepath.absolute_path, 'w', encoding='utf-8')
        html_handle.write(HTML_HEADER)
        html_handle.write(page)
        html_handle.write(HTML_FOOTER)
        html_handle.close()
        print('Wrote', html_filepath.relative_path)

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
        link += item.idstr[3:]
    elif item.object_type == 'comment':
        link += '%s/_/%s' % (item.submission[3:], item.idstr[3:])
    link = '<a href="%s">permalink</a>' % link
    return link

def html_helper_urlortext(submission):
    if submission.url:
        text = '<a href="{url}">{url}</a>'.format(url=submission.url)
    elif submission.selftext:
        text = render_markdown(submission.selftext)
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

def render_markdown(text):
    text = markdown.markdown(text, output_format='html5')
    return text

def sanitize_braces(text):
    text = text.replace('{', '{{')
    text = text.replace('}', '}}')
    return text

def trees_from_database(database, specific_submission=None):
    '''
    Given a timesearch database filename, take all of the submission
    ids, take all of the comments for each submission id, and run them
    through `tree_from_submission`.

    Yield each submission's tree as it is generated.
    '''
    cur1 = database.sql.cursor()
    cur2 = database.sql.cursor()

    if specific_submission is None:
        cur1.execute('SELECT idstr FROM submissions ORDER BY created ASC')
        submission_ids = common.fetchgenerator(cur1)
    else:
        specific_submission = 't3_' + specific_submission.split('_')[-1]
        # Insert as a tuple to behave like the sql fetch results
        submission_ids = [(specific_submission, None)]

    found_some_posts = False
    for submission_id in submission_ids:
        # Extract sql fetch
        submission_id = submission_id[0]
        found_some_posts = True
        cur2.execute('SELECT * FROM submissions WHERE idstr == ?', [submission_id])
        submission = cur2.fetchone()
        cur2.execute('SELECT * FROM comments WHERE submission == ?', [submission_id])
        fetched_comments = cur2.fetchall()
        submission_tree = tree_from_submission(submission, fetched_comments)
        yield submission_tree

    if not found_some_posts:
        raise Exception('Found no submissions!')

def tree_from_submission(submission, commentpool):
    '''
    Given the sqlite data for a submission and all of its comments,
    return a tree with the submission id as the root
    '''
    submission = DBEntry(submission)
    commentpool = [DBEntry(c) for c in commentpool]
    commentpool.sort(key=lambda x: x.created)

    print('Building tree for %s (%d comments)' % (submission.idstr, len(commentpool)))
    # Thanks Martin Schmidt for the algorithm
    # http://stackoverflow.com/a/29942118/5430534
    tree = TreeNode(identifier=submission.idstr, data=submission)
    node_map = {}

    for comment in commentpool:
        # Ensure this comment is in a node of its own
        this_node = node_map.get(comment.idstr, None)
        if this_node:
            # This ID was detected as a parent of a previous iteration
            # Now we're actually filling it in.
            this_node.data = comment
        else:
            this_node = TreeNode(comment.idstr, comment)
            node_map[comment.idstr] = this_node

        # Attach this node to the parent.
        if comment.parent.startswith('t3_'):
            tree.add_child(this_node)
        else:
            parent_node = node_map.get(comment.parent, None)
            if not parent_node:
                parent_node = TreeNode(comment.parent, data=None)
                node_map[comment.parent] = parent_node
            parent_node.add_child(this_node)
            this_node.parent = parent_node
    return tree

def offline_reading_argparse(args):
    return html_from_database(
        subreddit=args.subreddit,
        username=args.username,
        specific_submission=args.specific_submission,
    )
