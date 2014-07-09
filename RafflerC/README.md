Raffler (Comments)
==========

This is a utility rather than a bot. 

- Give it the permalink or the id number of a thread. If you hit Enter without typing anything, it will take whatever is in your clipboard.

- It finds the submission object, and pulls all of the root comments. 

- They are put into a .txt file with the oldest comment at the top, numbered starting from 1. Multiple comments by the same user will not be considered. 

- The report will suggest a random user to you, but you could use [Random.org](http://random.org) for true-random instead.

Gathering the comments can take a very long time on big threads. In order to ensure fairness, the script will grab *every single comment* in the thread. Every time you see the "load more comments" button in a thread, that's where the bot needs to spend an additional 2 seconds to get them. Just let it run.
