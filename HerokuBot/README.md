Using Heroku to run a bot
=============

[Thank you /u/cmd-t for helping me to finally understand this](http://www.reddit.com/r/botwatch/comments/34dpku/can_someone_write_a_complete_idiots_guide_to/cqts1tr)

Inside git.zip is the .git repo that I created for this. I had to zip it so that I can push it here.

1. Create a [Heroku account](http://heroku.com)
2. Install [Heroku toolbelt](https://toolbelt.heroku.com/)
3. Install [Git](http://git-scm.com/)
4. Create a folder to keep your repo
5. cd into this folder
5. Write your bot
6. Create requirements.txt, and require a version of praw
7. Create runtime.txt, and require a version of Python
8. Create Procfile, and create a worker that will launch your bot.
9. `> heroku login`
10. `> git init`
11. `> git add .`
12. `> git commit -m "1"`
13. `> heroku create`

        Creating aqueous-plains-9797... done, stack is cedar-14
	    https://aqueous-plains-9797.herokuapp.com/ | https://git.heroku.com/aqueous-plains-9797.git
	    Git remote heroku added
14. `> git push heroku master`

	    Counting objects: 10, done.
	    Delta compression using up to 4 threads.
	    Compressing objects: 100% (7/7), done.
	    Writing objects: 100% (10/10), 1.06 KiB, done.
	    Total 10 (delta 1), reused 0 (delta 0)
	    remote: Compressing source files... done.
	    remote: Building source:
	    remote:
	    remote: -----> Python app detected
	    remote: -----> Installing runtime (python-3.4.2)
	    remote: -----> Installing dependencies with pip
	    remote:        Collecting praw>=2.1.21 (from -r requirements.txt (line 1))
	    remote:          Downloading praw-2.1.21-py2.py3-none-any.whl (75kB)
	    remote:        Collecting requests>=2.3.0 (from praw>=2.1.21->-r requirements.txt (line 1))
	    remote:          Downloading requests-2.6.2-py2.py3-none-any.whl (470kB)
	    remote:        Collecting update-checker>=0.11 (from praw>=2.1.21->-r requirements.txt (line 1))
	    remote:          Downloading update_checker-0.11-py2.py3-none-any.whl
	    remote:        Collecting six>=1.4 (from praw>=2.1.21->-r requirements.txt (line 1))
	    remote:          Downloading six-1.9.0-py2.py3-none-any.whl
	    remote:        Installing collected packages: six, update-checker, requests, praw
	    remote:
	    remote:
	    remote:
	    remote:
	    remote:        Successfully installed praw-2.1.21 requests-2.6.2 six-1.9.0 update-checker-0.11
	    remote:
	    remote: -----> Discovering process types
	    remote:        Procfile declares types -> worker
	    remote:
	    remote: -----> Compressing... done, 38.3MB
	    remote: -----> Launching... done, v3
	    remote:        https://aqueous-plains-9797.herokuapp.com/ deployed to Heroku
	    remote:
	    remote: Verifying deploy... done.
	    To https://git.heroku.com/aqueous-plains-9797.git
	     * [new branch]      master -> master
15. `> heroku ps:scale worker=1`

        Scaling dynos... done, now running worker at 1:1X.
16. `> heroku logs > logs.txt`

	    2015-05-01T00:32:38.691805+00:00 app[worker.1]: Logging in.
	    2015-05-01T00:32:41.396117+00:00 app[worker.1]: Getting subreddit info.
	    2015-05-01T00:32:41.397202+00:00 app[worker.1]: /r/Goldtesting
	    2015-05-01T00:32:45.316887+00:00 app[worker.1]: 	Created at: 1400997940
	    2015-05-01T00:32:45.316897+00:00 app[worker.1]: 	Subscribers: 17
	    2015-05-01T00:32:45.316900+00:00 app[worker.1]: All done!

17. Celebrate