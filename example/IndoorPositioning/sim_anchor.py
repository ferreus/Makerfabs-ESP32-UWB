#!/usr/bin/env python
import sys
from PyQt5.QtWidgets import QAction, QLabel, QMainWindow, QApplication, QPushButton, QTabWidget, QHBoxLayout,QVBoxLayout, QWidget, QToolButton, QLineEdit
from PyQt5.QtCore import QObject,pyqtSignal
import random
import json
import socket
UDP_PORT = 4545


class Window(QMainWindow):
    def __init__(self, parent=None):
        super(Window,self).__init__(parent)
        self.init_ui()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addr = ("127.0.0.1",4545)


    def init_ui(self):
        layout = QVBoxLayout()
        self.txt1 = QLineEdit()
        self.txt2 = QLineEdit()
        self.txt3 = QLineEdit()
        self.txt4 = QLineEdit()
        self.anchors = (self.txt1, self.txt2, self.txt3, self.txt4)
        addr = 0x00
        random.seed()
        for a in self.anchors:
            addr += 1
            box = QHBoxLayout()
            box.addWidget(QLabel(hex(addr)))
            box.addWidget(a)
            r = random.randint(1,10)
            a.setText(str(r))
            layout.addLayout(box)

        self.btnStart = QPushButton("▶️")
        self.btnStop = QPushButton("⏹️")
        self.btnSend = QPushButton("✉️")
        box = QHBoxLayout()
        box.addWidget(self.btnStart)
        box.addWidget(self.btnStop)
        box.addWidget(self.btnSend)
        layout.addLayout(box)
        self.btnStart.clicked.connect(self.on_start)
        self.btnStop.clicked.connect(self.on_stop)
        self.btnSend.clicked.connect(self.on_send)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        pass

    def on_start(self):
        print("Start")

    def on_stop(self):
        print("Stop")

    def on_send(self):
        data = dict()
        addr = 0x00
        links = []
        for a in self.anchors:
            addr += 1
            item = dict()
            item["A"] = addr
            item["R"] = int(a.text())
            links.append(item)
        data["links"] = links
        print(json.dumps(data,indent = 4))
        data_str = json.dumps(data, indent = 4)
        payload = str.encode(data_str)
        self.sock.sendto(payload, self.addr)



def main():
    app = QApplication(sys.argv)
    main = Window()
    main.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
