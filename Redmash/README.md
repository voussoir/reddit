REDMASH
==========

Don't waste your time posting this to /r/shittyprogramming. It's bad. I know. 

This scrapes reddit for posts with keywords in the titles, keydomains as the linked url, or keynames as the submitter. It compiles these into multiple TXT files which are sorted by various criteria. 

At the end, it packs the information into a pickle file. This allows you to generate more txt files without having to re-run the program. This is especially important if you're scraping several thousand submissions.

**To use the pickle file:**

Open Python interpreter

`import pickle`

`filec = open('C:\\path\\file.p', 'rb')`

`loaded = pickle.load(filec)`

'loaded' now contains all of the posts. This is in a dictionary form rather than an object form. To get the author of the sixth post in the list:

`item = loaded[5]`

`print(item['author'])`

Contact me if this doesn't make any sense. I wouldn't be surprised.