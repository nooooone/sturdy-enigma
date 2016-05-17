import re
from socketserver import ThreadingTCPServer, BaseRequestHandler
from threading import Thread
from typing import List, Tuple, ByteString

# TODO should use a queue for destructive operations

COMMANDS = ['INDEX', 'REMOVE', 'QUERY']
PKGNAME_RE = re.compile(r'^[a-z]+$')
DEPLIST_RE = re.compile(r'^([a-z],?)+$')

class CommandParsingError(Exception): pass

class Package:
    """Represents a package. The only data enumerated in the challenge
    description are package name and its dependencies, so that's all that is
    tracked here."""
    __slots__ = ['dependencies', 'name']

    def __init__(self,
                 name: str,
                 dependencies: List['Package']) -> None:
        self.name = name
        self.dependencies = dependencies

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return "{}|{}".format(self.name, ','.join(map(str, self.dependencies)))

    def __str__(self) -> str:
        return self.name

# TODO i might not need this; this is just for global state tracking. Will
# either contain some kind of package lookup or cache structure, if anything.
class Data: pass

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

def depends(pkg0: Package,
            pkg1: Package) -> bool:
    """Given two packages, returns whether or not pkg0 depends no pkg1"""
    return False

def index(data: Data,
          pkg0: Package,
          deps: List[Package]) -> Result:
    return ERROR

def remove(data: Data,
           pkg0: Package) -> Result:
    return ERROR

def query(data: Data,
          pkg0: Package) -> Result:
    return ERROR


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
        print("Incoming client connection, starting poll on socket")
        # TODO less tight loop. I tried both select and poll but couldn't get behavior I wanted.
        while True:
            try:
                command = self.request.recv(1024)
                (command, pkg_name, deps) = parse_command(command)
                # TODO if mutable, acquire a lock (on what?)
                # TODO don't need to always encode this
                self.request.send(OK.bytes)
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
    server = IndexerServer((HOST, PORT), IndexerRequestHandler)
    server_thread = Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    server_thread.join()

if __name__ == '__main__':
    main()
