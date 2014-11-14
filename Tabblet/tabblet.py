import json
import tkinter
from tkinter import Label, Button, PhotoImage
import time
import praw
import datetime
import threading

class Tabblet():
	def __init__(self):
		self.tkvar = tkinter.Tk()

		with open("options.json") as j:
			joptions = json.load(j)

		self.tkvar.wm_title("Tabblet")
		self.tkvar.iconbitmap('resources\\tabbleto.ico')

		self.screenwidth = self.tkvar.winfo_screenwidth()
		self.screenheight = self.tkvar.winfo_screenheight()
		self.windowwidth = int(joptions['width'])
		self.windowheight = int(joptions['height'])
		self.windowx = (self.screenwidth-self.windowwidth) / 2
		self.windowy = ((self.screenheight-self.windowheight) / 2) - 27
		self.geometrystring = '%dx%d+%d+%d' % (self.windowwidth, self.windowheight, self.windowx, self.windowy)
		self.tkvar.geometry(self.geometrystring)

		self.image_resetwindow = PhotoImage(file="resources\\resetwindow.gif")
		self.button_resetwindow = Button(self.tkvar, command= lambda: self.tkvar.geometry(self.geometrystring))
		self.button_resetwindow.configure(relief="flat", image=self.image_resetwindow)
		self.button_resetwindow.pack(expand=False,anchor="ne")

		self.tkvar.bind('<Configure>', lambda event: self.button_resetwindow.place(x=self.tkvar.winfo_width()-20, y=0))
		self.tkvar.bind('<B1-Motion>', self.dragmotion)
		self.tkvar.bind('<ButtonPress-1>', lambda event: self.mousestate(True))
		self.tkvar.bind('<ButtonRelease-1>', lambda event: self.mousestate(False))
		
		self.velocityx = 0
		self.velocityy = 0
		self.mousepositionsx = [2]
		self.mousepositionsy = [2]
		self.ismousepressed = False
		self.labelvelocityind = Label(self.tkvar, text='•')
		velocitythread = threading.Thread(target=self.velocitymanager)
		velocitythread.daemon = True
		velocitythread.start()
		self.tkvar.mainloop()

	def dragmotion(self, event):
		#print(event.x, event.y)
		self.mousepositionsx.append(event.x)
		self.mousepositionsy.append(event.y)
		self.mousepositionsx = self.mousepositionsx[-20:]
		self.mousepositionsy = self.mousepositionsy[-20:]
		print(event.x, event.y)

	def mousestate(self, state):
		self.ismousepressed = state

	def velocitymanager(self):
		while True:
			if not self.ismousepressed:
				try:
					self.velocityx = (sum(self.mousepositionsx)/len(self.mousepositionsx)) - self.mousepositionsx[-1]
					self.velocityy = (sum(self.mousepositionsy)/len(self.mousepositionsy)) - self.mousepositionsy[-1]
				except:
					self.velocityx = 0
					self.velocityy = 0
				self.velocityx = int(self.velocityx * 0.9)
				self.velocityy = int(self.velocityy * 0.9)
			#print(self.velocityx, self.velocityy, self.ismousepressed)
			if abs(self.velocityx) < 2:
				self.velocityx = 0
			if abs(self.velocityy) < 2:
				self.velocityy = 0
			time.sleep(0.0165)
			#60 fps baby
			self.labelvelocityind.configure(text="•")
			self.labelvelocityind.place(x=512+self.velocityx, y=288+self.velocityy)
			self.mousepositionsx = self.mousepositionsx[1:]
			self.mousepositionsy = self.mousepositionsy[1:]




tabblet = Tabblet()