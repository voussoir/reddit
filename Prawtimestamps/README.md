timesearch.py
=============

It's all fresh all smooth

This creates an sqlite database file containing the submissions on a subreddit within the requested time span. Best when used in conjunction with an SQL viewer or a tool like Redmash to create text files.

If you leave the subreddit blank, it will ask you to enter a username instead. This feature is not 100% perfect yet.

Don't forget to change the Useragent before starting.

============

commentaugment.py
==============

The commentaugment script will take the submissions in one of your timesearch databases, and get their comments. These comments will be packed back into the same database, so be mindful of the item's fullname when you are later doing analysis (t1=comment, t3=submission)

Commentaugment can be very slow, so you may wish to have verbosity=1 to see what's happening.

===============

I want to live in a future where everyone uses UTC and agrees on daylight savings.

<p align="center">
  <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/timesearch_logo_256.png?raw=true" alt="Timesearch"/>
</p>