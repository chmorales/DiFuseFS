from argparse import ArgumentParser
import binascii
from constants import DIFUSE_PORT
from hashlib import sha256
from protocol import MAX_MESSAGE_LEN, Opcode, read_message, write_message, message_addr
from socket import socket, AF_INET, SOCK_STREAM
from stat import ST_MODE
import syscalls


CONN_QUEUE_LENGTH = 20

class Peer():

    def __init__(self, interface, port, boot_ip, boot_port):
        # Create local storage folder
        syscalls.create_localstorage()
        self.bootstrap = boot_ip
        # Create listening socket
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind((interface, port))
        self.sock.listen(CONN_QUEUE_LENGTH)
        # Bookkeeping
        self.peerlist = [] # Should be a list of tuples sorted by the first element
        self.files = []

    # Peer tuple is of format (iphash, ipaddress)
    def add_peer(self, peer_ip, peer_hash):
        for i in range(len(self.peerlist)):
            if self.peerlist[i][0] < peer_hash:
                self.peerlist.insert(i, (peer_hash, peer_ip))
                return
        self.peerlist.append()

    def remove_peer(self, peer_ip, peer_hash):
        for i in range(len(self.peerlist)):
            if self.peerlist[i][0] == peer_hash:
                return self.peerlist.pop(i)

    def prev_peer(self):
        for i in range(len(self.peerlist)):
            if self.peerlist[i][0] == self.myhash:
                return self.peerlist[i - 1]
        return None

    def next_peer(self):
        for i in range(len(self.peerlist)):
            if self.peerlist[i][0] > self.myhash:
                return self.peerlist[i]
        return self.peerlist[0]

    def start(self):
        # Contact bootstrap and ask to join network
        resp = remote_call(self.bootstrap, Opcode.JOIN)
        if resp['opcode'] == Opcode.ERROR:
            print(resp['body']['message'])
            exit(1)
        self.peerlist = resp['body']['peers']
        self.myhash = resp['body']['hash']
        # Contact next node and ask for files
        neighbor = self.next_peer()
        
        # Listen and action loop
        actions = {
            Opcode.CHMOD: syscalls.chmod,
            Opcode.CREATE: syscalls.create,
            Opcode.GETATTR: syscalls.getattr,
            Opcode.OPEN: syscalls.open,
            Opcode.READ: syscalls.read,
            Opcode.READDIR: syscalls.readdir,
            Opcode.UNLINK: syscalls.unlink,
            Opcode.WRITE: syscalls.write,
            Opcode.JOIN: self.add_peer,
            Opcode.LEAVE: self.remove_peer
        }
        while True:
            conn, addr = self.sock.accept()
            req = read_message(conn)
            try:
                # Body consists of args to local functions
                args = req['body']
                try:
                    ret = actions[req['opcode']](conn, **args)
                except OSError as e:
                    write_message(conn, Opcode.ERROR, message='OSError: {}'.format(e.errno))
            except KeyError:
                write_message(conn, Opcode.ERROR, message='Unsupported opcode.')
            conn.close()

    def shutdown(self):
        # Contact bootstrap announcing leave
        remote_call(self.bootstrap, Opcode.LEAVE)
        # Open and write all local files to next peer
        neighbor = self.prev_peer()
        for filename in syscalls.readdir('/')[2:]:
            remote_call(neighbor[1], Opcode.CREATE, path=filename, mode=syscalls.getattr(filename)[ST_MODE])
            data = syscalls.read(filename, MAX_MESSAGE_LEN, 0)
            remote_call(neighbor[1], Opcode.WRITE, path=filename, data=binascii.hexlify(data), offset=0)
            exit(1)


def remote_call(ipaddress, opcode, **kwargs):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((ipaddress, DIFUSE_PORT))
    write_message(sock, opcode, **kwargs)
    resp = read_message(sock)
    sock.close()
    return resp