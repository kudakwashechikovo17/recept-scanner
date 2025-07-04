#!/bin/sh
# Simple helper script to install required packages
set -e

python -m pip install --upgrade pip
pip install -r requirements.txt
