import socket


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("0.0.0.0",4545))
s,addr = sock.accept()
