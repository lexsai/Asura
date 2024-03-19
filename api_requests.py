"""This module contains functions for accessing resources on the game's web server."""

import logging
from typing import TypedDict
import requests

from constants.hosts import WEB_SERVER, API_BASE, SERVER_LIST_ENDPOINT

API_URL = WEB_SERVER + API_BASE

logger = logging.getLogger('API Requester')

class ServerInfo(TypedDict):
    """A class representing a game server."""

    host: str
    serverName: str
    region: str
    time: int

def fetch_server_list() -> list[ServerInfo]:
    """Fetch available game servers from the game's web API."""

    url = API_URL + SERVER_LIST_ENDPOINT
    response = requests.get(url, timeout = 10000)

    response.raise_for_status()

    logger.info('Received serverlist: "%s"', response.json())

    return response.json()['servers']
