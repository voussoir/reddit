MailMe
=============

This bot works on the same premise as ReplyBot, but instead of replying to the comments you find, it will send you a PM with a permalink to the comment that included your keyword.

Also works on submissions. See the `DO_SUBMISSIONS` variable.

NOTE: MailMe does not want to send mail if the comment that it finds was written by you or the bot. However, without the `identity` OAuth scope, the bot cannot retrieve its own username. This will not be a problem if you don't have the bot writing comments, but just be aware.