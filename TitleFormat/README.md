TitleFormat
==========

**USE AUTOMODERATOR INSTEAD**

http://www.reddit.com/r/RequestABot/comments/29ejj3/looking_for_a_bot_for_rsoundcloud_that_forces/cikbe59

This bot will enforce the use of one or more title structures on your subreddit. By adding more entries to `FORMATS` you can add more permitted structures

For example:

"[*] * - *" = "[Genre] Artist - Song Name"

"* (\*) [\*x\*]" = "Martian dude (Colored Pencil) [1920x1080]"

Notice that the asterisks do not care how many words replace them. 

The check is *very* strict, and includes spaces ([pass](http://www.reddit.com/r/GoldTesting/comments/29f08x/genre_title_author/), [fail](http://www.reddit.com/r/GoldTesting/comments/29f0bd/genretitle_author)). You will need to enter additional formats to allow different spacing structures or to allow interchangeable use of parentheses and brackets.

Posts which do not pass the check will be removed with a comment. You could change `.remove()` to `.report()` if you want to be more lenient.