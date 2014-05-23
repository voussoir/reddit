import praw 
import time
import winsound
import html.entities
from tkinter import Tk, BOTH, Entry, PhotoImage
from tkinter.ttk import Frame, Button, Style, Label

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
        self.style = Style()
        self.style.theme_use("clam")
        self.pack(fill=BOTH, expand = 1)

        self.labelU = Label(self, text="U:")
        self.labelP = Label(self, text="P:")
        
        self.entryUsername = Entry(self)
        self.entryUsername.config(relief='flat')
        self.entryUsername.focus_set()
        self.entryUsername.bind('<Return>', lambda event: self.entryPassword.focus_set())

        self.entryPassword = Entry(self)
        self.entryPassword.config(relief='flat', show='•')
        self.entryPassword.bind('<Return>', lambda event: self.login(self.entryUsername.get(), self.entryPassword.get()))

        self.newbutton = Button(self, text="Login", command= lambda: self.login(self.entryUsername.get(), self.entryPassword.get()))
        self.newbutton.bind('<Return>', lambda event: self.login(self.entryUsername.get(), self.entryPassword.get()))
        self.newbutton.config(width=6)
        self.quitbutton = Button(self, text="Quit", command= lambda: self.quit())
        self.quitbutton.config(width=6)
        
        self.mailIconRed = PhotoImage(file="mail.gif")
        self.labelRed = Label(self, image=self.mailIconRed)
        self.mailIconGray = PhotoImage(file="mail2.gif")
        self.labelGray = Label(self, image=self.mailIconGray)
        self.labelKarma = Label(self, text = '•')

        self.labelU.grid(row=0, column=0)
        self.entryUsername.grid(row=0, column=1)
        self.labelP.grid(row=1, column=0)
        self.entryPassword.grid(row=1, column=1, pady=4)
        self.newbutton.grid(row=2, column=1)
        self.quitbutton.grid(row=3, column=1, pady=4)
        

        '''
        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()

        w=150
        h=112
        x = (sw - w) / 2
        y = (sh - h) / 2

        self.parent.geometry('%dx%d+%d+%d' % (w, h, x, y-50))
        '''


    def login(self, username, password):
        print('U: ' + username)
        self.username = username
        if username == '':
            print('Please enter a username')
            self.entryUsername.focus_set()
        elif password == '':
            print('Please enter a password')
            self.entryPassword.set_focus()
            
        if username != '' and password != '':
            print('Attempting login for ' + username)
            try:
                self.USERAGENT = username + ' scans his inbox for new mail.'
                self.r = praw.Reddit(self.USERAGENT)
                self.r.login(username, password)
                print('You have logged in as ' + username)
                self.labelU.grid_forget()
                self.labelP.grid_forget()
                self.entryUsername.grid_forget()
                self.entryPassword.grid_forget()
                self.newbutton.grid_forget()
                self.quitbutton.grid_forget()
                self.usernamelabel = Label(self, text=username)
                self.usernamelabel.grid(row=0, column=0, pady = 10, padx = 30)
                self.quitbutton.grid(row=1, column=0)
                self.labelKarma.grid(row = 3, column = 0)
                self.playedSound = 'false'
                self.loop()
            except praw.errors.InvalidUserPass:
                print('Invalid username or password')

    def loop(self):
        print('Starting new search')
        hasmail = 'false'
        for msg in self.r.get_unread(limit=None):
            hasmail = 'true'
        
        if hasmail == 'true':
            print("You've got mail!")
            if self.playedSound == 'false':
                winsound.PlaySound('pop.wav', winsound.SND_FILENAME)
            self.playedSound = 'true'
            self.labelGray.grid_forget()
            self.labelRed.grid(row=2, column=0)
        if hasmail == 'false':
            self.playedSound = 'false'
            print('No mail!')
            self.labelRed.grid_forget()
            self.labelGray.grid(row=2, column=0)
        self.user = self.r.get_redditor(self.username)
        lkarma = str(self.user.link_karma)
        ckarma = str(self.user.comment_karma)
        lkarma = self.karmaRound(lkarma)
        ckarma = self.karmaRound(ckarma)
        karmastring = lkarma + ' • ' + ckarma
        self.labelKarma.config(text = karmastring)

        self.after(10000, lambda: self.loop())

    def karmaRound(self, karma):
        if len(karma) > 4 and len(karma) < 7:
            tstring = karma[:-3]
            tstring2 = karma[-3:]
            karma = tstring + '.' + tstring2[:2] + 'K'
            return karma
        if len(karma) > 6:
            tstring = karma[:-6]
            tstring2 = karma[-6:]
            karma = tstring + '.' + tstring2[:2] + 'M'
            return karma
        else:
            return karma

        

def main():
    root = Tk()
    ex = Example(root)
    root.iconbitmap('ping.ico')
    root.mainloop()



if __name__ == '__main__':
    main()



