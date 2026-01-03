#!/bin/bash
set -e

# Read Python version from .python-version
if [ -f ".python-version" ]; then
    PYTHON_VERSION=$(cat .python-version | tr -d '[:space:]')
    echo "Found Python version: $PYTHON_VERSION"
else
    echo "Error: .python-version file not found"
    exit 1
fi

# Install make and build tools
echo "Installing make and build tools..."
sudo apt-get update
sudo apt-get install -y make build-essential

# Install Python dependencies
echo "Installing Python build dependencies..."
sudo apt-get install -y \
    wget \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libreadline-dev \
    libsqlite3-dev \
    libgdbm-dev \
    libdb5.3-dev \
    libbz2-dev \
    libexpat1-dev \
    liblzma-dev \
    libffi-dev \
    tk-dev

# Download and build Python from official source
echo "Building Python $PYTHON_VERSION from source..."
cd /tmp
wget "https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz"
tar -xf "Python-$PYTHON_VERSION.tgz"
cd "Python-$PYTHON_VERSION"

./configure --enable-optimizations --prefix=/usr/local
make -j$(nproc)
sudo make altinstall

# Clean up
cd /tmp
sudo rm -rf "Python-$PYTHON_VERSION" "Python-$PYTHON_VERSION.tgz"

# Verify installations
echo "Verifying installations..."
make --version | head -n1
python${PYTHON_VERSION%.*} --version

echo "All installations completed successfully"
