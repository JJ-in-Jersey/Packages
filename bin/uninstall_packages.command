#!/bin/sh

python %HOME/PycharmProjects/Packages/bin/cleanup.py

pip3 cache purge

pip freeze > /tmp/freeze
pip uninstall -r /tmp/freeze -y