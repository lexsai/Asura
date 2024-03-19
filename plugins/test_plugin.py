"""A plugin for testing."""

from typing import Callable
import logging

from plugins.plugin import Plugin
from darzapacketlib.packet import Packet
from darzapacketlib.client import ChatPacket
from darzapacketlib.server import ChatsPacket
from darzapacketlib.packet_types import Color
from darzapacketlib.packet_ids import PACKET_NAME_TO_ID, PACKET_ID_TO_NAME

logger = logging.getLogger('TestPlugin')

class TestPlugin(Plugin):
    """
    A plugin for testing.
    """
    def __init__(self, proxy):
        self.proxy = proxy
        self.color = Color(255, 255, 220, 255)
        self.filter = []

    def on_all(self, packet_bytes: bytes, packet_id: int) -> bytes:
        """Log packets."""

        packet_class = Packet.id_to_class.get(packet_id, None)
        if packet_class and not packet_id in self.filter:
            packet = packet_class.from_bytes(packet_bytes)
            logger.info('%s %s', PACKET_ID_TO_NAME[packet_id], vars(packet))

        return packet_bytes

    def on_chat(self, packet_bytes: bytes, _packet_id: int) -> bytes:
        """Receive plugin commands."""

        chat_packet = ChatPacket.from_bytes(packet_bytes)

        args = chat_packet.text.split(' ')
        if args[0] == '/fadd':
            for arg in args[1:]:
                if not arg in PACKET_NAME_TO_ID or PACKET_NAME_TO_ID[arg] in self.filter:
                    continue

                self.filter.append(PACKET_NAME_TO_ID[arg])

                chats_packet = ChatsPacket.from_msg(
                    self.color,
                    f'Packet "{arg}" (id {PACKET_NAME_TO_ID[arg]}) added to filter.'
                )
                self.proxy.send(self.proxy.conn_to_client, chats_packet.to_raw_bytes())

                logger.info('Packet "%s" (ID %d) added to filter.', arg, PACKET_NAME_TO_ID[arg])
            return bytes()

        if args[0] == '/fremove':
            for arg in args[1:]:
                if not arg in PACKET_NAME_TO_ID:
                    continue

                self.filter.remove(PACKET_NAME_TO_ID[arg])

                chats_packet = ChatsPacket.from_msg(
                    self.color,
                    f'Packet "{arg}" (id {PACKET_NAME_TO_ID[arg]}) removed from filter.'
                )
                self.proxy.send(self.proxy.conn_to_client, chats_packet.to_raw_bytes())

                logger.info('Packet %s (ID %d) removed from filter.', arg, PACKET_NAME_TO_ID[arg])
            return bytes()

        if args[0] == '/color':
            if len(args) != 4:
                return bytes()

            chats_packet = ChatsPacket.from_msg(
                'This is a test message!',
                Color(255, int(args[1]), int(args[2]), int(args[3]))
            )
            self.proxy.send(self.proxy.conn_to_client, chats_packet.to_raw_bytes())
            return bytes()

        return packet_bytes

    def get_hooks(self) -> dict[int, Callable]:
        """Hooks."""

        return {
            # -1: self.on_all,
            PACKET_NAME_TO_ID['Chat']: self.on_chat
        }
