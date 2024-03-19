"""A plugin containing core features of Asura."""

from typing import Callable
import threading
import logging

from plugins.plugin import Plugin
from darzapacketlib.server import ChatsPacket, ReconnectPacket
from darzapacketlib.packet_types import Color
from darzapacketlib.packet_ids import PACKET_NAME_TO_ID

logger = logging.getLogger('AsuraCorePlugin')

class AsuraCorePlugin(Plugin):
    """
    A plugin containing core features of Asura.
    """
    def __init__(self, proxy):
        self.proxy = proxy
        self.color = Color(255, 255, 220, 220)
        self.filter = []

    def on_map_info(self, packet_bytes: bytes, _packet_id: int):
        """Send greeting."""

        chats_packet = ChatsPacket.from_msg('Connected to Asura!', self.color)
        self.proxy.send(self.proxy.conn_to_client, chats_packet.to_raw_bytes())

        return packet_bytes

    def on_reconnect(self, packet_bytes, _packet_id: int):
        """Handle reconnects."""

        reconnect_packet = ReconnectPacket.from_bytes(packet_bytes)

        self.proxy.remote_host = reconnect_packet.host
        self.proxy.remote_port = reconnect_packet.port

        self.proxy.reconnecting = True
        self.proxy.connected = False

        logger.info('Reconnect request received. Restarting Proxy -> Server thread...')

        self.proxy.conn_to_server.close()
        conn_server_thread = threading.Thread(
            target=self.proxy.connect_server
        )
        conn_server_thread.start()

        new_packet = ReconnectPacket.from_params(self.proxy.local_host, self.proxy.local_port)

        return new_packet.to_raw_bytes()

    def get_hooks(self) -> dict[int, Callable]:
        """Hooks."""

        return {
            PACKET_NAME_TO_ID['MapInfo']: self.on_map_info,
            PACKET_NAME_TO_ID['Reconnect']: self.on_reconnect
        }
