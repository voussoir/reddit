Sticky Comments
===============

[/r/PersonalFinance](http://reddit.com/r/personalfinance) is using some special CSS to make certain comments appear at the top of the thread. This bot will track a designated user / users and sticky every comment they make.

CSS trick here: https://www.reddit.com/r/modclub/comments/2mv444/true_sticky_comments_with_some_css3_magic/cn0li1k

Examples here: https://www.reddit.com/r/GoldTesting/comments/39x5b8/testing_the_biowiki_bot_again/

Seen in stylesheet here: https://www.reddit.com/r/GoldTesting/about/stylesheet/

&nbsp;

If the bot cannot find the anchor text that it needs to find the VIP's name and the sticky ID list, it will remove itself as a moderator so that you may fix the issue.

stickycomments_individual.py keeps the subreddit and username hardcoded. It may be more suitable if you're only running this in a single place.