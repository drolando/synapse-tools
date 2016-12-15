#!/bin/bash

echo "Installing synapse-tools package"
dpkg -i /work/dist/synapse-tools_*.deb

# Set -e here because the previous install should fail lacking dependencies
# and then we can fix it here
set -e
apt-get -y install -f

echo "Testing that pyyaml uses optimized cyaml parsers if present"
/opt/venvs/synapse-tools/bin/python -c 'import yaml; assert yaml.__with_libyaml__'

echo "Full integration test"
py.test /itest.py
