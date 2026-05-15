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
# File:    run_multiplier_benchmarks.sh
# Brief:   Run qCheck multiplier equivalence-checking experiments.
#
# Details:
# This script executes equivalence-checking experiments for multiplier
# benchmark circuits of increasing bit-widths.
#
# For each multiplier size:
#
#   1. The benchmark implementation:
#        - s1_mul_<N>_<N>.bench
#
#      is compared against:
#        - s2_mul_<N>_<N>.bench
#
#   2. A miter circuit is generated automatically.
#
#   3. DIMACS or qDIMACS encodings are produced.
#
# Usage:
#   ./scripts/run_multiplier_benchmarks.sh [dimacs|qdimacs]
#
# Example:
#   ./scripts/run_multiplier_benchmarks.sh dimacs
#   ./scripts/run_multiplier_benchmarks.sh qdimacs
#
# Author:  Abhoy Kole
# Updated: 07.05.2026
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

if [[ "$CNF_FORMAT" != "dimacs" && "$CNF_FORMAT" != "qdimacs" ]]; then
    echo "[ERROR] Invalid CNF format: '$CNF_FORMAT'"
    echo ""
    echo "Usage:"
    echo "  $0 [dimacs|qdimacs]"
    exit 1
fi

# ---------------------------------------------------------
# Benchmark configuration
# ---------------------------------------------------------
START=4
END=12

# ---------------------------------------------------------
# Experiment banner
# ---------------------------------------------------------
echo "=================================================="
echo "      qCheck Multiplier Benchmark Suite"
echo "=================================================="
echo " CNF format : $CNF_FORMAT"
echo " Mode       : miter"
echo " Bit range  : ${START} -> ${END}"
echo "=================================================="
echo ""

# ---------------------------------------------------------
# Run experiments
# ---------------------------------------------------------
for (( c=START; c<=END; c++ )); do

    BENCH_A="$ROOT_DIR/input/mul-bench/s1_mul_${c}_${c}.bench"
    BENCH_B="$ROOT_DIR/input/mul-bench/s2_mul_${c}_${c}.bench"

    echo "--------------------------------------------------"
    echo " Running ${c}-bit multiplier experiment"
    echo "--------------------------------------------------"
    echo " Benchmark A : s1_mul_${c}_${c}.bench"
    echo " Benchmark B : s2_mul_${c}_${c}.bench"
    echo ""

    python3 "$ROOT_DIR/src/cnf.py" \
        --cnf_format="$CNF_FORMAT" \
        --mode=miter \
        "$BENCH_A" \
        "$BENCH_B"

    echo ""
    echo "[DONE] ${c}-bit multiplier experiment completed."
    echo ""
done

# ---------------------------------------------------------
# Completion message
# ---------------------------------------------------------
echo "=================================================="
echo " All multiplier benchmark experiments completed."
echo "=================================================="