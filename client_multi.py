import socket
import errno

import time


HEADER_LENGTH = 10
SERVER_IP = socket.gethostname()
SERVER_PORT = 5000


def receive(client_socket):

    try:

        message_header = client_socket.recv(HEADER_LENGTH)

        if message_header:

            message_length = int(message_header.decode('utf-8'))
            message = client_socket.recv(message_length)
            message = message.decode('utf-8')

            return message
        else:
            return False

    except socket.error as err:

        if err.errno == errno.WSAECONNRESET:
            print(f"server with address ({SERVER_IP, SERVER_PORT}) has forcibly closed the connection")
            return False


def send_msg(client_socket, msg):

    try:

        client_socket.send(f'{len(msg):<{HEADER_LENGTH}}'.encode('utf-8') + msg.encode('utf-8'))

    except socket.error as err:

        if err.errno == errno.WSAECONNRESET:
            print(f"server with address ({SERVER_IP, SERVER_PORT}) has forcibly closed the connection")


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, SERVER_PORT))

cnt = 0

while True:

    message = "test"

    send_msg(client_socket, message + str(cnt))
    cnt += 1

    time.sleep(2)

    received = receive(client_socket)
    if received:
        print(received)
    else:
        quit()
