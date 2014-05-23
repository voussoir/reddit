from cx_Freeze import setup, Executable
setup(
	name = "RedditInbox",
	version = "1.0",
	description = "Check your Karma privilege",
	executables = [Executable("RedditInbox.py")]
)