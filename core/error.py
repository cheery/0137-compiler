class CrunchError(Exception):
    def __init__(self, msg, node):
        self.msg  = msg
        self.node = node
