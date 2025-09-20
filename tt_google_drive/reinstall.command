#!/bin/sh

python3 $HOME/PycharmProjects/Packages/bin/cleanup.py

pip3 cache purge

cd $HOME/PycharmProjects/Packages

pip3 uninstall tt_google_drive -y
pip3 install ./tt_google_drive

python3 $HOME/PycharmProjects/Packages/bin/cleanup.py
