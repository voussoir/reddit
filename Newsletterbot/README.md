Newsletterbot
=============

- 2016 04 15
    - Added broadcast functionality to send a message to all subscribers. Not operable via PM yet.
    - Added deletion functionality to remove inactive users. Everyone must send the bot a message within a certain time span, indicating they are active.

Sends a newsletter to users when their favorite subreddit has a new post.

This bot operates via Private Message correspondence. When sending a message to Newsletterly, the subject does not matter. On each line of the body should be a command and any arguments it needs, separated by spaces. Scroll down to see image examples.

# Commands

## Subscribing
- `subscribe redditdev`
    - Subscribe to /r/redditdev
- `subscribe redditdev, learnpython`
    - Subscribe to both /r/redditdev and /r/learnpython
- `unsubscribe redditdev`
    - Unsubscribe from /r/redditdev
- `unsubscribe redditdev, learnpython`
    - Unsubscribe from both /r/redditdev and /r/learnpython
- `unsubscribe all`
    - Unsubscribe from everything

## Other
- `report`
    - Receive a list of all the subreddits you're subscribed to, including a joined /r/a+b+c link.
- `keep`
    - Very rarely, I will purge inactive users from Newsletterly, so it does not waste API time checking subreddits that nobody is actually using. If you receive a message declaring an upcoming purge, you must send this command to be maintained. Purging is **not** a regular thing and you don't need to worry about it if you're legitimately active.

## Admins only
- `forcesubscribe goldensights.redditdev`
    - Forcefully add /u/goldensights to receive /r/redditdev.
- `forceunsubscribe goldensights.redditdev`
    - Forcefully remove /u/goldensights from /r/redditdev.
- `kill`
    - Completely shut down the bot using Python's `quit()`. The bot's last breath will be a PM to you confirming the action.
- `reportuser goldensights`
    - See the subreddit report for /u/goldensights.
- `reportall`
    - See the reports for every user.

&nbsp;
Receiving a Newsletter:

<p align="center">
  <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/newsletterly_demo_newposts.png?raw=true" alt="Stay tuned."/>
</p>

&nbsp;
Subscribing:
<p align="center">
  <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/newsletterly_demo_subscribe.png?raw=true" alt="Stay tuned."/>
</p>
<p align="center">
  <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/newsletterly_demo_subscribemultiple.png?raw=true" alt="Stay tuned."/>
</p>

&nbsp;
Checking your subscriptions:

<p align="center">
  <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/newsletterly_demo_report.png?raw=true" alt="Stay tuned."/>
</p>

&nbsp;
Composing a message with multiple commands:
<p align="center">
  <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/newsletterly_demo_multiplecompose.png?raw=true" alt="Stay tuned."/>
</p>
<p align="center">
  <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/newsletterly_demo_multipleresponse.png?raw=true" alt="Stay tuned."/>
</p>

&nbsp;
Surviving a purge:
<p align="center">
  <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/newsletterly_purge_keep.png?raw=true" alt="Stay tuned."/>
</p>

Failing a purge:
<p align="center">
  <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/newsletterly_purge_drop.png?raw=true" alt="Stay tuned."/>
</p>

&nbsp;

&nbsp;

<p align="center">
  <img src="https://github.com/voussoir/reddit/blob/master/.GitImages/Newsletterly_cover2.png?raw=true" alt="Stay tuned."/>
</p>