import sys

from cx_Freeze import setup, Executable

base = None
if sys.platform == "win32":
    base = "Win32GUI"
    
setup(
	name = "RedditInbox",
	version = "1.0",
	description = "Check your Karma privilege",
	executables = [Executable("RedditInbox.py", base = base)]
)