import threading
import tkinter
import time
import string
import os
import sys

goodchars = string.ascii_lowercase + string.digits + '_-'
todo = set()

class T():
    def __init__(self, name, noskip):
        self.name = name
        self.noskip = noskip
    def __hash__(self):
        return self.name.__hash__()

class SysLabel:
    def __init__(self, module, maxsize):
        self.lines = []
        self.module = module
        self.maxsize = maxsize
    def write(self, data):
        data = data.rstrip()
        data = data.split('\n')
        while '' in data:
            data.remove('')
        if len(data) > 0:
            self.lines += data
        self.lines = self.lines[-self.maxsize:]
        self.flush()
    def flush(self):
        self.module.configure(text='\n'.join(self.lines))

class EntryWithHistory(tkinter.Entry):
    def __init__(self, master, submithook, *args, **kwargs):
        super(EntryWithHistory, self).__init__(master, *args, **kwargs)
        self.previousinputs = []
        self.previousinputstep = 0

        self.submithook = submithook

        self.bind('<Return>', self.submit)
        self.bind('<Escape>', lambda b: self.delete(0, 'end'))
        self.bind('<Up>', self.previous_back)
        self.bind('<Down>', self.previous_forward)

    def submit(self, *b):
        x = self.get()
        x = x.lower()
        noskip = '!' in x
        if 2 < len(x) < 21:
            if len(self.previousinputs) == 0 or self.previousinputs[-1] != x:
                self.previousinputs.append(x)
            self.previousinputstep = 0
        self.submithook(x)
        self.delete(0, 'end')

    def previous_back(self, *b):
        self.previous_step(-1)

    def previous_forward(self, *b):
        self.previous_step(1)

    def previous_step(self, direction):
        self.previousinputstep += direction
        if abs(self.previousinputstep) > len(self.previousinputs):
            self.previousinputstep -= direction
            return
        self.delete(0, 'end')
        if self.previousinputstep >= 0:
            self.previousinputstep = 0
            return
        self.insert(0, self.previousinputs[self.previousinputstep])

class Primary():
    def __init__(self, todo):
        self.todo = todo
        self.t=tkinter.Tk()
        self.t.configure(bg='#333')
        self.sysoutsize = 6
        self.syslabel = tkinter.Label(self.t, bg='#000', fg='#eee', justify='left', anchor='nw', height=self.sysoutsize)
        self.syslabel.configure(font=('Consolas', 10))
        self.syslabel.pack(expand=True, fill='x', anchor='nw')
        self.sysout = SysLabel(self.syslabel, self.sysoutsize)
        sys.stdout = self.sysout
        sys.stderr = self.sysout
        self.display = tkinter.Label(self.t, text='Heyo', bg='#333', fg='#eee')
        self.display.configure(font=('Consolas', 10))
        self.display.pack(expand=True, fill='both')
        self.t.title('windowtitle')
        w = 550
        h = 400
        screenwidth = self.t.winfo_screenwidth()
        screenheight = self.t.winfo_screenheight()
        windowwidth = w
        windowheight = h
        windowx = (screenwidth-windowwidth) / 2
        windowy = ((screenheight-windowheight) / 2) - 27
        geometrystring = '%dx%d+%d+%d' % (windowwidth, windowheight, windowx, windowy)
        self.t.geometry(geometrystring)
    
        self.enter = EntryWithHistory(self.t, self.submithook, bg='#111', relief='flat', fg='#fff', insertbackground='#fff')
        self.enter.configure(font=('Consolas', 10))
        self.enter.focus_set()
        self.enter.pack()
        #self.enter.bind('<Return>', self.submit)
        #self.enter.bind('<Up>', self.previous_back)
        #self.enter.bind('<Down>', self.previous_forward)
        #self.previousinputs = []
        #self.previousinputstep = 0
        self.update_screen()
        self.t.mainloop()

    def submithook(self, x):
        noskip = '!' in x
        x = [c for c in x if c in goodchars]
        x = ''.join(x)
        x = T(x, noskip)
        self.todo.add(x)

    def update_screen(self):
        self.display.configure(text='\n'.join([x.name for x in self.todo]))
        self.t.after(250, self.update_screen)
        
def a():
    primary = Primary(todo)
    primary.t.mainloop()

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
        un.process(x.name, quiet=True, noskip=x.noskip)
        todo.remove(x)
        break
    time.sleep(1)
