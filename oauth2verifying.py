import os

checkwords = ['USERNAME', 'PASSWORD']

def checkfile(filename):
	f = open(filename, 'r')
	lines = f.readlines()
	for line in lines:
		if any(ch in line for ch in checkwords):
			print(filename, lines.index(line)+1)

w = os.walk('.')
for x in w:
	if '.git' in x[0]:
		continue
	for filename in x[2]:
		if '.py' in filename:
			checkfile(x[0]+'\\'+filename)