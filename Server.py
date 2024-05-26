import socket
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

address = "localhost" if len(sys.argv) < 3 else sys.argv[2]
port = 8080 if len(sys.argv) < 4 else int(sys.argv[3])
is_client = len(sys.argv) > 1 and sys.argv[1] == "client"
is_server = len(sys.argv) > 1 and sys.argv[1] == "server"


def start_server(address="localhost", port=8080):
    sock.bind((address, port))

    sock.listen(1)
