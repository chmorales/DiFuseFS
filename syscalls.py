import os


LOCALSTORAGE_DIR = '.localstorage'

def create_localstorage():
    os.mkdir(LOCALSTORAGE_DIR)

def localpath(path):
    return LOCALSTORAGE_DIR + path

def exists(path):
    return os.path.exists(localpath(path))

def chmod(path, mode):
    os.chmod(localpath(path), mode)
    return 0

def create(path, mode):
    os.close(os.open(localpath(path), os.O_CREAT, mode=mode))
    return 0

# Fuse should turn into dict, not here
def getattr(path, fh=None):
    return os.stat(localpath(path))

def open(path, flags):
    os.close(os.open(localpath(path), flags))
    return 0

def read(path, size, offset, fh=None):
    fd = os.open(localpath(path), os.O_RDONLY)
    os.lseek(fd, offset, os.SEEK_SET)
    data = os.read(fd, size)
    os.close(fd)
    return data

def readdir(path, fh=None):
    dirs = ['.', '..']
    dirs.extend(os.listdir(path=localpath(path)))
    return dirs

def unlink(path):
    os.remove(localpath(path))
    return 0

def write(path, data, offset, fh=None):
    fd = os.open(localpath(path), os.O_RDWR)
    os.lseek(fd, offset, os.SEEK_SET)
    numbytes = os.write(fd, data)
    os.close(fd)
    return numbytes