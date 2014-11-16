SchedulizerM
========

Written for [/u/ApexRedditr](http://reddit.com/u/apexredditr) - [Req thread](http://www.reddit.com/r/RequestABot/comments/2m5abs/request_schedule_a_post/)

Enormous overhaul of the Schedulizer system. This bot allows a team of moderators to put "Source Posts" in a centralized subreddit, and the content of those posts will immediately be dispersed at the desired time.

##Creating a Schedule

See screenshot 1

A Source post **must** have three elements - A time to post, a subreddit to post to, and a title to post as, in that order. They must be demarcated by a Separator which is chosen by the bot owner, and is **||** by default. I advise you to never put the separator as part of your title, but you still may be able to.

Additionally, if the bot is a moderator of the subreddit you are scheduling the post to, you may include the following flags in the subreddit section

    [d] - Distinguish the post
    [s] - Sticky the post
    [f:Flair] - Assign the post with flair "Flair"
    [fc:flairclass] - Assign the post with the CSS flair class "flairclass"

Remember that the bot is the one making the post, not you! You will be notified when the post is created, but it will not otherwise be accredited to you. The bot must be a moderator of the chosen subreddit in order to distinguish the post, etc.

You *can* tell the bot to schedule a post in the same subreddit that the schedules are being made in. Why would you do that, though?


.

##Editing Schedules

See screenshot 2 and 3

If the time, subreddit, or title of your source is invalid, it is considered a "critical error". You *must* edit this schedule. Even if a source is valid, you may edit it if you have changed your mind about something.

To edit the schedule, simply reply to the bot's comment with the name of the key you wish to change, a colon, and the new value, like so:

   Key: value

You may only edit one key:value per line. See screenshot 3 for an example.

There is some leniency in your key edits. For example, `flairtext: Heyo`, `flair-text: Heyo`, and `flair_text: Heyo` are all going to do the same thing. Here are the ways you can edit the values.

	Time - 'time', 'timestamp'

	Subreddit - 'reddit', 'subreddit', 'sr'
	
	Title  - 'title'

	Distinguish - 'distinguish', 'dist', 'd'
		'0', 'no', 'false', 'off'
		'1', 'yes', 'true', 'on'

	Sticky - 'sticky', 's'
		'0', 'no', 'false', 'off'
		'1', 'yes', 'true', 'on'

	flair-text 'flair-text', 'flairtext', 'flair_text'

	flair-css 'flair-css', 'flaircss', 'flair_css'


.

##Deleting Schedules

Just delete your source post, and the bot will remove it from the calendar on the next cycle.


.


##Post content

The Post will mimick the Source. Selftext if it was a selfpost, or URL if it was a linkpost. The selftext and url data is NOT collected until the post is actually being made, so you can edit the post content as much as you like without having to notify the bot. Titles must be edited via discourse with the bot.

.

##Screenshots

Click on any image to see the full size

#####1 - A well-made post
<p align="center">
  <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/SchedulizerM_00.png?raw=true" alt="SM"/>
</p>


.


#####2 - Sometimes there are errors. Don't worry, you'll be notified and have plenty of time to fix things.
<p align="center">
  <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/SchedulizerM_01.png?raw=true" alt="SM"/>
</p>


.

#####3 - How to fix multiple errors at once
<p align="center">
  <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/SchedulizerM_02.png?raw=true" alt="SM"/>
</p>