import socket
import errno
import pickle

import asyncio
import aioconsole

from RC5 import RC5_key_generator
from CBC_RC5 import RC5_CBC_encryption, RC5_CBC_decryption


HEADER_SIZE = 10
SERVER_IP = socket.gethostname()
SERVER_PORT = 5000

CLIENT_KEY = []  # both keys are EXPANDED keys from the initial key seed found in client_key and server_key files
SERVER_KEY = []

SLEEP_TIME = 0.01  # in seconds


def receive(client_socket):

    try:

        message_header = client_socket.recv(HEADER_SIZE)
        if message_header:
            message_length = int(message_header.decode('utf-8'))

            message_with_sender = client_socket.recv(message_length)
            message_with_sender = pickle.loads(message_with_sender)

            sender = RC5_CBC_decryption(message_with_sender[0][0], SERVER_KEY, message_with_sender[0][1]).decode('utf-8')

            decryption_key = 0

            if sender == 'SERVER':
                decryption_key = SERVER_KEY
            else:
                decryption_key = CLIENT_KEY

            message = RC5_CBC_decryption(message_with_sender[1][0], decryption_key, message_with_sender[1][1]).decode('utf-8')

            message_pack = (sender, message)

            return message_pack  # tuple of (username that has sent the message, message)

        else:
            return False

    except socket.error as err:

        if err.errno == errno.WSAECONNRESET:
            print(f"connection with server {(SERVER_IP, SERVER_PORT)} has been forcibly closed")
            quit()


def show_msg(message_pack):
    print(f"{message_pack[0]} > {message_pack[1]}")


def send_msg(client_socket, msg_pack, encryption_key):

    try:
        msg_pack_encrypted = (RC5_CBC_encryption(msg_pack[0].encode('utf-8'), SERVER_KEY), RC5_CBC_encryption(msg_pack[1].encode('utf-8'), encryption_key))
        to_send = pickle.dumps(msg_pack_encrypted)

        to_send = f"{len(to_send):<{HEADER_SIZE}}".encode('utf-8') + to_send

        client_socket.send(to_send)

    except socket.error as err:

        if err.errno == errno.WSAECONNRESET:
            print(f"server with address {(SERVER_IP, SERVER_PORT)} has forcibly closed the connection")


def auth():

    # auth procedure

    print("please write your username, press ENTER then write the corresponding password and press ENTER again")

    username = input("username > ")
    password = input("password > ")

    auth_data = pickle.dumps({'username': username, 'password': password})
    auth_data_encrypted = RC5_CBC_encryption(auth_data, SERVER_KEY)
    auth_data_encrypted = pickle.dumps(auth_data_encrypted)
    auth_data_to_send = f"{len(auth_data_encrypted):<{HEADER_SIZE}}".encode('utf-8') + auth_data_encrypted

    client_socket.connect((SERVER_IP, SERVER_PORT))
    client_socket.send(auth_data_to_send)

    client_socket.settimeout(1)

    auth_rez = receive(client_socket)
    if auth_rez:
        show_msg(auth_rez)
    else:
        print("authentication failed (wrong username / password or username is already online); client app is now closed")
        quit()


# socket init

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("socket initialized")

# key init

SERVER_KEY = RC5_key_generator(int(open("server_key.txt").read()))
CLIENT_KEY = RC5_key_generator(int(open("client_key.txt").read()))

auth()

client_socket.settimeout(1)

# main loops after successful auth

# ------------------------- IMPLEMENTATION NOTE ----------------------------
# due to being implemented without proper user interface, input and output might overlap in the console
# in a slightly inconvenient way (DOES NOT impair functionality)
# ------------------------- ------------------- ----------------------------


async def input_loop():

    while True:

        receiver = await aioconsole.ainput("send message to : ")
        message_to_send = await aioconsole.ainput("message > ")

        send_msg(client_socket, (receiver, message_to_send), CLIENT_KEY)


async def receive_loop():

    while True:

        msg_received_pack = receive(client_socket)
        if msg_received_pack:

            print("(incoming messages, write the destination/ message after receiving following messages)")

            show_msg(msg_received_pack)

        await asyncio.sleep(SLEEP_TIME)


async def main_client_loop():

    tasks = [asyncio.create_task(receive_loop()), asyncio.create_task(input_loop())]

    await asyncio.gather(*tasks)


asyncio.run(main_client_loop())








