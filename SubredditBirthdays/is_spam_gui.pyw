import tkinter
import sqlite3
import webbrowser

class SpamGUI:
	def __init__(self):
		self.t = tkinter.Tk()
		self.t.pack_propagate(0)

		self.w = 400
		self.h = 350
		self.URL = "http://reddit.com/r/%s"

		self.sql = sqlite3.connect('sql.db')
		self.cur = self.sql.cursor()
		self.current_idint = 0
		self.suspected = []

		self.label_subredditname = tkinter.Label(self.t, text="", font=("Consolas", 12))
		self.label_subreddittype = tkinter.Label(self.t, text="Subreddit type: ", font=("Consolas", 10))
		self.label_submissiontype = tkinter.Label(self.t, text="Submission type: ", font=("Consolas", 10))
		self.spinbox_subreddittype = tkinter.Spinbox(self.t, from_=-1, to=6, width=2, font=("Consolas", 10))
		self.spinbox_subreddittype.delete(0, "end")
		self.spinbox_subreddittype.insert(0, 1)
		self.spinbox_submissiontype = tkinter.Spinbox(self.t, from_=-1, to=3, width=2, font=("Consolas", 10))
		self.spinbox_submissiontype.delete(0, "end")
		self.spinbox_submissiontype.insert(0, -1)

		self.button_yes_frame = tkinter.Frame(self.t, height=50, width=120)
		self.button_pass_frame = tkinter.Frame(self.t, height=50, width=40)
		self.button_no_frame = tkinter.Frame(self.t, height=50, width=120)
		self.button_browser_frame = tkinter.Frame(self.t, height=40, width=(self.w * 0.75))
		self.button_yes_frame.pack_propagate(0)
		self.button_pass_frame.pack_propagate(0)
		self.button_no_frame.pack_propagate(0)
		self.button_browser_frame.pack_propagate(0)
		self.button_yes = tkinter.Button(self.button_yes_frame, text="Yes", font=("Consolas", 10), relief="flat", bg="#76E22E", activebackground="#76E22E", command=lambda: self.mark(direction=1))
		self.button_pass = tkinter.Button(self.button_pass_frame, text="Pass", font=("Consolas", 10), relief="flat", bg="#f1c40f", activebackground="#f1c40f", command=lambda: self.mark(direction=-1))
		self.button_no = tkinter.Button(self.button_no_frame, text="No", font=("Consolas", 10), relief="flat", bg="#E23939", activebackground="#E23939", command=lambda: self.mark(direction=0))
		self.button_browser = tkinter.Button(self.button_browser_frame, text="open", font=("Consolas", 10), relief="flat", bg="#6fd5f6", activebackground="#6fd5f6", command=self.openbrowser)
		self.button_yes.pack(fill="both", expand=1)
		self.button_no.pack(fill="both", expand=1)
		self.button_pass.pack(fill="both", expand=1)
		self.button_browser.pack(fill="both", expand=1)
		self.button_refresh = tkinter.Button(self.t, text="refresh", font=("Consolas", 10), relief="flat", bg="#6fd5f6", activebackground="#6fd5f6", command=self.refresh)

		self.label_subredditname.place(x=(self.w/2), y=40, anchor="center")
		self.button_yes_frame.place(x=(self.w/8), y=150, anchor="w")
		self.button_pass_frame.place(x=(self.w/2), y=150, anchor="c")
		self.button_no_frame.place(x=(self.w - (self.w/8)), y=150, anchor="e")
		self.button_browser_frame.place(x=(self.w/2), y=100, anchor="c")
		self.label_subreddittype.place(x=(self.w/2)-5, y=250, anchor="e")
		self.spinbox_subreddittype.place(x=(self.w/2)+5, y=250, anchor="w")
		self.label_submissiontype.place(x=(self.w/2)-5, y=275, anchor="e")
		self.spinbox_submissiontype.place(x=(self.w/2)+5, y=275, anchor="w")
		self.button_refresh.place(x=(self.w/2), y=310, anchor="c")

		self.screenwidth = self.t.winfo_screenwidth()
		self.screenheight = self.t.winfo_screenheight()
		self.windowwidth = self.w
		self.windowheight = self.h
		self.windowx = (self.screenwidth-self.windowwidth) / 2
		self.windowy = ((self.screenheight-self.windowheight) / 2) - 27
		self.geometrystring = '%dx%d+%d+%d' % (self.windowwidth, self.windowheight, self.windowx, self.windowy)
		self.t.geometry(self.geometrystring)

		self.t.mainloop()

	def refresh(self):
		subreddit_type = int(self.spinbox_subreddittype.get())
		submission_type = int(self.spinbox_submissiontype.get())
		if submission_type == -1:
			self.cur.execute('SELECT * FROM subreddits WHERE IS_SPAM = ? AND SUBREDDIT_TYPE=? AND SUBMISSION_TYPE != ?', [-1, subreddit_type, 3])
		else:
			self.cur.execute('SELECT * FROM subreddits WHERE IS_SPAM = ? AND SUBREDDIT_TYPE=? AND SUBMISSION_TYPE = ?', [-1, subreddit_type, submission_type])
		self.suspected = list(self.cur.fetchall())
		self.suspected.sort(key=lambda x: x[1], reverse=True)
		self.shownext()

	def mark(self, direction):
		if self.current_idint != 0:
			print(self.current_idint, direction)
			self.cur.execute('UPDATE subreddits SET IS_SPAM=? WHERE IDINT=?', [direction, self.current_idint])
			self.sql.commit()
		self.shownext()

	def shownext(self):
		self.suspected = self.suspected[1:]
		try:
			next = self.suspected[0]
			self.current_idint = next[7]
			self.label_subredditname.configure(text=next[4])
		except:
			self.current_idint = 0
			self.label_subredditname.configure(text='[no more found]')

	def openbrowser(self):
		redditname = self.label_subredditname.cget("text")
		if redditname:
			url = self.URL % redditname
			webbrowser.open(url)

spamgui = SpamGUI()