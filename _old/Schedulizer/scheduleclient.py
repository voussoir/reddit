import praw 
import time
import html.entities
import tkinter
import datetime
import string
import sqlite3
from tkinter import Tk, BOTH, Entry, PhotoImage, OptionMenu, Spinbox, Text, Scrollbar, Listbox
from tkinter.ttk import Frame, Button, Style, Label
from tkinter.tix import ScrolledWindow

class Program():
    def __init__(self, name, path):
        self.name = name
        self.path = path

class Example(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent)

        self.parent = parent
        self.initUI()

    def initUI(self):
        self.parent.title("")
        #self.style = Style()
        #self.style.theme_use("clam")
        #self.pack(fill=BOTH, expand = 1)


        self.quitbutton = Button(self, text="Quit", command= lambda: self.quit())

        self.quitbutton.grid(row=3, column=1, pady=4)

        self.labelErrorPointer = Label(self, text="◀")

        self.labellist = []
        self.entrylist = []
        self.verifylist = []
        self.misclist = []
                
        self.optionCreate = "Create"
        self.optionUpcoming = "Upcoming"
        self.optionPast = "Past"

        self.prevmode = self.optionCreate
        self.curmode = self.optionCreate
        self.optionvar = tkinter.StringVar(self)
        self.optionvar.trace("w",self.permaloop)
        self.optionvar.set(self.optionCreate)
        self.option = OptionMenu(self, self.optionvar, self.optionCreate, self.optionUpcoming, self.optionPast)

        self.optionpostmodevar = tkinter.StringVar(self)
        self.optionpostmodevar.trace("w",self.permaloop)
        self.optionpostmodevar.set('url')
        self.optionpostmode = OptionMenu(self, self.optionpostmodevar, 'url', 'text')

        self.labelText = Label(self, text='Selftext:')
        self.entryText = Text(self)
        self.labelURL = Label(self, text='URL:')
        self.entryURL = Entry(self)
        self.entryURL.configure(width=60)  

        self.sql = sqlite3.connect('sql.db')
        print('Loaded SQL Database')
        self.cur = self.sql.cursor()

        self.cur.execute('CREATE TABLE IF NOT EXISTS upcoming(ID TEXT, SUBREDDIT TEXT, TIME INT, TITLE TEXT, URL TEXT, BODY TEXT)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS past(ID TEXT, SUBREDDIT TEXT, TIME INT, TITLE TEXT, URL TEXT, BODY TEXT, POSTLINK TEXT)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS internal(NAME TEXT, ID INT)')
        print('Loaded Completed table')
        self.cur.execute('SELECT * FROM internal')
        f = self.cur.fetchone()
        if not f:
            print('Database is new. Adding ID counter')
            self.cur.execute('INSERT INTO internal VALUES(?, ?)', ['counter', 1])
            self.idcounter = 1
        else:
            self.idcounter = f[1]
            print('Current ID counter: ' + str(self.idcounter))

        self.sql.commit()
        

        
        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()


        w=853
        h=480
        x = (sw - w) / 2
        y = (sh - h) / 2

        self.parent.geometry('%dx%d+%d+%d' % (w, h, x, y-50))

        self.login()
        

    def login(self):

        try:
            self.quitbutton.grid_forget()
            self.quitbutton.grid(row=9000, column=0, columnspan=20)          

            self.option.grid(row=1,column=0,columnspan=80,pady=8)

            self.updategui(fullclean=True)
        except praw.errors.InvalidUserPass:
            pass
            print('Invalid username or password')
            self.entryPassword.delete(0,200)
            self.labelErrorPointer.grid(row=1, column=2)

    def permaloop(self, *args):
        self.curmode = self.optionvar.get()
        print('Was: ' + self.prevmode + ' | Now: ' + self.curmode)
        if self.curmode != self.prevmode:
            self.prevmode = self.curmode
            self.updategui(fullclean=True)
        else:
            self.updategui(False)

    def getTime(self, bool):
        timeNow = datetime.datetime.now(datetime.timezone.utc)
        timeUnix = timeNow.timestamp()
        if bool is False:
            return timeNow
        else:
            return timeUnix

    def addentrytobase(self, subreddit, title, url="", body="", mode="", ptime=""):
        curtime = round(self.getTime(True))
        try:
            t = self.entryMo.get() + ' ' + self.entryDa.get() + ' ' + self.entryYr.get() + ' ' + self.entryHH.get() + ':' + self.entryMM.get()
            plandate = datetime.datetime.strptime(t, "%B %d %Y %H:%M")
            plandate = plandate.timestamp()
        except ValueError:
            print('Invalid Day')
            return False

        if mode == 'url':
            url = self.entryURL.get()
            body = ""
            if 'http://' not in url and 'https://' not in url:
                print('Please enter a proper URL')
                return False
        if mode == 'text':
            body = self.entryText.get("1.0", "end")
            url = ""

        if plandate < curtime:
            print('Please enter a time in the future')
            return False

        if not all(char in string.ascii_letters+string.digits+'_-' for char in subreddit):
            print('Subreddit contains invalid characters')
            return False

        if len(subreddit) == 0:
            print('You must enter a subreddit')
            return False

        if len(title) == 0:
            print('You must enter a title')
            return False
        if len(title) > 300:
            print('Title is too long. ' + str(len(title)) + '/300 char max')
            return False
        if len(body) > 15000:
            print('Body is too long. ' + str(len(body)) + '/15,000 char max')

        print('Timestamp:', plandate)
        self.cur.execute('INSERT INTO upcoming VALUES(?, ?, ?, ?, ?, ?)', [self.idcounter, subreddit, int(plandate), title, url, body])
        self.idcounter += 1
        self.cur.execute('UPDATE internal SET ID=? WHERE NAME=?', [self.idcounter, 'counter'])
        self.sql.commit()
        print('\nPost Saved!')
        print(self.idcounter, subreddit, self.timestamptoday(int(plandate)))
        print(title)
        print(url, body)
        print()
        self.entryText.delete("1.0", "end")
        self.entryURL.delete(0, 'end')
        self.entryTitle.delete(0, 'end')
        #self.updategui(halfclean=True)

    def timestamptoday(self, timestamp):
        d = datetime.datetime.fromtimestamp(timestamp)
        info = datetime.datetime.strftime(d, "%b %d %H:%M")
        return info


    def dropentryfrombase(self, ID):
        if '-' not in ID:
            try:
                ID = int(ID)
                l = [ID]
            except ValueError:
                print('You must enter a number')
                return
        else:
            if ID.count('-') == 1:
                try:
                    ID = ID.replace(' ', '')
                    ID = ID.split('-')
                    ID[0] = int(ID[0])
                    ID[1] = int(ID[1])
                    if ID[1] > ID[0]:
                        l = list(range(ID[0], ID[1]+1))
                    else:
                        return
                except ValueError:
                    return

        for item in l:
            item = str(item)
            print('Dropping Item ' + item + ' from Upcoming')
            self.cur.execute('DELETE FROM upcoming WHERE ID=?', [item])
            self.sql.commit()
        self.updategui(fullclean=True)

    def printbasetofile(self, db):
        filea = open(db + '.txt', 'w')
        if db == 'past':
            self.cur.execute('SELECT * FROM past')
        if db == 'upcoming':
            self.cur.execute('SELECT * FROM upcoming')
        f = self.cur.fetchall()
        print('Printed ' + db + ' unimpeded to file')
        for item in f:
            i = list(item)
            i[2] = self.timestamptoday(i[2])
            i.remove('')

            print(str(i)[1:-1], file=filea)
        filea.close()

        


    def updategui(self, halfclean=False, fullclean=False):

        if self.curmode == self.optionCreate:
            try:
                print(self.optionpostmodevar.get())

                if self.optionpostmodevar.get() == 'url':
                    self.entryText.delete("1.0", 'end')
                    self.labelText.grid_forget()
                    self.entryText.grid_forget()
    
                    self.labelURL.grid(row=8, column=0, columnspan=30)
                    self.entryURL.grid(row=9, column=0, columnspan=12, pady=10)
    
                if self.optionpostmodevar.get() == 'text':
                    self.entryURL.delete(0, 'end')
                    self.labelURL.grid_forget()
                    self.entryURL.grid_forget()
    
                    self.labelText.grid(row=8, column=0, columnspan=30)
                    self.entryText.configure(width=40, height=8)
                    self.entryText.grid(row=9, column=0, columnspan=12)
            except AttributeError:
                pass

        if fullclean is True:
            print('Cleaning GUI')
            for item in self.labellist:
                item.grid_forget()
            for item in self.entrylist:
                item.grid_forget()
            for item in self.verifylist:
                item.grid_forget()
            for item in self.misclist:
                item.grid_forget()
            self.labellist = []
            self.entrylist = []
            self.verifylist = []
            self.misclist = []

            if self.curmode == self.optionCreate:
                self.newrowindex = 6
                self.labelSubreddit = Label(self, text="Subreddit:    /r/")
                self.labelTitle = Label(self, text="Post title:  ")
                self.entrySubreddit = Entry(self)
                self.entryTitle = Entry(self)


                self.labelHH = Label(self, text="Schedule time (Local timezone):")
                nowlist = datetime.datetime.strftime(datetime.datetime.now(), "%B %d %Y %H %M").split()

                self.entryMo = Spinbox(self, width=9, values=('January', 'February', 'March', 'April', 'May', 'June', 'July', \
                    'August', 'September', 'October', 'November', 'December'))
                self.entryMo.delete(0,'end')
                self.entryMo.insert(0, nowlist[0])


                self.entryDa = Spinbox(self, width=2, from_=1, to=31)
                self.entryDa.delete(0,'end')
                self.entryDa.insert(0, nowlist[1])

                self.entryYr = Spinbox(self, width=4, from_=2014, to=2500)
                self.entryYr.delete(0,'end')
                self.entryYr.insert(0, nowlist[2])

                self.entryHH = Spinbox(self, from_=0, to=23, width=2)
                self.entryHH.delete(0,'end')
                self.entryHH.insert(0, nowlist[3])

                self.entryMM = Spinbox(self, from_=0, to=59, width=2)
                self.entryMM.delete(0,'end')
                self.entryMM.insert(0, nowlist[4])

                self.buttonAddentry = Button(self, text='Save', command=lambda: self.addentrytobase(self.entrySubreddit.get(), self.entryTitle.get(),\
                    mode=self.optionpostmodevar.get()))


                self.misclist.append(self.labelSubreddit)
                self.misclist.append(self.entrySubreddit)
                self.misclist.append(self.labelHH)
                self.misclist.append(self.entryHH)
                self.misclist.append(self.entryMM)
                self.misclist.append(self.entryMo)
                self.misclist.append(self.entryDa)
                self.misclist.append(self.entryYr)
                self.misclist.append(self.labelTitle)
                self.misclist.append(self.entryTitle)
                self.misclist.append(self.buttonAddentry)
                self.misclist.append(self.optionpostmode)
                self.misclist.append(self.labelText)
                self.misclist.append(self.entryText)
                self.misclist.append(self.labelURL)
                self.misclist.append(self.entryURL)

                self.labelSubreddit.grid(row=2, column=0, sticky="e")
                self.labelTitle.grid(row=3, column=0, sticky="e")
                self.entrySubreddit.grid(row=2, column=1, columnspan=3, sticky="w")
                self.entryTitle.grid(row=3, column=1, columnspan=3, sticky="w")
                self.entryMo.grid(row=4, column=1,sticky="e")
                self.entryDa.grid(row=4, column=2)
                self.entryYr.grid(row=4, column=3)
                self.labelHH.grid(row=4, column=0, sticky="se", pady=5)
                self.entryHH.grid(row=5, column=1, sticky="e")
                self.entryMM.grid(row=5, column=2, sticky="w")
                self.optionpostmode.grid(row=6, column=0, columnspan=20, pady=10)
                self.buttonAddentry.grid(row=200, column=0, columnspan=20)

            if self.curmode == self.optionUpcoming:
                self.cur.execute('SELECT * FROM upcoming')
                dobutton = True

            if self.curmode == self.optionPast:
                self.cur.execute('SELECT * FROM past')
                dobutton = False

            if self.curmode == self.optionPast or self.curmode == self.optionUpcoming:

                
                self.listboxId = Listbox(self)
                self.listboxId.configure(width=118, height=20, font=("Courier 8"))
                self.misclist.append(self.listboxId)

                self.listboxScroller = Scrollbar(self, orient='horizontal', command=self.listboxId.xview)
                self.listboxScroller.grid(row=4, column=0, columnspan=900)
                self.listboxId.grid(row=3, column=0, columnspan=10)

                self.listboxId.configure(xscrollcommand=self.listboxScroller.set)
                self.misclist.append(self.listboxScroller)

                self.buttonPrinter = Button(self, text="Print to .txt file")
                if self.curmode == self.optionPast:
                    self.buttonPrinter.configure(command=lambda: self.printbasetofile('past'))
                if self.curmode == self.optionUpcoming:
                    self.buttonPrinter.configure(command=lambda: self.printbasetofile('upcoming'))   

                self.buttonPrinter.grid(row = 6, column=0, columnspan=90)
                self.misclist.append(self.buttonPrinter)

                if dobutton is True:
                    self.entryDelete = Entry(self)
                    self.buttonDelete = Button(self, text="Delete Item: ", command=lambda: self.dropentryfrombase(self.entryDelete.get()))
                    self.buttonDelete.grid(row=5, column=0, sticky='e')
                    self.entryDelete.grid(row=5, column=1, sticky='w')
                    self.misclist.append(self.entryDelete)
                    self.misclist.append(self.buttonDelete)


                fetched = self.cur.fetchall()
                for item in fetched:

                    info = self.timestamptoday(item[2])

                    if item[4] == '':
                        infx = item[5]
                    if item[5] == '':
                        infx = item[4]
                    if self.curmode == self.optionPast:
                        infy = '.' + item[6]
                    else:
                        infy = ''

                    self.listboxId.insert('end', \
                        item[0] + '.'*(6 - len(item[0])) \
                        + item[1][:10] + '.'*(12 - len(item[1][:10])) \
                        + info + '.'*(15 - len(info[:14])) \
                        + item[3][:18] + '.'*(20 - len(item[3][:14])) \
                        + infx[:45] + '.'*(47-len(infx[:45])) \
                        + infy)

                    
                



    def morerows(self, label, columnm, columnn, limit, *args):
        self.redditlabel = Label(self,text=label)
        self.redditlabel.grid(row=self.newrowindex,column=columnm, sticky="e")
        self.labellist.append(self.redditlabel)

        self.redditentry = Entry(self)
        self.redditentry.grid(row=self.newrowindex,column=columnn, columnspan=9)
        self.entrylist.append(self.redditentry)

        self.newrowindex += 1
        if self.newrowindex >= limit:
            self.morerowbutton.grid_forget()
        print(self.newrowindex)





        

def main():
    root = Tk()
    f1 = tkinter.Frame(width=200, height=200)
    ex = Example(root)
    f1.pack(fill="both", expand=True, padx=20, pady=20)
    ex.place(in_=f1, anchor="c", relx=.5, rely=.5)
    root.mainloop()



if __name__ == '__main__':
    main()



