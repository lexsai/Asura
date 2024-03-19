"""
This module contains a class representing a proxy server between game client and game server.
"""

import logging
import select
import struct
import socket

from constants.hosts import GAME_PORT
from plugin_manager import PluginManager

logger = logging.getLogger("Proxy")

class ProxyServer:
    """
    Represents a proxy server between game client and game server.
    """
    def __init__(self, host: str) -> None:
        self.local_host: str = "127.0.0.1"
        self.local_port: int = GAME_PORT

        self.remote_host: str = host
        self.remote_port: int = GAME_PORT

        self.proxy_socket: socket.socket | None = None
        self.conn_to_client: socket.socket | None = None
        self.conn_to_server: socket.socket | None = None

        self.reconnecting: bool = False
        self.connected: bool = False
        self.kill: bool = False

        self.plugins = PluginManager(self)
        self.plugins.load()

    def listen(self) -> None:
        """
        Listen for packets from the client and server.
        """
        while not self.kill:
            if not self.connected:
                continue

            readable = select.select(
                [self.conn_to_client, self.conn_to_server],
                [], []
            )[0]

            if self.conn_to_client in readable:
                packet_id, packet_bytes = self.recv(self.conn_to_client, False)
                if self.plugins.is_hooked(packet_id):
                    packet_bytes = self.plugins.process_hooks(packet_id, packet_bytes)
                if packet_bytes:
                    self.send(self.conn_to_server, packet_bytes)

            if self.conn_to_server in readable:
                packet_id, packet_bytes = self.recv(self.conn_to_server, True)
                if self.plugins.is_hooked(packet_id):
                    packet_bytes = self.plugins.process_hooks(packet_id, packet_bytes)
                if packet_bytes:
                    self.send(self.conn_to_client, packet_bytes)

    def connect_client(self) -> None:
        """
        Opens a socket for the client to connect. 
        Run in a different thread.
        """
        self.proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy_socket.bind((self.local_host, self.local_port))
        self.proxy_socket.listen()
        logger.info('Client -> Proxy - Listening for client connection...')

        # Keep the socket open to connections
        while not self.kill:
            self.conn_to_client = self.proxy_socket.accept()[0]
            self.reconnecting = False
            logger.info('Client -> Proxy - Client connection received.')

        logger.info('Client -> Proxy - Client connection thread killed.')

    def connect_server(self) -> None:
        """
        Attempts to open a connection to the server. 
        Run in a different thread.
        """

        # Block until client connects to proxy.
        logger.info('Proxy -> Server - Waiting for client connection...')
        while not self.conn_to_client or self.reconnecting:
            if self.kill:
                logger.info('Proxy -> Server - Game connection thread killed.')
                return

        logger.info('Proxy -> Server - Connecting to game server...')
        self.conn_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn_to_server.connect((self.remote_host, self.remote_port))
        self.connected = True
        logger.info('Proxy -> Server - Connected to game server.')

    def send(self, sock: socket.socket, data: bytes) -> None:
        """
        Send data to the socket specified.
        """
        if not self.kill and isinstance(sock, socket.socket):
            sock.sendall(data)

    def recv(self, sock: socket.socket, recv_from_server: bool) -> tuple[int, bytes]:
        """
        Receive one packet from the socket.
        Returns the received packet.
        """
        assert isinstance(sock, socket.socket)

        raw_packet_size = sock.recv(4)
        packet_size = struct.unpack('<I', raw_packet_size)[0]

        raw_packet_id = sock.recv(1)
        packet_id = struct.unpack('B', raw_packet_id)[0]

        left_to_read = packet_size - 1

        raw_packet_data = bytearray()
        while len(raw_packet_data) < left_to_read:
            if left_to_read - len(raw_packet_data) < 2048:
                if recv_from_server:
                    raw_packet_data += sock.recv(left_to_read - len(raw_packet_data))
                else:
                    raw_packet_data += sock.recv(left_to_read % 2048)
            else:
                raw_packet_data += sock.recv(2048)

        packet_bytes = raw_packet_size + raw_packet_id + raw_packet_data

        return packet_id, packet_bytes

    def close(self) -> None:
        """
        Close all active connections to both client and server.
        """
        logger.info('Shutting down...')

        if self.conn_to_server:
            self.conn_to_server.close()

        if self.proxy_socket:
            self.proxy_socket.close()

        self.kill = True
