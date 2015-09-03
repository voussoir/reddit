reddit
======

A collection of reddit bots and utilities, all written by /u/GoldenSights. Many of these are done via /r/botrequests+requestabot, and some are done on a whim.
_______
###Before running any of my bots

[Read this.](http://www.reddit.com/r/GoldTesting/comments/26r2ob/how_to_install_and_use_a_python_reddit_bot/)

Do not put multiple programs in the same folder. They use SQL databases to store information and you musn't allow them to mix. You can always edit `sql = sqlite3.connect('sql.db')` to use a different filename for the database, but folders are nice.

**Use descriptive useragents**. Include a username by which admins can identify you. Tell what your bot is doing and why. Convince the admins that you aren't wasting their bandwidth. Inadequate useragents may cause your bot to get logged out in the middle of your session, and the program will crash. Abusive useragents can get your bot shadowbanned.

[Reddit API rules](https://github.com/reddit/reddit/wiki/API)


________



###Bot.py

In a lot of my bots, you'll see 

    import bot
    USERAGENT = bot.aG

etc. This is a file in my python library which contains my bot's oauth credentials. I use this system so that I can push this code to git without worrying about my stuff being seen.

To create your own bot.py is very simple. It's just a regular .py file which you save in C:\Python34\Lib\. Then you just enter some variables

`username = "robot"`

`password = "12345"`

Now, when you `import bot`, you can type `bot.username` and get "robot". You can create as many variables as you want, including useragents and multiple account credentials.