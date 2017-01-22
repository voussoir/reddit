def base36encode(number, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    """Converts an integer to a base36 string."""
    if not isinstance(number, (int)):
        raise TypeError('number must be an integer')
    base36 = ''
    sign = ''
    if number < 0:
        sign = '-'
        number = -number
    if 0 <= number < len(alphabet):
        return sign + alphabet[number]
    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36
    return sign + base36

def base36decode(number):
    return int(number, 36)

def b36(i):
	if type(i) == int:
		return base36encode(i)
	if type(i) == str:
		return base36decode(i)

import praw
PREFIX = 't3_'
def get_new(r):
	subreddit = r.get_subreddit('all')
	newestitem = next(subreddit.get_new())
	newestitem = b36(newestitem.id)
	while True:
		window = list(range(newestitem, newestitem+100))
		window =  [PREFIX + b36(i) for i in window]
		#print(window[0], window[-1])
		try:
			items = list(r.get_submissions(fullnames=window))
		except praw.errors.NotFound:
			items = None
		r.evict(r.config['by_id'])
		if items is None:
			continue
		for item in items:
			newestitem = b36(item.id) + 1
			yield item