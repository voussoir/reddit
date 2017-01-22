SourceIt
==========

When a user makes a post in the subreddit, he has a certain amount of time to provide a comment describing the post or providing a source. If he does not, the post will be removed and a warning left.

[This](http://www.reddit.com/r/GoldTesting/comments/26wjq1/red/) post met the requirement. [This](http://www.reddit.com/r/GoldTesting/comments/26whfo/pyre/) one didn't.

________
As of reddit 21, sourceit.py has received a major upgrade. The original is available as s.py in case there are bugs in the new one.

**New Things**:

- Minimum length enforcement. MINLENGTH is how long the person's comment must be. 0 would mean any comment is okay
- If a comment is not found, and there is time left, nothing happens
- If a comment is not found, and there is no time left, the post is removed with a note from the mods

- If a comment is found, and there is time left, but the comment is too short, they receive a warning
- If a comment is found, and there is no time left, and it is too short, the post will be reported. A moderator may decide if the short comment is okay.
- If a comment is found, and meets all requirements, nothing happens and the post passes.
