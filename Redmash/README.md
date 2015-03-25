REDMASH
==========

While the other version may work, I only care about redmash_db currently.

This reads from an sqlite database and outputs into either .txt or .html a listing of all the submissions in the database sorted by date, score, title, author, and flair. The database must be of the form produced by my other script, Prawtimestamps, as they are meant to work best together.

If the database filename starts with "@", it is assumed to be a database representing a user's posts instead of a subreddit. This ties in with the update to prawtimestamps that allows for getting user posts.

If you set the output filename to be a ".json" file, the script will not Mash the data, but instead produce a breakdown by subreddit, to be used in conjunction with @user databases.

You can run the script with commandline parameters to skip all of the input steps. `redmash_db.py database output scorethreshold`