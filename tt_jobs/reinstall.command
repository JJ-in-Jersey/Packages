#!/bin/sh

python3 $HOME/PycharmProjects/Packages/bin/cleanup.py

pip3 cache purge

cd $HOME/PycharmProjects/Packages

pip3 install ./tt_jobs

python3 $HOME/PycharmProjects/Packages/bin/cleanup.py