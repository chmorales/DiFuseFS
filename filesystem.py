from fuse import FUSE, Operations
from protocol import read_message, write_message, message_addr
import syscalls


class DiFuseFS(Operations):

    def __init__(self, bootstrap):
        self.bootstrap = bootstrap

    def chmod(self, path, mode):
        pass
    
    def create(self, path, mode):
        pass
    
    def getattr(self, path, fh=None):
        pass

    def open(self, path, flags):
        pass
    
    def read(self, path, size, offset, fh=None):
        pass
    
    def readdir(self, path, fh=None):
        pass

    def unlink(self, path):
        pass

    def write(self, path, data, offset, fh=None):
        pass