#!/bin/bash

if [ -z "$VIRTUAL_ENV" ]; then
     echo "\$VIRTUAL_ENV is unset, this is almost certainly not what you want."
     echo "Install this into a venv, and then re-run the script."
     echo "To install this, run the following from the root of the project:"
     echo "> python3 -mvenv /tmp/indexvenv"
     echo "> source /tmp/indexvenv/bin/activate"
     echo "> python setup.py install -e"
     exit 1
fi

cd tests
python -munittest unit/*.py integration.py
