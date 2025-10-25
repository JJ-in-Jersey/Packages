#!/bin/zsh

python3 $HOME/PycharmProjects/Packages/bin/cleanup.py

pip3 cache purge

pip3 freeze > /tmp/freeze
pip3 uninstall -r /tmp/freeze -y

python3 $HOME/PycharmProjects/Packages/bin/cleanup.py

pip3 list