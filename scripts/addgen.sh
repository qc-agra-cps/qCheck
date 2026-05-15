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
# File:    run_adder_experiments.sh
# Brief:   Run qCheck adder equivalence-checking experiments.
#
# Details:
# This script executes qCheck on carry-lookahead and ripple-carry
# adder benchmark circuits for multiple bit-widths.
#
# The script:
#   1. Ensures the Python virtual environment is activated.
#   2. Runs miter-based equivalence checking.
#   3. Generates DIMACS or qDIMACS encodings.
#
# Usage:
#   ./scripts/run_adder_experiments.sh [dimacs|qdimacs]
#
# Example:
#   ./scripts/run_adder_experiments.sh dimacs
#   ./scripts/run_adder_experiments.sh qdimacs
#
# Author:  Abhoy Kole
# Updated: 10.12.2025
# -------------------------------------------------------------------------

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ---------------------------------------------------------
# Activate virtual environment if not already activated
# ---------------------------------------------------------
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "[INFO] Activating Python virtual environment..."

    if [[ ! -f "$ROOT_DIR/venv/bin/activate" ]]; then
        echo "[ERROR] Virtual environment not found."
        echo "Please run:"
        echo "  ./scripts/setup.sh"
        exit 1
    fi

    # shellcheck disable=SC1091
    source "$ROOT_DIR/venv/bin/activate"
else
    echo "[INFO] Virtual environment already active."
fi

# ---------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------
CNF_FORMAT="${1:-qdimacs}"
SIZES=(4 8 16 32)

if [[ "$CNF_FORMAT" != "dimacs" && "$CNF_FORMAT" != "qdimacs" ]]; then
    echo "[ERROR] Invalid CNF format: '$CNF_FORMAT'"
    echo ""
    echo "Usage:"
    echo "  $0 [dimacs|qdimacs]"
    exit 1
fi

# ---------------------------------------------------------
# Experiment banner
# ---------------------------------------------------------
echo "=================================================="
echo "         qCheck Adder Benchmark Suite"
echo "=================================================="
echo " CNF format : $CNF_FORMAT"
echo " Mode       : miter"
echo " Sizes      : ${SIZES[*]}"
echo "=================================================="
echo ""

# ---------------------------------------------------------
# Run experiments
# ---------------------------------------------------------
for c in "${SIZES[@]}"; do

    BENCH_A="$ROOT_DIR/input/add-bench/cl_${c}.bench"
    BENCH_B="$ROOT_DIR/input/add-bench/rc_${c}.bench"

    echo "--------------------------------------------------"
    echo " Running ${c}-bit adder equivalence experiment"
    echo "--------------------------------------------------"
    echo " Benchmark A : cl_${c}.bench"
    echo " Benchmark B : rc_${c}.bench"
    echo ""

    python3 "$ROOT_DIR/src/cnf.py" \
        --cnf_format="$CNF_FORMAT" \
        --mode=miter \
        "$BENCH_A" \
        "$BENCH_B"

    echo ""
    echo "[DONE] ${c}-bit experiment completed."
    echo ""
done

# ---------------------------------------------------------
# Completion message
# ---------------------------------------------------------
echo "=================================================="
echo " All qCheck experiments completed successfully."
echo "=================================================="