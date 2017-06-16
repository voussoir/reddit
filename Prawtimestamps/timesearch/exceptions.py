class DBNotFound(FileNotFoundError):
    def __init__(self, path):
        self.path = path
