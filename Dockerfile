FROM ubuntu:16.04
MAINTAINER nooooone <hj9lt@slipry.net>
EXPOSE 8080
RUN apt-get update && apt-get -y install git python3 python3-setuptools
RUN git clone https://github.com/nooooone/sturdy-enigma
# must be in python project dir, otherwise setuptools walks entire filesystem
RUN cd sturdy-enigma && python3 setup.py install
CMD indexer
