# qCheck

qCheck is a tool for generating:

- classical CNF formulas in DIMACS format,
- quantum-compatible qCNF/eCNF formulas in qDIMACS format,

for Boolean circuits represented in BENCH format.

The framework supports:
- single-circuit CNF generation,
- miter-based equivalence checking,
- ESOP-based quantum clause encoding for qSAT workflows.

---

# Research Reference

If you use qCheck in academic work, please cite:

```bibtex
@article{kole2025qsat,
  title={qSAT: Design of an Efficient Quantum Satisfiability Solver for Hardware Equivalence Checking},
  author={Kole, Abhoy and Djeridane, Mohammed E. and Weingarten, Lennart  and Datta, Kamalika and Drechsler, Rolf},
  journal={ACM Journal on Emerging Technologies in Computing Systems},
  year={2025},
  doi={10.1145/3729229}
}
```

Paper:  
https://dl.acm.org/doi/10.1145/3729229

---

# Features

- Classical CNF generation (DIMACS)
- Quantum-compatible qCNF/eCNF generation (qDIMACS)
- Miter construction for equivalence checking
- BENCH parser and writer
- Lingeling SAT integration
- ESOP-based quantum-compatible encoding

Supported gate types:
- AND
- OR
- NOT
- BUF
- XOR
- XNOR
- NAND
- NOR
- MUX
- MAJ

---

# Repository Structure

```text
qCheck/
├── src/
│   ├── cnf.py
│   ├── ckt.py
│   ├── adapter.py
│   └── readbench.py
├── scripts/
│   └── setup.sh
├── extern/
├── input/
│   └── demo/
├── output/
└── README.md
```

---

# Installation

## Clone Repository

```bash
git clone --recurse-submodules https://gitlab.informatik.uni-bremen.de/quantum-computing/qcheck.git
cd qCheck
```

If the repository was already cloned without submodules:

```bash
git submodule update --init --recursive
```

---

## Install Dependencies

qCheck provides an automated installation script.

Run:

```bash
chmod +x scripts/setup_deps.sh
./scripts/setup_deps.sh
```

The script automatically:

- creates a Python virtual environment,
- installs Python build tools,
- installs `natsort`,
- installs `swig`,
- downloads and builds:
  - pyPicoSAT
  - pyLingeling

---

## Activate Virtual Environment

```bash
source venv/bin/activate
```

---

# Input Format

qCheck accepts circuits in BENCH format.

Example:

```bench
INPUT(A)
INPUT(B)
INPUT(Cin)

OUTPUT(Sum)
OUTPUT(Cout)

AxorB = XOR(A, B)
Sum = XOR(AxorB, Cin)

AandB = AND(A, B)
AxorBandCin = AND(AxorB, Cin)

Cout = OR(AandB, AxorBandCin)
```

---

# qDIMACS Conventions

qCNF/qDIMACS files use the following ESOP notation:

| Symbol | Meaning |
|---|---|
| `@` | XOR separator |
| `!` | Constant logic-1 |

---

# Usage

---

# Single-Circuit CNF Generation

The option:

```bash
--mode=no_miter
```

generates CNF/qCNF files independently for every output of a single circuit.

---

## Classical CNF (DIMACS)

```bash
python3 src/cnf.py \
    --cnf_format=dimacs \
    --mode=no_miter \
    input/demo/fulladder.bench
```

Generated files:

```text
output/fulladder/
├── fulladder_Sum.dimacs
└── fulladder_Cout.dimacs
```

---

## Quantum-Compatible qCNF (qDIMACS)

```bash
python3 src/cnf.py \
    --cnf_format=qdimacs \
    --mode=no_miter \
    input/demo/fulladder.bench
```

Generated files:

```text
output/fulladder/
├── fulladder_Sum.qdimacs
└── fulladder_Cout.qdimacs
```

---

# Miter-Based Equivalence Checking

By default, qCheck constructs a miter circuit between two BENCH circuits and generates a CNF/qCNF encoding for equivalence checking.

---

## Classical CNF Miter

```bash
python3 src/cnf.py \
    --cnf_format=dimacs \
    --mode=miter \
    input/demo/test_nor.bench \
    input/demo/test_or.bench
```

---

## Quantum-Compatible qCNF Miter

```bash
python3 src/cnf.py \
    --cnf_format=qdimacs \
    --mode=miter \
    input/demo/test_nor.bench \
    input/demo/test_or.bench
```

Generated file:

```text
output/
└── test_nor__test_or_miter.(q)dimacs
```

---

# Output Format

---

## DIMACS CNF

The classical CNF output follows the standard DIMACS CNF format:

```text
p cnf <num_variables> <num_clauses>
```

---

## qDIMACS/qCNF

The quantum-compatible encoding uses an ESOP-style clause representation.

Example:

```text
! @ 5 @ 1 2 0
```

where:
- `!` represents logic constant `1`,
- `@` separates XOR terms.

---

# Notes

- The tool internally builds AST-based circuit representations.
- qCNF encodings are optimized for quantum circuit synthesis workflows.
- Buffer-cleaning passes are automatically applied to generated miters.
- Lingeling is used for classical SAT-based equivalence checking.

---

# Requirements

- Python 3.8+
- SWIG
- natsort
- pyPicoSAT
- pyLingeling

All dependencies are automatically installed through:

```bash
./scripts/setup_deps.sh
```

---

# License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

See the `LICENSE` file for the full license text.

---

# Authors

- Abhoy Kole
- Mohammed Elkacem Djeridane

Developed at:

Deutsches Forschungszentrum für Künstliche Intelligenz (DFKI)  
Cyber-Physical Systems Department

---
