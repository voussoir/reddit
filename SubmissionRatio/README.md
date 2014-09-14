SubmissionRatio
===

This measures the ratio of users' comments-to-submissions on your subreddit. If a users' ratio falls below a certain threshold, you may enact one or more punishments -- reporting, removing, or commenting.

The ratios can then be published to a subreddit [wiki page](http://www.reddit.com/r/GoldTesting/wiki/heyo).

#SETTING UP

Seriously, read this

The first time you run the bot, set MAXPOSTS to 1000 and turn all of the punishments to False. This is your initial data collection to start building the database. Once you see "Running again in 20 seconds", shut the bot down, and turn MAXPOSTS back to 100. Leave punishments off.

Because Reddit only allows us to get [1,000](http://www.reddit.com/r/redditdev/comments/2ffide/listing_old_comments/ck8qlme) submissions and 1,000 comments, there are probably going to be a **TON** of people who didn't make it into your database, or are not fairly represented in your database. For this reason, you should not enable punishments until after the bot has been running a very long time, or you'll be punishing people who haven't been around for a while and who were not seen by the bot in the first few days.

You may use AddUser.py to scan a user's profile for material in your subreddit to augment what the bot was able to collect. This is subject to the same 1k limits, but may pick up the scraps.

You may use ChangeUser.py to manually enter a user's information, but you need to run AddUser on him first.

You should download my wiki.txt file as a starting point, and modify it if you're feeling brave. Compare the contents of wiki.txt to [this page](http://www.reddit.com/r/GoldTesting/wiki/heyo) to understand how they match up.