from functools import total_ordering
import socket
import json
import select
import array
import copy

HOST = "ecast.jackboxgames.com"
SERVER_IP = socket.gethostbyname(HOST)
PORT = 80

CODE_LENGTH = 4
LAST_CHAR = 91
STARTING_CHAR = 65

CURR_CODE_LIST = ([65]*(CODE_LENGTH-1))+[64]
CURRENT_CODE = array.array('B',CURR_CODE_LIST)
def generate_code():
    reminder = 0

    CURRENT_CODE[CODE_LENGTH-1] += 1

    for i in range(CODE_LENGTH-1,-1,-1):
        if reminder == 1:
           CURRENT_CODE[i] += 1
           reminder = 0

        if CURRENT_CODE[i] == LAST_CHAR:
            CURRENT_CODE[i] = STARTING_CHAR
            reminder = 1
        else:
            break

    if reminder == 1:
        return None

    to_return = ""
    for ch in CURRENT_CODE:
        to_return += chr(ch)
    return to_return



FOUND_ROOMS = []
def found_handler(data:bytes, body_start:int):
    # body = json.loads(data[body_start:].decode('ascii'))
    # print("Found:",body)
    FOUND_ROOMS.append(data[body_start:])

def not_found_handler(data:bytes, body_start:int):
    pass


PAYLOAD = "GET /api/v2/rooms/{room} HTTP/1.1\r\nHost: ecast.jackboxgames.com\r\nConnection: keep-alive\r\n\r\n"
# http://ecast.jackboxgames.com/api/v2/rooms/AFTY
def bruteforce(n_connections:int):
    global CURRENT_CODE

    connections = []
    for i in range(n_connections):
        sock = socket.socket()
        sock.setblocking(False)
        try:
            sock.connect((SERVER_IP,PORT))
        except:
            pass
        connections.append(sock)

    run = True
    while run:
        rs,ws,es = select.select(connections,connections,connections)
        
        for w in ws:
            prev_code = copy.copy(CURRENT_CODE)
            room = generate_code()
            if room is None:
                run = False
                break

            payload = PAYLOAD.format(room=room).encode("ascii")

            try:
                w.sendall(payload)
            except:
                CURRENT_CODE = prev_code

        for r in rs:
            p_data = r.recv(20000,socket.MSG_PEEK)
            eol = p_data.find(b"\r\n\r\n")

            start = p_data.find(b"Content-Length:")
            if start == -1:
                continue
            end = p_data.find(b"\r",start+15)
            if end == -1:
                continue

            body_length = int(p_data[start+15:end].decode("ascii"))

            total_length = eol+body_length+4

            if eol == -1\
                or len(p_data)<total_length:
                continue

            data = r.recv(total_length)
            
            if data == b'':
                es.append(r)

            
            if data[9:12] == b"404":
                # not found
                not_found_handler(data, eol+4)
            else:
                # found
                found_handler(data, eol+4)

        for e in es:
            index = connections.index(e)
            sock = socket.socket()
            sock.setblocking(False)
            try:
                sock.connect((SERVER_IP,PORT))
            except:
                pass
            connections[index] = sock



def main():
    n_connections = 300
    bruteforce(n_connections)

    for room in FOUND_ROOMS:
        print(json.loads(room.decode('ascii')))


if __name__ == "__main__":
    main()
