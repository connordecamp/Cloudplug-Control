import sys
from typing import List
from collections import defaultdict
import struct, time

from PyQt5.QtCore import QByteArray, QObject, pyqtSignal
from PyQt5.QtNetwork import QAbstractSocket, QHostAddress, QTcpServer, QTcpSocket

from modules.network.message import Message, MessageCode, unpackRawBytes
from modules.network.utility import *

class MyTCPServer(QObject):

    client_connected_signal = pyqtSignal(object)
    client_disconnected_signal = pyqtSignal(str)

    # Sends ONLY a number to the UI thread that
    # can handle updating things
    update_ui_signal = pyqtSignal(MessageCode)

    # Emit messages to the main windows log
    log_signal = pyqtSignal(object)

    # A dictionary of connected sockets, with the ip string
    # as the key and the socket object as the value
    connected_socket_dict: defaultdict

    def __init__(self, parent=None):
        super(MyTCPServer, self).__init__(parent)
        self.server = None
        self.connected_socket_dict = defaultdict(None)
        self.connected_dock_dict = {}
        self.connected_cloudplug_dict = {}

    def openSession(self):
                
        self.server = QTcpServer()
        self.HOST = get_LAN_ip_address()
        self.PORT = 20100
        
        self.server.newConnection.connect(self.handleNewConnection)

        if not self.server.listen(QHostAddress(self.HOST), self.PORT):
            raise Exception(f"Server failed to listen on {self.HOST}:{self.PORT}")
        
        self.log_signal.emit(f'TCP Server listening on {self.HOST}:{self.PORT}')

    def initDockConnection(self, sender_ip):
        self.connected_dock_dict[sender_ip] = ''

    def initCloudplugConnection(self, sender_ip):
        self.connected_cloudplug_dict[sender_ip] = ''

    def handleNewConnection(self):
        
        client_connection = self.server.nextPendingConnection()
        print(f'{client_connection.peerAddress() = }')
        client_ip = client_connection.peerAddress().toString()
        
        if client_ip in self.connected_dock_dict:
            self.connected_dock_dict[client_ip] = client_connection
            self.client_connected_signal.emit((DeviceType.DOCKING_STATION, client_ip))
        elif client_ip in self.connected_cloudplug_dict:
            self.connected_cloudplug_dict[client_ip] = client_connection
            self.client_connected_signal.emit((DeviceType.CLOUDPLUG, client_ip))
        else:
            print(f"Unknown IP address: {client_ip}")
            return

        

        #self.connected_socket_dict[client_ip] = client_connection
        print(f'Incoming client connection from {client_ip}')
        
        # Set up the disconnected signal
        client_connection.disconnected.connect(self.handleClientDisconnect)
        client_connection.readyRead.connect(self.handleClientMessage)
        client_connection.stateChanged.connect(self.handleClientStateChange)

        self.log_signal.emit(f'Client connected from {client_ip}')

        # Add new client to the list of current connections
        #if client_connection not in self.connected_socket_list:
        #    self.connected_socket_list.append(client_connection)
        #    # Emit client IP as data
        #    print('Added socket to list')
        #    self.log_signal.emit(f'Client connected from {client_connection.peerAddress().toString()}')

    def handleClientDisconnect(self):
        # Technically bad design, but we need to know
        # which client disconnected
        client: QTcpSocket = self.sender()

        print(f'{client.peerAddress() = }')
        client_ip = client.peerAddress().toString()

        self.log_signal.emit(f'Client at {client.peerAddress().toString()} disconnected')
        print(f'Client disconnected: {client.peerAddress().toString() = }')
        print(f'There were {client.bytesAvailable()} bytes waiting to be processed')

        if client_ip in self.connected_dock_dict:
            self.connected_dock_dict.pop(client_ip)
            self.client_disconnected_signal.emit((DeviceType.DOCKING_STATION, client_ip))
        
        if client_ip in self.connected_cloudplug_dict:
            self.connected_cloudplug_dict.pop(client_ip)
            self.client_disconnected_signal.emit((DeviceType.CLOUDPLUG, client_ip))

        client.close()
        self.connected_socket_dict[client_ip] = None

    def handleClientMessage(self):
        '''
        Handler for when a client sends a message
        '''
        client_socket: QTcpSocket = self.sender()
        client_ip = client_socket.peerAddress().toString()
        client_port = client_socket.peerPort()
        raw_msg = client_socket.readAll()
        
        code, data = struct.unpack('!H254s', raw_msg)
        # Stripping \x00 may not be the best idea:
        # If the DATA part of the message must contain
        # zeros they would be removed...
        sent_cmd = Message(code, str(data, 'utf-8').strip('\x00'))

        print(sent_cmd)
        
        print(f'Client at {client_ip} sent a message: {sent_cmd}')
        self.log_signal.emit(f'Client at {client_ip} sent a message: {sent_cmd}')

        self.processClientMessage(client_ip, client_port, raw_msg)

    def processClientMessage(self, ip: str, port: int, raw_bytes: bytes):
        sent_cmd: Message = unpackRawBytes(raw_bytes)


        if sent_cmd.code == MessageCode.CLONE_SFP_MEMORY_ERROR:
            self.log_signal.emit(f'ERROR from DOCKING STATION at {ip}:{port} said: {sent_cmd.data}')
        elif sent_cmd.code == MessageCode.CLONE_SFP_MEMORY_SUCCESS:
            self.update_ui_signal.emit(MessageCode.CLONE_SFP_MEMORY_SUCCESS)

    def handleClientStateChange(self, state):

        # Show that the connection has been made
        if state == QAbstractSocket.ConnectedState:
            self.log_signal.emit('Connection established')

    def sendCommand(self, destination_ip: str, code: MessageCode, msg: str):
        '''
        This method sends a command to a destination IP address.
        '''
        if not self.connected_socket_dict[destination_ip]:
            print("Trying to send command to unknown IP")
            self.log_signal.emit(f"ERROR: Tried to send data to {destination_ip} which is an unknown destination.")
            return

        destination_socket: QTcpSocket = self.connected_socket_dict[destination_ip]
        
        command = Message(code, msg)
        raw_command = command.to_network_message()
        
        qba = QByteArray(raw_command)
        destination_socket.write(qba)

    def _close_all_connections(self):
        
        for key in self.connected_socket_dict:
            if self.connected_socket_dict[key] is not None:
                sock: QTcpSocket = self.connected_socket_dict[key]

                sock.disconnectFromHost()
                sock.waitForDisconnected()
                sock.close()




'''
def main():

    app = QApplication(sys.argv)
    tcp_server = MyTCPServer()
    tcp_server.openSession()
    tcp_server.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
'''