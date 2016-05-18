# Package Indexer Challenge

# Project Layout

    .
    |-- Dockerfile # Uses ubuntu image to install and run this code
    |-- indexer
    |   |-- __init__.py # The implementation
    |-- README.md # This file
    |-- run_tests.sh # Test runner
    |-- setup.py # Helper for installing this into a venv
    |-- tests  # Test suite
        |-- integration.py
        |-- unit
            |-- cmd_parse.py
            |-- commands.py
            |-- dispatch.py
## Requirements

Python 3.5.1 **or** Docker

## Installation (Docker)

Build the provided Dockerfile. It uses the Ubuntu 16.04 image and exposes port 8080.

## Installation (local)

From the root of the project:

    python3 -mvenv /tmp/indexervenv
    source /tmp/indexervenv/bin/activate
    python setup.py install


## Running (Docker)

Using the image id created from `docker build`,

    docker run -p 127.0.0.1:8080:8080 <image id>

## Running (local)

Assuming your venv is active, just run `indexer`.

## Running the tests

Do a local install and activate its venv, then run `./run_tests.sh` from the root of the
project.

There is a small integration test suite (tests/integration.py) that exercises
sending good and bad data to the server. It also tests concurrent client
support.

There is a set of unit tests (tests/unit/*.py) that exercise command parsing,
command dispatching, and datastore manipulation.

## Design

### Language

My two most familiar languages at this point are Python and Clojure. I feel
like either is fine for this task. There is an inherent performance increase
with Clojure but I would argue that both language's concurrency mechanisms are
up to task. Further, it's much harder to stick to "built in" Clojure code since
almost everything in Clojure requires at least contrib libraries if not third
party libraries.

### Datastore

I use an in memory datastore for two reasons: 1) I wanted to error on the side
of the "only my code" requirement and thus not use a DB connection library and
2) I can control the performance characteristics and reason about them which is
important for this code challenge.

I use a hash table to map package names to Packge objects which contain lists
of their dependencies and children. When a package is added or removed, I
update the children lists for any of its dependencies.

While not the most sophisticated of data structures, it is suitably fast and
compact. Further, it could be easily persisted to disk using Python's pickle
library.

### Concurrency Architecture

Since there is a hard requirement of data consistency here, I couldn't really
see a way to divide this this task up computationally. However, being able to
handle multiple concurrent connections is necessary, so I opted for threads. I
think they are ideal here since I have shared data (the index data structure)
and they can block in parallel getting data as needed. 

I start a thread for each socket connection that lives until the client
disconnects. Each of these threads polls the socket, processing any commands
that come in. I use a lock whenever a command is being run that reads or writes
the index's datastore.

To make it obvious to readers of the code what data is shared among threads, I
create an immutable data structure (Python's namedtuple) that is explicitly
passed to the functions that interact with the datastore.

### Network Architecture

I use Python's built in TCPServer; specifically, the threaded variety. It
handles opening threads for each client connection for me and closing them as
necessary.

### Performance characteristics

The provided test harness takes about 9.5 seconds to run on my machine. The
next step for optimizing this would be reducing the time spent per
datastore-accessing function by dropping down to Python's optimized ctypes.
Such an optimization felt excessive for this assignment.

I don't see an easy way to adapt this for multiple cores without moving to a
database backend like Postgresql since as long as the index is stored in memory
we have the requirement of shared state between concurrent units of execution.
