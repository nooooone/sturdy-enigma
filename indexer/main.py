class Package:
    """Represents a package. The only data enumerated in the challenge
    description are package name and its dependencies, so that's all that is
    tracked here."""
    __slots__ = ['dependencies', 'name']

    def __init__(self,
                 name: str,
                 dependencies: List[Package]) -> None:
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
    __slots__ = ['code']

    def __init__(self, code: str) -> None:
        if code not in ['fail', 'ok', 'error']:
            raise Exception("Bad argument to Result, got: '{}'".format(code))

        self.code = code

    def __repr__(self) -> str:
        return self.code

    def __str__(self) -> str:
        return self.code.upper()

error = Result('error')
fail = Result('fail')
ok = Result('ok')

def depends(pkg0: Package,
            pkg1: Package) -> bool:
    """Given two packages, returns whether or not pkg0 depends no pkg1"""
    return False

def index(data: Data,
          pkg0: Package,
          deps: List[Package]) -> Result:
    return error

def remove(data: Data,
           pkg0: Package) -> Result:
    return error

def query(data: Data,
          pkg0: Package) -> Result:
    return error

if __name__ == '__main__':
    print('runnin')
