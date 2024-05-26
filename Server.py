import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def start_server():
    sock.bind(("localhost", 8080))

    sock.listen(1)
