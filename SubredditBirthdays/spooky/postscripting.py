#import subprocess
#subprocess.call("echo %cd%")
#subprocess.call("C:\bit\ghostscript\bin\gswin64 -r600 -sDEVICE=png16m -dBATCH -dNOPAUSE -dSAFER -sOutputFile=heyo.png Heyo.ps")
import time
import tkinter
import threading
import random
import string
import subprocess

def rounded(x, rounding=100):
	return int(round(x/rounding)) * rounding

def plotdict(title, inputdata, colorbg="#fff", colorfg="#000", colormid="#888"):
	print('Printing', title)
	t=tkinter.Tk()

	canvas = tkinter.Canvas(t, width=3840, height=2160, bg=colorbg)
	canvas.pack()
	canvas.create_line(430, 250, 430,1755, width=10, fill=colorfg)
	#Y axis
	canvas.create_line(430,1750, 3590,1750, width=10, fill=colorfg)
	#X axis

	dkeys = inputdata[0]
	dvals = inputdata[1]
	entrycount = len(dkeys)
	availablespace = 3140
	availableheight= 1490
	entrywidth = availablespace / entrycount
	#print(dkeys, dvals, "Width:", entrywidth)

	smallest = min(dvals)
	bottom = int(smallest*0.75) - 5
	bottom = 0 if bottom < 8 else rounded(bottom, 100)
	largest = max(dvals)
	top = int(largest + (largest/5))
	top = rounded(top, 100)
	print(bottom,top)
	span = top-bottom
	perpixel = span/availableheight

	curx = 445
	cury = 1735

	labelx = 420
	labely = 255
	#canvas.create_text(labelx, labely, text=str(top), font=("Consolas", 72), anchor="e")
	labelspan = 130#(1735-255)/10
	canvas.create_text(labelx, 100, text="Subreddits", font=("Consolas", 72), anchor="e", fill=colorfg)
	for x in range(12):
		value = int(top -((labely - 255) * perpixel))
		value = rounded(value, 100)
		value = '{0:,}'.format(value)
		canvas.create_text(labelx, labely, text=value, font=("Consolas", 72), anchor="e", fill=colorfg)
		canvas.create_line(430, labely, 3590, labely, width=2, fill=colormid)
		labely += labelspan

	for entrypos in range(entrycount):
		entry = dkeys[entrypos]
		entryvalue = dvals[entrypos]
		entryx0 = curx + 10
		entryx1 = entryx0 + (entrywidth-10)
		curx += entrywidth

		entryy0 = cury
		entryy1 = entryvalue - bottom
		entryy1 = entryy1/perpixel
		#entryy1 -= bottom
		#entryy1 /= perpixel
		entryy1 = entryy0 - entryy1
		#print(perpixel, entryy1)
		#print(entry, entryx0,entryy0, entryx1, entryy1)
		canvas.create_rectangle(entryx0,entryy0, entryx1,entryy1, fill=colorfg, outline=colorfg)

		font0x = entryx0 + (entrywidth / 2)
		font0y = entryy1 - 5

		font1y = 1760

		entryvalue = round(entryvalue)
		fontsize0 = len(str(entryvalue)) 
		fontsize0 = round(entrywidth / fontsize0) + 3
		fontsize0 = 100 if fontsize0 > 100 else fontsize0
		fontsize1 = len(str(entry))
		fontsize1 = round(1.5* entrywidth / fontsize1) + 5
		fontsize1 = 60 if fontsize1 > 60 else fontsize1
		canvas.create_text(font0x, font0y, text=entryvalue, font=("Consolas", fontsize0), anchor="s", fill=colorfg)
		canvas.create_text(font0x, font1y, text=entry, font=("Consolas", fontsize1), anchor="n", fill=colorfg)
		canvas.update()
	print('\tDone')
	canvas.postscript(file=title+".ps", width=3840, height=2160)
	t.geometry("1x1+1+1")
	t.update()
	t.destroy()
		

data = []
data.append(['x']*30)
data.append([random.randint(30, 250000) for x in range(30)])
plotdict('testc', data)
