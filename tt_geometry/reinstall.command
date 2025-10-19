#!/bin/sh

python3 $HOME/PycharmProjects/Packages/bin/cleanup.py

pip3 cache purge

cd $HOME/PycharmProjects/Packages

pip3 uninstall tt_geometry -y
pip3 install ./tt_geometry

python3 $HOME/PycharmProjects/Packages/bin/cleanup.py
