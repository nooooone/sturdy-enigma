from collections import namedtuple
from functools import partial
import re
from socketserver import ThreadingTCPServer, BaseRequestHandler
import threading
from threading import Thread, Lock
from typing import List, Tuple, ByteString, Dict

COMMANDS = ['INDEX', 'REMOVE', 'QUERY']
PKGNAME_RE = re.compile(r'^[a-z0-9-_+A-Z]+$')
DEPLIST_RE = re.compile(r'^([a-z0-9-_+A-Z],?)+$')
IndexStore = Dict
State = namedtuple('State', ['index_store', 'lock'])

class CommandParsingError(Exception): pass

class Package:
    """Represents a package. The only data enumerated in the challenge
    description are package name and its dependencies, so that's all that is
    tracked here."""
    __slots__ = ['dependencies', 'name', 'children']

    def __init__(self,
                 name: str,
                 dependencies: List[str]) -> None:
        self.name = name
        self.dependencies = dependencies
        self.children = []

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return "{}|{}".format(self.name, ','.join(map(str, self.dependencies)))

    def __str__(self) -> str:
        return self.name

class Result:
    """Contains a response code as self.code; one of 'fail', 'ok', or 'error'.
    Uppercases the code before converting to a string so it can be passed back
    out over the network"""
    __slots__ = ['code', '_bs']

    def __init__(self, code: str) -> None:
        self._bs = None
        if code not in ['fail', 'ok', 'error']:
            raise Exception("Bad argument to Result, got: '{}'".format(code))

        self.code = code

    def __repr__(self) -> str:
        return self.code

    def __str__(self) -> str:
        return self.code.upper() + '\n'

    @property
    def bytes(self) -> ByteString:
        if self._bs is None:
            self._bs = str(self).encode('utf-8')
        return self._bs

ERROR = Result('error')
FAIL = Result('fail')
OK = Result('ok')

def index(state: State,
          pkg_name: str,
          deps: List[str]) -> Result:
    """For `INDEX` commands, the server returns `OK\n` if the package could be
    indexed or if it was already present. It returns `FAIL\n` if the package
    cannot be indexed because some of its dependencies aren't indexed yet and
    need to be installed first."""
    with state.lock:
        pkg = state.index_store.get(pkg_name)

        if pkg is not None:
            return OK

        dep_pkgs = map(lambda d: state.index_store.get(d), deps)
        if not all(dep_pkgs):
            return FAIL
        else:
            index_store[pkg_name] = Package(pkg_name, deps, [])
            for dep_pkg in dep_pkgs:
                dep_pkg.children.append(pkg)
            return OK

def remove(state: State,
           pkg_name: str) -> Result:
    """For `REMOVE` commands, the server returns `OK\n` if the package could be
    removed from the index. It returns `FAIL\n` if the package could not be
    removed from the index because some other indexed package depends on it. It
    returns `OK\n` if the package wasn't indexed."""
    with state.lock:
        pkg = state.index_store.get(pkg_name)
        if pkg is None:
            return OK

        if len(pkg.children) == 0:
            del state.index_store[pkg_name]
            for dep_name in pkg.dependencies:
                dep_pkg = state.index_store.get(dep_name)
                dep_pkg.children.remove(pkg.name)
            return OK
        else:
            return FAIL

def query(state: State,
          pkg_name: str) -> Result:
    """For `QUERY` commands, the server returns `OK\n` if the package is
    indexed. It returns `FAIL\n` if the package isn't indexed."""
    with state.lock:
        if state.index_store.get(pkg_name):
            return OK
        else:
            return FAIL

def parse_command(data: bytes) -> Tuple[str, str, List[str]]:
    if not data.endswith(b'\n'):
        raise CommandParsingError()

    parts = data.decode().strip().split('|')
    if len(parts) != 3:
        raise CommandParsingError()

    if parts[0] not in COMMANDS:
        raise CommandParsingError()

    if re.match(PKGNAME_RE, parts[1]) is None:
        raise CommandParsingError()

    deplist_string = parts[2]
    deps = []
    if len(deplist_string) > 0 and parts[0] == 'INDEX':
        if re.match(DEPLIST_RE, deplist_string) is None:
            raise CommandParsingError()
        deps = list(filter(lambda s: len(s) > 0, deplist_string.split(',')))

    return (parts[0], parts[1], deps)

class IndexerRequestHandler(BaseRequestHandler):
    def handle(self) -> None:
        cur_thread = threading.current_thread()
        print("Incoming client connection on ", cur_thread.name)
        # TODO less tight loop. I tried both select and poll but couldn't get behavior I wanted.
        while True:
            try:
                command = self.request.recv(1024)
                (command, pkg_name, deps) = parse_command(command)

                actions = {'QUERY': partial(query, pkg_name),
                           'REMOVE': partial(remove, pkg_name),
                           'INDEX': partial(index, pkg_name, deps)}

                self.request.send(actions[command]().bytes)
            except CommandParsingError as e:
                try:
                    print('GOT BROKEN MESSAGE ', command.decode())
                    self.request.send(ERROR.bytes)
                except BrokenPipeError as e:
                    print("Tried to report error to client, got broken pipe")
                    break
            except BrokenPipeError as e:
                print("Client connection closed")
                break
            except ConnectionResetError as e:
                print("Client connection closed")
                break
        print('Ceasing')

class IndexerServer(ThreadingTCPServer):
    request_queue_size = 128
    allow_reuse_address = True

def main():
    HOST, PORT = ('127.0.0.1', 8080)
    print("Running at {}:{}".format(HOST, PORT))

    index_store = {}
    lock = Lock()
    state = State(index_store, lock)
    IndexerRequestHandler.state = state

    server = IndexerServer((HOST, PORT), IndexerRequestHandler)
    server_thread = Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    server_thread.join()

if __name__ == '__main__':
    main()
