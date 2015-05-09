import threading
import tkinter
import time
import string
import os
import sys

goodchars = string.ascii_lowercase + string.digits + '_-'
todo = set()

class SysLabel:
	def __init__(self, module, maxsize):
		self.lines = []
		self.module = module
		self.maxsize = maxsize
	def write(self, data):
		data = data.strip()
		if len(data) > 0:
			self.lines.append(data)
		self.lines = self.lines[-self.maxsize:]
		self.flush()
	def flush(self):
		self.module.configure(text='\n'.join(self.lines))

def a():
	def submit(*b):
		x = enter.get()
		x = x.lower()
		if 2 < len(x) < 21:
			x = [c for c in x if c in goodchars]
			x = ''.join(x)
			todo.add(x)
		enter.delete(0, 'end')
		update()
	
	def update():
		display.configure(text='\n'.join(todo))
		t.after(250, update)
	
	t=tkinter.Tk()
	t.configure(bg='#333')
	syslabel = tkinter.Label(t, bg='#000', fg='#eee', justify='left', anchor='nw', height=3)
	syslabel.configure(font=('Consolas', 10))
	syslabel.pack(expand=True, fill='x', anchor='nw')
	sysout = SysLabel(syslabel, 3)
	sys.stdout = sysout
	sys.stderr = sysout
	display = tkinter.Label(t, text='Heyo', bg='#333', fg='#eee')
	display.configure(font=('Consolas', 10))
	display.pack(expand=True, fill='both')
	t.title('windowtitle')
	w = 550
	h = 350
	screenwidth = t.winfo_screenwidth()
	screenheight = t.winfo_screenheight()
	windowwidth = w
	windowheight = h
	windowx = (screenwidth-windowwidth) / 2
	windowy = ((screenheight-windowheight) / 2) - 27
	geometrystring = '%dx%d+%d+%d' % (windowwidth, windowheight, windowx, windowy)
	t.geometry(geometrystring)
	
	enter = tkinter.Entry(t, bg='#111', relief='flat', fg='#fff', insertbackground='#fff')
	enter.configure(font=('Consolas', 10))
	enter.focus_set()
	enter.pack()
	enter.bind('<Return>', submit)
	t.mainloop()

	# Brutal shutdown because otherwise closing the tkinter window
	# causes a TCL Async "deleted by wrong thread" error which causes
	# Python to hang and open a Windows crash screen.
	os._exit(0)


thread = threading.Thread(target=a)
thread.daemon=False
thread.start()
import un
un.MIN_LASTSCAN_DIFF *= 100
print('Ready.')
while thread.is_alive():
	for x in todo:
		un.process(x, quiet=True)
		todo.remove(x)
		break
	time.sleep(1)
