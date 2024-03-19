"""This module contains a manager for the hooks of loaded plugins."""

import logging
from collections import defaultdict

from plugins import Plugin
from darzapacketlib.packet_ids import PACKET_ID_TO_NAME

logger = logging.getLogger('Plugin Manager')

class PluginManager:
    """
    Represents a manager for the hooks of loaded plugins.
    """
    def __init__(self, proxy):
        self.hooks = defaultdict(list)
        self.proxy = proxy
        self.has_global_hook = False

    def load(self):
        """
        Collect the hooks from the loaded into a dictionary of hooks. 
        """
        for plugin_class in Plugin.plugins:
            plugin_inst = plugin_class(self.proxy)
            hooks = plugin_inst.get_hooks()

            logger.info('Loading plugin %s...', plugin_class.__name__)
            for key, value in hooks.items():
                self.hooks[key].append(value)

                if key == -1:
                    self.has_global_hook = True

                logger.info(
                    'Packet "%s" hooked by %s.',        
                    PACKET_ID_TO_NAME[key] if key != -1 else '*',
                    plugin_class.__name__
                )

            logger.info(
                'Loaded %d hooks from plugin "%s"',
                len(hooks.items()),
                plugin_class.__name__
            )

        logger.info('Finished loading plugins. Loaded %d hook%s in total from %d plugin%s.',
            len(self.hooks.keys()),
            's' if len(self.hooks.keys()) > 1 else '',
            len(Plugin.plugins),
            's' if len(Plugin.plugins) > 1 else ''
        )

    def is_hooked(self, packet_id: int) -> bool:
        """
        Returns whether a particular packet, identified by packet id, is hooked by a plugin.
        """
        return packet_id in self.hooks or self.has_global_hook

    def process_hooks(self, packet_id: int, packet_bytes: bytes) -> bytes:
        """
        Processes the hooks for a particular packet.
        """
        hooked_bytes = packet_bytes
        for hook_func in self.hooks[packet_id] + self.hooks[-1]:
            hooked_bytes = hook_func(hooked_bytes, packet_id)
            if not hooked_bytes:
                break
        return hooked_bytes
