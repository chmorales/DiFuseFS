from construct import BytesInteger, PascalString, Struct
from enum import IntEnum
import json
from socket import socket, AF_INET, SOCK_STREAM

OPCODE_LEN = 1
LEN_FIELD_LEN = 3
MAX_MESSAGE_LEN = 10 * (2 ** 20)

class Opcode(IntEnum):
    JOIN = 0
    LEAVE = 1
    ERROR = 2
    CHMOD = 3
    CREATE = 4
    GETATTR = 5
    OPEN = 6
    READ = 7
    READDIR = 8
    UNLINK = 9
    WRITE = 10
    TAKE = 11


MESSAGE = Struct(
    'opcode' / BytesInteger(OPCODE_LEN),
    'body' / PascalString(BytesInteger(LEN_FIELD_LEN), 'ascii')
)

def read_message(socket):
    header = socket.recv(3)
    body = socket.recv(BytesInteger(4).parse(header[1:]))
    message = MESSAGE.parse(header + body)
    message['body'] = json.loads(message['body'])
    return message

def write_message(socket, opcode, **kwargs):
    socket.send(MESSAGE.build(dict(opcode=opcode, body=json.dumps(kwargs))))

def message_addr(addr, opcode, **kwargs):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(addr)
    write_message(sock, opcode, **kwargs)
    resp = read_message(sock)
    sock.close()
    return resp
