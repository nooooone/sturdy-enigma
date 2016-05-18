"""This test suite ensures we can start our server, send it some requests, and
get sane responses back. It is not intended for in-depth testing; see the tests
in the unit directory for that."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from functools import partial
from multiprocessing import Process
from socket import socket
from time import sleep
import unittest

import indexer

HOST = '127.0.0.1'
PORT = 8080
WARM = 4 # seconds to wait for server to start
FAIL = b'FAIL\n'
OK = b'OK\n'
ERROR = b'ERROR\n'

def request(sock, line):
    """Given a socket, sends the given line bytestring and blocks waiting for a
    response."""
    sock.send(line)
    return sock.recv(1024)

@contextmanager
def test_server():
    """Context manager for cleanly starting/stopping a test server. Yields a
    partial'ed request function with the socket argument set."""
    try:
        p = Process(target=indexer.main)
        sock = socket()
        p.start()
        print('Sleeping {} seconds to let test server start...'.format(WARM))
        sleep(WARM)
        print('Connecting socket...')
        sock.connect((HOST, PORT))
        yield partial(request, sock)
    finally:
        print('Killing test server and closing socket')
        p.terminate()
        sock.close()

class TestServer(unittest.TestCase):
    def test_can_send_good_stuff(self):
        with test_server() as req:

            script = [
                (b'QUERY|coffee|\n', FAIL),
                (b'QUERY|tea|\n', FAIL),
                (b'QUERY|vim|\n', FAIL),
                (b'INDEX|coffee|\n', OK),
                (b'INDEX|tea|\n', OK),
                (b'INDEX|vim|coffee,tea\n', OK),
                (b'QUERY|vim|\n', OK),
                (b'QUERY|coffee|\n', OK),
                (b'QUERY|tea|\n', OK),
                (b'REMOVE|vim|\n', OK),
                (b'REMOVE|coffee|\n', OK),
                (b'REMOVE|tea|\n', OK),
                (b'QUERY|coffee|\n', FAIL),
                (b'QUERY|tea|\n', FAIL),
                (b'QUERY|vim|\n', FAIL),
            ]

            for line, response in script:
                self.assertEqual(req(line), response)

    def test_can_send_bad_stuff(self):
        with test_server() as req:
            script = [
                (b'QEURY|coffee|\n', ERROR),
                (b'INDEX|coffee|blah blah\n', ERROR),
                (b'QUERY|tea|', ERROR),
                (b'REMOVE|vim vi improved|\n', ERROR),
                (b'INDEX|emacs:yeah|\n', ERROR),
            ]

            for line, response in script:
                self.assertEqual(req(line), response)

    def test_concurrency_ok(self):
        script0 = [
            (b'QUERY|coffee|\n', FAIL),
            (b'QUERY|tea|\n', FAIL),
            (b'QUERY|vim|\n', FAIL),
            (b'INDEX|coffee|\n', OK),
            (b'INDEX|tea|\n', OK),
            (b'INDEX|vim|coffee,tea\n', OK),
            (b'QUERY|vim|\n', OK),
            (b'QUERY|coffee|\n', OK),
            (b'QUERY|tea|\n', OK),
            (b'REMOVE|vim|\n', OK),
            (b'REMOVE|coffee|\n', OK),
            (b'REMOVE|tea|\n', OK),
            (b'QUERY|coffee|\n', FAIL),
            (b'QUERY|tea|\n', FAIL),
            (b'QUERY|vim|\n', FAIL),
        ]
        script1 = [
            (b'QUERY|yerba|\n', FAIL),
            (b'QUERY|chicory|\n', FAIL),
            (b'QUERY|emacs|\n', FAIL),
            (b'INDEX|yerba|\n', OK),
            (b'INDEX|chicory|\n', OK),
            (b'INDEX|emacs|yerba,chicory\n', OK),
            (b'QUERY|emacs|\n', OK),
            (b'QUERY|yerba|\n', OK),
            (b'QUERY|chicory|\n', OK),
            (b'REMOVE|emacs|\n', OK),
            (b'REMOVE|yerba|\n', OK),
            (b'REMOVE|chicory|\n', OK),
            (b'QUERY|yerba|\n', FAIL),
            (b'QUERY|chicory|\n', FAIL),
            (b'QUERY|emacs|\n', FAIL),
        ]
        script2 = [
            (b'QUERY|spiced_wine|\n', FAIL),
            (b'QUERY|tisane|\n', FAIL),
            (b'QUERY|nano|\n', FAIL),
            (b'INDEX|spiced_wine|\n', OK),
            (b'INDEX|tisane|\n', OK),
            (b'INDEX|nano|spiced_wine,tisane\n', OK),
            (b'QUERY|nano|\n', OK),
            (b'QUERY|spiced_wine|\n', OK),
            (b'QUERY|tisane|\n', OK),
            (b'REMOVE|nano|\n', OK),
            (b'REMOVE|spiced_wine|\n', OK),
            (b'REMOVE|tisane|\n', OK),
            (b'QUERY|spiced_wine|\n', FAIL),
            (b'QUERY|tisane|\n', FAIL),
            (b'QUERY|nano|\n', FAIL),
        ]

        def run_script(req, script):
            results = []
            for line, response in script:
                results.append((req(line), response))
            return results

        with test_server() as req0:
            try:
                sock1 = socket()
                sock1.connect((HOST, PORT))
                req1 = partial(request, sock1)
                sock2 = socket()
                sock2.connect((HOST, PORT))
                req2 = partial(request, sock2)

                with ThreadPoolExecutor(max_workers=3) as executor:
                    future0 = executor.submit(run_script, req0, script0)
                    future1 = executor.submit(run_script, req1, script1)
                    future2 = executor.submit(run_script, req2, script2)

                    for future in [future0, future1, future2]:
                        for got, expected in future.result():
                            self.assertEqual(got, expected)
            finally:
                sock1.close()
                sock2.close()
