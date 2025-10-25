#!/bin/sh

python3 $HOME/PycharmProjects/Packages/bin/cleanup.py

pip3 cache purge

cd $HOME/PycharmProjects/Packages

pip3 uninstall tt_date_time_tools -y
pip3 install ./tt_date_time_tools

python3 $HOME/PycharmProjects/Packages/bin/cleanup.py
