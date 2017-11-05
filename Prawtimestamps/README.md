timesearch
=============

I don't have a test suite. You're my test suite! Messages go to [/u/GoldenSights](https://reddit.com/u/GoldenSights).

Timesearch is a collection of utilities for archiving subreddits.

### Make sure you have:
- Installed [Python](https://www.python.org/download). I use Python 3.6.
- Installed PRAW >= 4, as well as the other modules in `requirements.txt`. Try `pip install -r requirements.txt` to get them all.
- Created an OAuth app at https://reddit.com/prefs/apps. Make it `script` type, and set the redirect URI to `http://localhost:8080`. The title and description can be anything you want, and the about URL is not required.
- Used [this PRAW script](https://praw.readthedocs.io/en/latest/tutorials/refresh_token.html) to generate a refresh token. Just save it as a .py file somewhere and run it through your terminal / command line. For simplicity's sake, I just choose `all` for the scopes.
- Downloaded a copy of [this file](https://github.com/voussoir/reddit/blob/master/bot4.py) and saved it as `bot.py`. Fill out the variables using your OAuth information, and read the instructions to see where to put it. The Useragent is a description of your API usage. Typically "/u/username's praw client" is sufficient.

### This package consists of:

- **timesearch**: If you try to page through `/new` on a subreddit, you'll hit a limit at or before 1,000 posts. Timesearch uses the `timestamp` cloudsearch query parameter to step from the beginning of a subreddit to present time, to collect as many submissions as possible. Read more about timestamp searching [here](https://www.reddit.com/r/reddittips/comments/2ix73n/use_cloudsearch_to_search_for_posts_on_reddit/).  
    `> timesearch.py timesearch -r subredditname <flags>`  
    `> timesearch.py timesearch -u username <flags>`

- **commentaugment**: Although we can search for submissions, we cannot search for comments. After performing a timesearch, you can use commentaugment to download the comment tree for each submission.  
    Note: commentaugment only gets the comments attached to the submissions that you found in your timesearch scan. If you're trying to commentaugment on a user, you're going to get comments that were made on their submissions, **not** comments they made on other people's submissions. Therefore, comprehensively collecting a user's activity is not possible. You will have to use someone else's dataset like that of [/u/Stuck_in_the_Matrix](https://reddit.com/u/Stuck_in_the_Matrix) at [pushshift.io](https://pushshift.io).  
    `> timesearch.py commentaugment -r subredditname <flags>`  
    `> timesearch.py commentaugment -u username <flags>`

- **livestream**: timesearch+commentaugment is great for starting your database and getting historical posts, but it's not the best for staying up-to-date. Instead, livestream monitors `/new` and `/comments` to continuously ingest data.  
    `> timesearch.py livestream -r subredditname <flags>`  
    `> timesearch.py livestream -u username <flags>`

- **getstyles**: Downloads the stylesheet and CSS images.  
    `> timesearch.py getstyles -r subredditname`

- **getwiki**: Downloads the wiki pages, sidebar, etc. from /wiki/pages.  
    `> timesearch.py getwiki -r subredditname`

- **offline_reading**: Renders comment threads into HTML via markdown.  
    Note: I'm currently using the [markdown library from pypi](https://pypi.python.org/pypi/Markdown), and it doesn't do reddit's custom markdown like `/r/` or `/u/`, obviously. So far I don't think anybody really uses o_r so I haven't invested much time into improving it.  
    `> timesearch.py offline_reading -r subredditname <flags>`  
    `> timesearch.py offline_reading -u username <flags>`

- **redmash**: Generates plaintext or HTML lists of submissions, sorted by a property of your choosing. You can order by date, author, flair, etc.  
    `> timesearch.py redmash -r subredditname <flags>`  
    `> timesearch.py redmash -u username <flags>`

- **breakdown**: Produces a JSON file indicating which users make the most posts in a subreddit, or which subreddits a user posts in.  
    `> timesearch.py breakdown -r subredditname` <flags>  
    `> timesearch.py breakdown -u username` <flags>

- **mergedb**: Copy all new data from one timesearch database into another. Useful for syncing or merging two scans of the same subreddit.  
    `> timesearch.py mergedb --from filepath/database1.db --to filepath/database2.db`

### To use it

You'll want to download the `timesearch.py` file, as well as the entire `timesearch` directory, as it is a package. The .py file and the package should be siblings as they are seen here. On GitHub you can't download a folder as a zip so you'll have to visit each file and download them individually. Sorry.

When you run the .py file, it imports the package and sends it your commandline arguments. You can view a summarized version of all the docstrings with just `timesearch.py`, or you can view a specific docstring with `timesearch.py livestream`, etc.

I recommend [sqlitebrowser](https://github.com/sqlitebrowser/sqlitebrowser/releases) if you want to inspect the database yourself.

### Changelog
- 2017 11 04
    - For timesearch, I switched from using my custom cloudsearch iterator to the one that comes with PRAW4+.

- 2017 10 12
    - Added the `mergedb` utility for combining databases.

- 2017 06 02
    - You can use `commentaugment -s abcdef` to get a particular thread even if you haven't scraped anything else from that subreddit. Previously `-s` only worked if the database already existed and you specified it via `-r`. Now it is inferred from the submission itself.

- 2017 04 28
    - Complete restructure into package, started using PRAW4.

- 2016 08 10
    - Started merging redmash and wrote its argparser

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


____


I want to live in a future where everyone uses UTC and agrees on daylight savings.

<p align="center">
    <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/timesearch_logo_256.png?raw=true" alt="Timesearch"/>
</p>
