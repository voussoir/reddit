import os

checkwords = ['USERNAME', 'PASSWORD']
#checkwords = ['== None', '!= None']

def checkfile(filename):
	f = open(filename, 'r')
	text = f.read()
	f.close()
	for (index, line) in enumerate(text.splitlines()):
		if any(ch in line for ch in checkwords):
			print(filename, index+1)

w = os.walk('.')
for x in w:
	if '.git' in x[0]:
		continue
	for filename in x[2]:
		if 'oauth2verifying.py' == filename:
			continue
		if '.py' in filename:
			checkfile(x[0]+'\\'+filename)