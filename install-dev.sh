#!/bin/bash
# Development installation script for local IDE use

set -e

echo "Installing mojo-shared in development mode..."
cd mojo-shared
pip install -e ".[dev]"
cd ..

echo "Installing mojo_api in development mode..."
cd mojo_api
pip install -e ".[dev]"
cd ..

echo "Development installation complete!"
echo "Both packages are now installed in editable mode for IDE support."