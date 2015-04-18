import un
import threading
import tkinter
import time
import string

goodchars = string.ascii_lowercase + string.digits + '_-'
todo = set()

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
	display = tkinter.Label(t, text='Heyo')
	display.pack(expand=True, fill='both')
	t.title('windowtitle')
	w = 450
	h = 350
	screenwidth = t.winfo_screenwidth()
	screenheight = t.winfo_screenheight()
	windowwidth = w
	windowheight = h
	windowx = (screenwidth-windowwidth) / 2
	windowy = ((screenheight-windowheight) / 2) - 27
	geometrystring = '%dx%d+%d+%d' % (windowwidth, windowheight, windowx, windowy)
	t.geometry(geometrystring)
	
	enter = tkinter.Entry(t)
	enter.focus_set()
	enter.pack()
	enter.bind('<Return>', submit)
	t.mainloop()


thread = threading.Thread(target=a)
thread.daemon=True
thread.start()
while True:
	for x in todo:
		un.process(x, quiet=True)
		todo.remove(x)
		break
	time.sleep(1)