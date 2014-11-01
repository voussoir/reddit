import time
import praw
import bot
import threading
import textwrap
import tkinter
from tkinter import Label, Frame, Button, Text

prevx = 0
prevy = 0
samewidget = False
totalitems = 0

def framedrag(event):
	global prevx
	global prevy
	global samewidget
	#print("pointer",event.widget.winfo_pointerx(), event.widget.winfo_pointery())
	#print("event", event.x, event.y)
	#print("root",event.widget.winfo_rootx(), event.widget.winfo_rooty())
	#print("winfo", event.widget.winfo_x(), event.widget.winfo_y())
	cursorx = event.widget.winfo_pointerx()
	cursory = event.widget.winfo_pointery()
	if samewidget:
		newx = event.widget.winfo_x()
		newy = event.widget.winfo_y()
		newx += (cursorx - prevx)
		newy += (cursory - prevy)
		event.widget.place(x=newx)
	prevx = cursorx
	prevy = cursory
	samewidget = True

def resetdrag(event):
	global samewidget
	samewidget = False
	winx = event.widget.winfo_x()
	if winx > -10:
		event.widget.place(x=event.widget.wx)
		if winx > 50:
			event.widget.configure(bg="#555")
			if event.widget.sourceitem.new:
				event.widget.sourceitem.mark_as_read()
	else:
		recycle(event.widget)
		refreshscreen()

widgets = []
widgetpool = []
def recycle(widget):
	global widgetpool
	global widgets
	widgetpool.append(widget)
	widgets.remove(widget)
	widget.rt.grid_forget()
	widget.rb.grid_forget()
	widget.configure(width=1, height=1)

def refreshscreen():
	global widgets
	coll = 0
	for w in widgets:
		ww = 680
		wh = 10 + (18 * len(w.sourceitem.body.split('\n')))
		wx = 20
		wy = 20 + (coll) + (20*widgets.index(w))
		w.configure(width=ww, height=wh)
		w.place(x=wx, y=wy)
		w.rt.place(x=450, y=10)
		w.rb.place(x= 450, y=wh-30)
		#print(coll)
		#print(ww, wh, wx, wy)
		coll += wh
	if len(widgets) < 2:
		final = widgets[-1].sourceitem.fullname
		print(final)
		inbox = list(r.get_inbox(params={"after":final}))
		print('Inbox')
		additems(inbox)
		refreshscreen()

def additems(i, doreturn=False, bgcolor="#555"):
	returnable = []
	for item in i:
		global totalitems
		totalitems += 1
		ff = Frame(f, bg=bgcolor)
		item.body = item.author.name + ' || ' + item.fullname + '\n' + item.body
		item.body = str(totalitems) + '\n' + item.body
		ibody = item.body.replace('\n\n', '\n')
		ifinal = ''
		for paragraph in ibody.split('\n'):
			ifinal += '\n'.join(textwrap.wrap(paragraph))
			ifinal += '\n'  
	
		item.body = ifinal
		ww = 680
		wh = 10 
		wx = 20
		wy = 20 
		#print(ww, wh, wx, wy)
		ff.ww = ww
		ff.wh = wh
		ff.wx = wx
		ff.wy = wy
		ff.body = item.body
		ff.sourceitem = item
		ff.configure(width=ww, height=wh)
		ff.place(x=wx, y=wy)
		ff.bind("<B1-Motion>", framedrag)
		ff.bind("<ButtonRelease-1>", resetdrag)
		ff.pack_propagate(0)
		l = Label(ff, text=item.body, bg="#777")
		l.place(x=10,y=10)
		rt = Text(ff, width= 15, height= (len(ifinal.split('\n'))) - 2)
		rt.sourceitem = item
		rt.place(x=400,y=10)
		rb = Button(ff, text="Reply", command= lambda rep=rt: reply(rep))
		rb.place(x=400,y=wh-20)
		ff.rt = rt
		ff.rb = rb
		if not doreturn:
			widgets.append(ff)
		else:
			returnable.append(ff)
	if doreturn:
		return returnable
	else:
		refreshscreen()

def grabunread():
	global r
	global widgets
	while True:
		u = list(r.get_unread(limit=None))
		u = additems(u, doreturn=True, bgcolor="#FE5900")
		conflict = True
		while conflict:
			conflict = False
			for un in u:
				for wi in widgets:
					if un.sourceitem.id == wi.sourceitem.id:
						conflict = True
						u.remove(un)
						break
		widgets[0:0] = u
		refreshscreen()
		l = list(range(60))
		l.reverse()
		for x in l:
			print('\rNext update in ' + "%02d"%x, end="")
			time.sleep(1)

def reply(inwidget):
	source = inwidget.sourceitem
	text = inwidget.get(0.0, "end")
	if len(text.replace('\n', '')) > 0:
		if 't1_' in source.fullname:
			print(source.fullname, text)
			source.reply(text)
		elif 't4_' in source.fullname:
			print(source.fullname, text)
			#Just give me a minute
			source.reply(text)
		inwidget.delete(0.0, "end")




t = tkinter.Tk()

sw = t.winfo_screenwidth()
sh = t.winfo_screenheight()
fw = 720
fh = 406
sw = (sw - fw) / 2
sh = (sh - fh) / 3
t.geometry('%dx%d+%d+%d' % (fw, fh, sw, sh))
f = Frame(t)
f.configure(bg="black")
f.pack(fill="both", expand=1)

print('Reddit')
r=bot.rG()
print('Inbox')
inbox = list(r.get_inbox())
done = False
while not done:
	done = True
	for x in inbox:
		if x.new:
			done = False
			inbox.remove(x)
additems(inbox)

unreadthread = threading.Thread(target=grabunread)
unreadthread.daemon=True
unreadthread.start()

t.mainloop()