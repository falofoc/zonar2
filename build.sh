#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create an empty file to indicate build is complete
touch /tmp/build_complete 