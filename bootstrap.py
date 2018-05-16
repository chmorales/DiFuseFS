from argparse import ArgumentParser
from constants import DIFUSE_PORT
from hashlib import sha256
from protocol import Opcode, write_message, read_message, message_addr
from socket import socket, AF_INET, SOCK_STREAM


class Bootstrap():

    def __init__(self, interface):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind((interface, DIFUSE_PORT))
        self.sock.listen(20)
        self.peerlist = [] # list of tuples in format (peer_iphash, peer_ip)

    def peer_inlist(self, peer_iphash):
        for peer_tuple in self.peerlist:
            if peer_tuple[0] == peer_iphash:
                return True
        return False

    def add_peer(self, peer_ip, peer_iphash):
        for i in range(len(self.peerlist)):
            if peer_iphash < self.peerlist[i][0]:
                self.peerlist.insert(i, (peer_iphash, peer_ip))
                return
        self.peerlist.append((peer_iphash, peer_ip))

    def remove_peer(self, peer_iphash):
        for i in range(len(self.peerlist)):
            if self.peerlist[i][0] == peer_iphash:
                return self.peerlist.pop(i)

    def peer_join(self, join_conn, join_ip):
        # Check to see if ip already exists in peerlist
        join_iphash = sha256(join_ip.encode()).hexdigest()
        if self.peer_inlist(join_iphash):
            write_message(join_conn, Opcode.ERROR, message='IP already in network.')
            return
        # Let other peers know that this peer is joining
        for peer_tuple in self.peerlist:
            sock = socket(AF_INET, SOCK_STREAM)
            sock.connect((peer_tuple[1], DIFUSE_PORT))
            write_message(sock, Opcode.JOIN, peer_ip=join_ip, hash=join_iphash)
            sock.close()
        self.add_peer(join_ip, join_iphash)
        write_message(join_conn, Opcode.JOIN, status='ok', peers=self.peerlist, hash=join_iphash)

    def peer_leave(self, leave_conn, leave_ip):
        # Remove peer for peerlist
        leave_iphash = sha256(leave_ip.encode()).hexdigest()
        self.remove_peer(leave_iphash)
        # Let other peers know this peer is leaving
        for peer_tuple in self.peerlist:
            sock = socket(AF_INET, SOCK_STREAM)
            sock.connect((peer_tuple[1], DIFUSE_PORT))
            write_message(sock, Opcode.LEAVE, peer_ip=leave_ip, hash=leave_iphash)
            sock.close()
        write_message(leave_conn, Opcode.LEAVE, status='ok')

    def start(self):
        actions = {
            Opcode.JOIN: self.peer_join,
            Opcode.LEAVE: self.peer_leave
        }
        while True:
            conn, addr = self.sock.accept()
            req = read_message(conn)
            try:
                actions[req['opcode']](conn, addr[0])
            except KeyError:
                write_message(conn, Opcode.ERROR, message='Unsupported opcode.')
            conn.close()
        