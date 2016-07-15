SubmissionRatio
===

This measures the ratio of users' comments-to-submissions on your subreddit. If a users' ratio falls below a certain threshold, you can receive a message in modmail.

The ratios can then be published to a subreddit [wiki page](http://www.reddit.com/r/GoldTesting/wiki/heyo).

#SETTING UP

Seriously, read this

The first time you run the bot, set MAXPOSTS to 1000 and turn the modmail warning off. This is your initial data collection to start building the database. Once you see "Running again in 20 seconds", shut the bot down, and turn MAXPOSTS back to 100.

Because Reddit only allows us to get [1,000](http://www.reddit.com/r/redditdev/comments/2ffide/listing_old_comments/ck8qlme) submissions and 1,000 comments, there are probably going to be a **TON** of people who didn't make it into your database, or are not fairly represented in your database. For this reason, you may not want to enable the modmail warning until you think the database has enough data.

You should download my wiki.txt file as a starting point, and modify it to your liking. Compare the contents of wiki.txt to [this page](http://www.reddit.com/r/GoldTesting/wiki/heyo) to understand how they match up.