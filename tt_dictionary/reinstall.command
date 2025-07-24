#!/bin/sh

python3 $HOME/PycharmProjects/Packages/bin/cleanup.py

pip3 cache purge

cd $HOME/PycharmProjects/Packages

pip3 uninstall tt_dictionary -y
pip3 install ./tt_dictionary

python3 $HOME/PycharmProjects/Packages/bin/cleanup.py
