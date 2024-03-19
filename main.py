"""This module initializes the threads used by the proxy server."""

import logging
import threading

from proxy_server import ProxyServer
from api_requests import fetch_server_list
from constants.proxy import PREFERRED_SERVER

def main():
    """The main function. Iniitalizes the proxy and starts threads to run its functions."""

    logging.basicConfig(
        format='%(asctime)s | %(name)s | %(message)s',
        datefmt='%H:%M:%S',
        level=logging.INFO
    )

    logger = logging.getLogger("Main")

    logger.info('Starting...')

    server_list = fetch_server_list()
    server = [s for s in server_list if s['region'] == PREFERRED_SERVER][0]

    proxy = ProxyServer(server['host'])

    logger.info('Proxy initialized with target set as %s (Preferred region is set to "%s").',
        server['host'],
        PREFERRED_SERVER
    )

    conn_client_thread = threading.Thread(
        target=proxy.connect_client
    )
    conn_client_thread.daemon = True
    conn_client_thread.start()

    conn_server_thread = threading.Thread(
        target=proxy.connect_server
    )
    conn_server_thread.start()

    listen_thread = threading.Thread(
        target=proxy.listen
    )
    listen_thread.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        proxy.close()

if __name__ == '__main__':
    main()
