timesearch.py
=============

- 2016 07 03
    - Improved docstring clarity.

- 2016 07 02
    - Added `livestream` argparse

- 2016 06 07
    - Offline_reading has been merged with the main timesearch file
    - `get_all_posts` renamed to `timesearch`
    - Timesearch parameter `usermode` renamed to `username`; `maxupper` renamed to `upper`.
    - Everything now accessible via commandline arguments. Read the docstring at the top of the file.

- 2016 06 05
    - NEW DATABASE SCHEME. Submissions and comments now live in different tables like they should have all along. Submission table has two new columns for a little bit of commentaugment metadata. This allows commentaugment to only scan threads that are new.
    - You can use the `migrate_20160605.py` script to convert old databases into new ones.

- 2015 11 11
    - created `offline_reading.py` which converts a timesearch database into a comment tree that can be rendered into HTML

- 2015 09 07
    - fixed bug which allowed `livestream` to crash because `bot.refresh()` was outside of the try-catch.

- 2015 08 19
    - fixed bug in which updatescores stopped iterating early if you had more than 100 comments in a row in the db
    - commentaugment has been completely merged into the timesearch.py file. you can use commentaugment_prompt() to input the parameters, or use the commentaugment() function directly.

&nbsp;

It's all fresh all smooth

This creates an sqlite database file containing the submissions on a subreddit within the requested time span. Best when used in conjunction with an SQL viewer or a tool like Redmash to create text files.

If you leave the subreddit blank, it will ask you to enter a username instead. This feature is not as perfect as subreddit scanning due to API limitations.

Don't forget to change the Useragent before starting.

============


I want to live in a future where everyone uses UTC and agrees on daylight savings.

<p align="center">
    <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/timesearch_logo_256.png?raw=true" alt="Timesearch"/>
</p>
