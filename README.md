# Digital Ocean Indexer Challenge

## Requirements

Python 3.5.1

## Running

cd indexer
python3 main.py

## Design

* Language

My two most familiar languages at this point are Python and Clojure. I feel
like either is fine for this task. There is an inherent performance increase
with Clojure but I would argue that both language's concurrency mechanisms are
up to task.

* Datastore

I use an in memory datastore for two reasons: 1) I wanted to error on the side
of the "only my code" requirement and thus not use a DB connection library and
2) I can control the performance characteristics and reason about them which is
important for this code challenge..

* Concurrency Architecture

TODO

* Network Architecture

TODO

