import praw 
import time
import html.entities
from tkinter import Tk, BOTH, Entry, PhotoImage
from tkinter.ttk import Frame, Button, Style, Label
  

'''This is the only thing you need to edit'''  
USERAGENT = ""
#This is a short description of what the bot does. For example "Newsletter bot"








try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERAGENT = bot.geta()
except ImportError:
    pass
    
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
        self.username = ''
        self.r = praw.Reddit(USERAGENT)
        self.parent.title("")
        self.style = Style()
        self.style.theme_use("clam")
        self.pack(fill=BOTH, expand = 1)

        self.labelU = Label(self, text="U:")
        self.labelP = Label(self, text="P:")
        
        self.entryUsername = Entry(self)
        self.entryUsername.config(relief='flat')
        self.entryUsername.focus_set()
        self.entryUsername.bind('<Return>', lambda event: self.login(self.entryUsername.get()))
        self.entryUsername.bind('<Up>', lambda event: self.entryUsername.insert(0, self.username))

        self.quitbutton = Button(self, text="Quit", command= lambda: self.quit())
        self.quitbutton.config(width=6)
        
    
        self.labelKarma = Label(self, text = '•')
        self.labelKarma.grid(row = 3, column = 1)


        self.labelU.grid(row=0, column=0)
        self.entryUsername.grid(row=0, column=1)
        self.quitbutton.grid(row=2, column=1, pady=4)

        self.usernamelabel = Label(self, text='')
        self.usernamelabel.grid(row=1, column=1)


    def login(self, username):
        print('U: ' + username)
        self.username = username
        self.entryUsername.delete(0, 200)
        if username == '':
            self.entryUsername.focus_set()
            
        else:
            try:
                self.user = self.r.get_redditor(self.username)
                lkarma = str(self.user.link_karma)
                ckarma = str(self.user.comment_karma)
                lkarma = self.karmaRound(lkarma)
                ckarma = self.karmaRound(ckarma)
                karmastring = lkarma + ' • ' + ckarma
                self.labelKarma.config(text = karmastring)
                self.usernamelabel.config(text= self.username)

            except:
                self.labelKarma.config(text = '•')
                self.usernamelabel.config(text= 'User not found')
                pass

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
    root.mainloop()



if __name__ == '__main__':
    main()



