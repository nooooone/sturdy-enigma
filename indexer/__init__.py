from collections import namedtuple
from functools import lru_cache
import re
from socketserver import ThreadingTCPServer, BaseRequestHandler
import threading
from threading import Thread, Lock
from typing import List, Tuple, ByteString, Dict

# Type aliases
IndexStore = Dict
Result = ByteString
State = namedtuple('State', ['index_store', 'lock'])

# Constants
COMMANDS = ['INDEX', 'REMOVE', 'QUERY']
PKGNAME_RE = re.compile(r'^[a-z0-9-_+A-Z]+$')
DEPLIST_RE = re.compile(r'^([a-z0-9-_+A-Z],?)+$')
ERROR = b'ERROR\n'
FAIL = b'FAIL\n'
OK = b'OK\n'

class CommandParsingError(Exception): pass

class Package:
    """Represents a package. Maintains a list of both children (packages that
    depend on this one) and dependencies (packages that this one depends on) as
    well as the package's name.
    """
    __slots__ = ['dependencies', 'name', 'children']

    def __init__(self,
                 name: str,
                 dependencies: List[str]) -> None:
        self.name = name
        self.dependencies = dependencies
        self.children = []

    def __repr__(self) -> str:
        return "<Package {}, depending on {}>".format(
            self.name, ','.join(map(str, self.dependencies))
        )

    def __str__(self) -> str:
        return self.name

def index(state: State, pkg_name: str, deps: List[str]) -> Result:
    """Returns OK if the package was found or successfully indexed; FAIL
    otherwise.
    """
    with state.lock:
        store = state.index_store
        pkg = store.get(pkg_name)

        if pkg is not None:
            return OK

        dep_pkgs = list(map(lambda d: store.get(d), deps))
        if not all(dep_pkgs):
            return FAIL
        else:
            store[pkg_name] = Package(pkg_name, deps)
            for dep_pkg in dep_pkgs:
                dep_pkg.children += [pkg_name]
            return OK

def remove(state: State, pkg_name: str) -> Result:
    """Returns OK if package was not found or was successfully removed; FAIL
    otherwise.
    """
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

def query(state: State, pkg_name: str) -> Result:
    """Returns OK if the package was found, FAIL otherwise.
    """
    with state.lock:
        return OK if state.index_store.get(pkg_name) else FAIL

@lru_cache(maxsize=128)
def parse_command(raw_command: ByteString) -> Tuple[str, str, List[str]]:
    """Given a byte string read from a socket, validates that the sent command
    is properly formed and returns a tuple of the command's components
    (command, package name, depdency list).
    """
    if not raw_command.endswith(b'\n'):
        raise CommandParsingError()

    parts = raw_command.decode().strip().split('|')
    if len(parts) != 3:
        raise CommandParsingError()

    command, pkg_name, deplist_string = parts

    if command not in COMMANDS:
        raise CommandParsingError()

    if re.match(PKGNAME_RE, pkg_name) is None:
        raise CommandParsingError()

    deps = []
    if len(deplist_string) > 0 and command == 'INDEX':
        if re.match(DEPLIST_RE, deplist_string) is None:
            raise CommandParsingError()
        deps = list(filter(lambda s: len(s) > 0, deplist_string.split(',')))

    return (command, pkg_name, deps)

def dispatch(state: State, raw_command: ByteString) -> Result:
    """Given a reference to our shared thread state and a raw command, this function:
        * validates the command
        * parses the command
        * runs the associated command function
        * returns a suitable Result bytestring
    """
    try:
        (command, pkg_name, deps) = parse_command(raw_command)

        if command == 'QUERY':
            return query(state, pkg_name)

        if command == 'REMOVE':
            return remove(state, pkg_name)

        if command == 'INDEX':
            return index(state, pkg_name, deps)

        raise RuntimeError()

    except CommandParsingError:
        return ERROR

class IndexerRequestHandler(BaseRequestHandler):
    def handle(self) -> None:
        """This request handler starts a loop for listening for incoming
        commands. For each command, it attempts to parse it (sending ERROR if
        that fails) and execute it. It stops looping when it can no longer read
        from its associated socket.
        """
        while True:
            raw_command = self.request.recv(1024)
            if not raw_command:
                break
            result = dispatch(self.state, raw_command)
            self.request.send(result)

def main():
    """Entry point for this module. Starts up the TCP server and sets up the
    shared thread state in an immutable data structure (a named tuple).
    """
    HOST, PORT = ('0.0.0.0', 8080)
    print("Running at {}:{}".format(HOST, PORT))

    IndexerRequestHandler.state = State({}, Lock())

    ThreadingTCPServer.allow_reuse_address = True
    ThreadingTCPServer.request_queue_size = 128

    server = ThreadingTCPServer((HOST, PORT), IndexerRequestHandler)
    server_thread = Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    server_thread.join()
