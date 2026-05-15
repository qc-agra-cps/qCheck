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
# File:    run_functional_benchmarks.sh
# Brief:   Run qCheck functional benchmark equivalence experiments.
#
# Details:
# This script executes equivalence-checking experiments on a collection
# of functional benchmark circuits using qCheck.
#
# For each Boolean function benchmark:
#
#   1. The reference implementation (*_F.bench) is compared against:
#        - *_R1.bench
#        - *_R2.bench
#
#   2. A miter circuit is generated automatically.
#
#   3. DIMACS or qDIMACS CNF encodings are produced.
#
# Supported benchmark families:
#   - AND
#   - NAND
#   - OR
#   - NOR
#   - XOR
#   - XNOR
#   - MUX
#   - CARRY
#   - FA (Full Adder)
#
# Usage:
#   ./scripts/run_functional_benchmarks.sh [dimacs|qdimacs]
#
# Example:
#   ./scripts/run_functional_benchmarks.sh dimacs
#   ./scripts/run_functional_benchmarks.sh qdimacs
#
# Note:
# In DIMACS mode, the R2 versions of MUX, CARRY, and FA are skipped because
# they contain atomic MUX/MAJ-style gates whose classical CNF clauses are not
# currently defined. These cases can still be executed in qDIMACS mode.
#
# Author:  Abhoy Kole
# Updated: 04.02.2025
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
CNF_FORMAT="${1:-dimacs}"

if [[ "$CNF_FORMAT" != "dimacs" && "$CNF_FORMAT" != "qdimacs" ]]; then
    echo "[ERROR] Invalid CNF format: '$CNF_FORMAT'"
    echo ""
    echo "Usage:"
    echo "  $0 [dimacs|qdimacs]"
    exit 1
fi

# ---------------------------------------------------------
# Benchmark list
# ---------------------------------------------------------
FUNCTIONS=(
    "AND"
    "NAND"
    "OR"
    "NOR"
    "XOR"
    "XNOR"
    "MUX"
    "CARRY"
    "FA"
)

# ---------------------------------------------------------
# Experiment banner
# ---------------------------------------------------------
echo "=================================================="
echo "      qCheck Functional Benchmark Suite"
echo "=================================================="
echo " CNF format : $CNF_FORMAT"
echo " Mode       : miter"
echo " Functions  : ${FUNCTIONS[*]}"
echo "=================================================="
echo ""

# ---------------------------------------------------------
# Run experiments
# ---------------------------------------------------------
for f in "${FUNCTIONS[@]}"; do

    REF_BENCH="$ROOT_DIR/input/fun-bench/${f}_F.bench"
    REV1_BENCH="$ROOT_DIR/input/fun-bench/${f}_R1.bench"
    REV2_BENCH="$ROOT_DIR/input/fun-bench/${f}_R2.bench"

    echo "--------------------------------------------------"
    echo " Running benchmark family: $f"
    echo "--------------------------------------------------"
    echo ""

    echo "[CASE 1] ${f}_F vs ${f}_R1"
    python3 "$ROOT_DIR/src/cnf.py" \
        --cnf_format="$CNF_FORMAT" \
        --mode=miter \
        "$REF_BENCH" \
        "$REV1_BENCH"

    echo ""
    echo "[DONE] ${f}_R1 completed."
    echo ""

    # In DIMACS mode, skip R2 versions of MUX, CARRY, and FA.
    # These R2 benchmarks contain atomic MUX/MAJ-style gates whose
    # classical CNF clauses are not currently defined in the DIMACS encoder.
    if [[ "$CNF_FORMAT" == "dimacs" && \
          ( "$f" == "MUX" || "$f" == "CARRY" || "$f" == "FA" ) ]]; then
        echo "[SKIP] ${f}_F vs ${f}_R2"
        echo "       Reason: DIMACS encoding for atomic MUX/MAJ-style R2 gates is not defined."
        echo ""
        continue
    fi

    echo "[CASE 2] ${f}_F vs ${f}_R2"
    python3 "$ROOT_DIR/src/cnf.py" \
        --cnf_format="$CNF_FORMAT" \
        --mode=miter \
        "$REF_BENCH" \
        "$REV2_BENCH"

    echo ""
    echo "[DONE] ${f}_R2 completed."
    echo ""
done

# ---------------------------------------------------------
# Completion message
# ---------------------------------------------------------
echo "=================================================="
echo " All functional benchmark experiments completed."
echo "=================================================="