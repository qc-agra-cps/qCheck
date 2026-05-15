#!/usr/bin/env bash
#
# This file is part of the qCheck tool.
#
# Developed for the Deutsches Forschungszentrum für Künstliche
# Intelligenz GmbH (DFKI), Cyber-Physical Systems Dept.
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version
# 3 of the License, or, at your option, any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program. If not, see
# <https://www.gnu.org/licenses/>.
#
# -------------------------------------------------------------------------
# File:    setup.sh
# Brief:   Automated dependency installation script for qCheck.
#
# Details:
# This script initializes the qCheck development environment by:
#
#   1. Installing required system dependencies.
#   2. Creating a Python virtual environment.
#   3. Installing Python dependencies.
#   4. Downloading and initializing external solver submodules.
#   5. Building and installing pyPicoSAT and pyLingeling.
#
# The script is intended for Ubuntu/Debian-based systems.
#
# Author:  Abhoy Kole
# Updated: 07.05.2026
# -------------------------------------------------------------------------
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXTERN_DIR="$ROOT_DIR/extern"

mkdir -p "$EXTERN_DIR"

echo "Installing system dependency: swig"
sudo apt-get update
sudo apt-get install -y swig

echo "Setting up virtual environment"
cd "$ROOT_DIR"
if [ ! -f "venv/bin/activate" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "Installing Python build tools"
pip install --upgrade pip setuptools wheel

echo "Installing Python dependency: natsort"
pip install natsort

echo "Adding pyPicoSAT submodule"
if [ ! -d "$EXTERN_DIR/pyPicoSAT" ]; then
    git submodule add https://github.com/pysmt/pyPicoSAT.git extern/pyPicoSAT
fi

echo "Adding pyLingeling submodule"
if [ ! -d "$EXTERN_DIR/pyLingeling" ]; then
    git submodule add https://github.com/pramodsu/pyLingeling.git extern/pyLingeling
fi

echo "Initializing submodules"
git submodule update --init --recursive

echo "Building and installing pyPicoSAT"
cd "$EXTERN_DIR/pyPicoSAT"
./build.sh picosat-965
python setup.py install

echo "Building and installing pyLingeling"
cd "$EXTERN_DIR/pyLingeling"
./build.sh
python setup.py build
python setup.py install
cd "$ROOT_DIR"
echo "Done."