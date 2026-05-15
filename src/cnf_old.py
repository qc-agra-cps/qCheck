# -*- coding: utf-8 -*-
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
# @file    cnf.py
# @brief   Command-line frontend for BENCH-to-CNF/qCNF conversion.
#
# @details
# This module provides the command-line interface for converting BENCH
# circuits into classical DIMACS CNF or quantum-compatible qDIMACS/qCNF
# files. It supports both single-circuit output encoding and miter-based
# equivalence-checking encoding between two BENCH circuits.
#
# The script:
#   - reads BENCH files using readbench,
#   - builds circuit miters using ckt,
#   - translates circuits through adapter into CNF or qCNF,
#   - removes redundant buffer clauses introduced by copied miter inputs,
#   - writes the resulting formula in DIMACS or qDIMACS format,
#   - optionally checks classical equivalence using the Lingeling solver.
#
# qDIMACS-specific notation:
#   - 0   is printed as '@' and is used as the ESOP separator,
#   - 0.1 is printed as '!' and is used as the constant-one ESOP marker.
#
# Reference:
#   A. Kole, M. E. Djeridane, L. Weingarten, K. Datta, and R. Drechsler,
#   "qSAT: Design of an Efficient Quantum Satisfiability Solver for
#   Hardware Equivalence Checking," ACM Journal on Emerging Technologies
#   in Computing Systems, 2025.
#   DOI: 10.1145/3729229
#
# @date    07.11.2023
# @version 1.1
# @author  Mohammed Elkacem Djeridane
#
# -------------------------------------------------------------------------
import os
import sys
import ckt
import argparse
import readbench
import adapter
from lingeling import Solver


def to_dimacs(cnf, filename, inputs_1=None, miter_literal_map=None, qdimacs=False):
    if miter_literal_map is None:
        miter_literal_map = {}
    if inputs_1 is None:
        inputs_1 = []
    for output in cnf:
        num_literals = max([max([abs(l) for l in clause]) for clause in output])
        with open(filename, "w") as f:
            if qdimacs:
                f.write("p qcnf %d %d\n" % (num_literals, len(output)))
            else:
                f.write("p cnf %d %d\n" % (num_literals, len(output)))
            for i in inputs_1:
                f.write("c %s -> %d\n" % (i.name, miter_literal_map[i]))
            for clause in output:
                for literal in clause:
                    if literal == 0:
                        f.write("@ ")
                    elif literal == 0.1:
                        f.write("! ")
                    else:
                        f.write("%d " % literal)
                f.write("0\n")


def check_eq(miter_cnf, miter_output, miter_literal_map, S):
    for cl in miter_cnf:
        S.addClause(*cl)
    # we don't need to add the miter output to the cnf now but a redundant clause doesn't hurt
    r = S.solve(miter_literal_map[miter_output])

    if r == 1:
        print("miter is SAT, circuits are not equivalent")
    elif r == 0:
        print("miter is UNSAT, circuits are equivalent")


def clean_cnf_buffer_clauses(miter_qcnf, miter_literal_map, inputs_1, inputs_2):
    def has_matching_literal(clause, lit_set):
        for lit in clause:
            if abs(lit) in lit_set:
                return True
        return False

    inp_1_lit = [miter_literal_map[i] for i in inputs_1]
    inp_2_lit = [miter_literal_map[i] for i in inputs_2]

    # find buffer clauses in the miter
    buffer_clauses = []
    for clause in miter_qcnf:
        if len(clause) == 2:
            if has_matching_literal(clause, inp_1_lit) and has_matching_literal(clause, inp_2_lit):
                inp1, inp2 = clause
                for c in miter_qcnf:
                    while inp2 in c or -inp2 in c:
                        if abs(inp2) in c:
                            c[c.index(abs(inp2))] = abs(inp1)
                        if -abs(inp2) in c:
                            c[c.index(-abs(inp2))] = -abs(inp1)

    # remove clauses of size 2 if they have the same literal i.e. they were buffer clauses before replacement
    miter_qcnf[:] = [c for c in miter_qcnf if len(c) > 2 or abs(c[0]) != abs(c[1])]


def clean_qcnf_buffer_clauses(miter_qcnf, miter_literal_map, inputs_1, inputs_2):
    def has_matching_literal(clause, lit_set):
        for lit in clause:
            if abs(lit) in lit_set:
                return True
        return False

    inp_1_lit = [miter_literal_map[i] for i in inputs_1]
    inp_2_lit = [miter_literal_map[i] for i in inputs_2]

    # find buffer clauses in the miter
    buffer_clauses = []
    for clause in miter_qcnf:
        if len(clause) == 4:
            if has_matching_literal(clause, inp_1_lit) and has_matching_literal(clause, inp_2_lit):
                not_used, not_used, inp1, inp2 = clause
                for c in miter_qcnf:
                    while inp1 in c or -inp1 in c:
                        if abs(inp1) in c:
                            c[c.index(abs(inp1))] = abs(inp2)
                        if -abs(inp1) in c:
                            c[c.index(-abs(inp1))] = -abs(inp2)

    # remove clauses of size 2 if they have the same literal i.e. they were buffer clauses before replacement
    miter_qcnf[:] = [c for c in miter_qcnf if abs(c[2]) != abs(c[3])]


def main(argv):
    # Read arguments
    parser = argparse.ArgumentParser(description='bench to cnf')
    parser.add_argument('--mode', choices=['no_miter', 'miter'], default='miter', help='Choose mode (default: miter)')
    parser.add_argument('--cnf_format', choices=['dimacs', 'qdimacs'], default='qdimacs', help='Choose either qdimacs or '
                                                                                            'dimacs (default: qdimacs)')
    parser.add_argument('--miter_or_output', choices=['True', 'False'], default='True',
                        help='Choose either miter or output (default: miter)')
    parser.add_argument('bench_1', type=str, help='Bench file to analyze')
    parser.add_argument('bench_2', nargs='?', type=str, help='Second bench file to analyze (only for miter mode)')

    args = parser.parse_args()
    if len(argv) == 1:
        parser.print_help()
        exit(1)
    if args.bench_1 is None:
        assert args.mode == 'no_miter', "miter option is selected & second bench is not specified"

    if args.miter_or_output == 'False':
        print("miter without or option is not implemented yet")
        return 0

    # Create output directory
    out_dir = "./output/"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Read first bench file
    inputs_1, outputs_1, node_map_1 = readbench.readBenchFile(args.bench_1)

    if args.mode == 'miter':
        # Read second bench file
        inputs_2, outputs_2, node_map_2 = readbench.readBenchFile(args.bench_2, "_copy", miter=True)

        # Make miter
        if args.miter_or_output:
            miter = ckt.Miter(inputs_1, node_map_1, outputs_1, inputs_2, node_map_2, outputs_2)
        elif not args.miter_or_output:
            miter = ckt.Miter_without_or(inputs_1, node_map_1, outputs_1, inputs_2, node_map_2, outputs_2)
        # Preparing Solver
        S = Solver()
        miter_literal_map = {}

        # Preparing output file
        name_a = os.path.splitext(args.bench_1)[0].split("/")[-1]
        name_b = os.path.splitext(args.bench_2)[0].split("/")[-1]

        if args.cnf_format == 'dimacs':
            # Generate CNF for the miter
            miter_cnf = [adapter.circuitToCNF(miter.miter_output, miter_literal_map, lambda n: S.newVar())]
            # Clean buffer clauses
            clean_cnf_buffer_clauses(miter_cnf[0], miter_literal_map, inputs_1, inputs_2)
            # Adding the miter output to the cnf
            miter_cnf[0].append([miter_literal_map[miter.miter_output]])
            # Outputting the DIMACS file
            out_path_cnf = out_dir + name_a + "__" + name_b + "_miter.dimacs"
            to_dimacs(miter_cnf, out_path_cnf, inputs_1, miter_literal_map, qdimacs=False)
            print("dimacs for the miter is written ")
            # Check equivalence
            check_eq(miter_cnf[0], miter.miter_output, miter_literal_map, S)

        elif args.cnf_format == 'qdimacs':
            # Generate qCNF for the miter
            miter_qcnf = [adapter.circuitToqCNF(miter.miter_output, miter_literal_map, lambda n: S.newVar())]
            # Clean buffer clauses
            clean_qcnf_buffer_clauses(miter_qcnf[0], miter_literal_map, inputs_1, inputs_2)
            # Adding the miter output to the qcnf
            miter_qcnf[0].append([miter_literal_map[miter.miter_output]])
            # Outputting the qDIMACS file
            out_path_qcnf = out_dir + name_a + "__" + name_b + "_miter.qdimacs"
            to_dimacs(miter_qcnf, out_path_qcnf, inputs_1, miter_literal_map, qdimacs=True)
            print("qdimacs for the miter is written")

        # Print mapping
        print("")
        print("node to literal map:")
        for i in inputs_1:
            print("%s : %d" % (i.name, miter_literal_map[i]))
        print("miter output literal:")
        print("%s : %d" % (miter.miter_output.name, miter_literal_map[miter.miter_output]))
    else:
        # Preparing Solver
        S = Solver()
        node_to_literal_map = {}
        # Preparing output file
        name_a = os.path.splitext(args.bench_1)[0].split("/")[-1]
        if not os.path.exists(out_dir + name_a):
            os.makedirs(out_dir + name_a)

        if args.qdimacs == 'dimacs':
            # Generate CNF for each output
            cnf = []
            for o in outputs_1:
                # Get CNF/qCNF of each output
                cnf.append(adapter.circuitToCNF(o, node_to_literal_map, lambda n: S.newVar()))
                # Adding the output to the cnf
                cnf[-1].append([node_to_literal_map[o]])
                # Outputting the DIMACS file
                to_dimacs(cnf, out_dir + name_a + "/" + name_a + "_" + o.name + ".dimacs", inputs_1,
                          node_to_literal_map, qdimacs=False)
                print("dimacs for the output %s is written " % o.name)

        elif args.qdimacs == 'qdimacs':
            # Generate qCNF for each output
            qcnf = []
            for o in outputs_1:
                # Get CNF/qCNF of each output
                qcnf.append(adapter.circuitToqCNF(o, node_to_literal_map, lambda n: S.newVar()))
                # Adding the output to the qcnf
                qcnf[-1].append([node_to_literal_map[o]])
                # Outputting the qDIMACS file
                to_dimacs(qcnf, out_dir + name_a + "/" + name_a + "_" + o.name + ".qdimacs", inputs_1,
                          node_to_literal_map,
                          qdimacs=True)
                print("qdimacs for the output %s is written " % o.name)

        # print the mapping
        print("")
        print("node to literal map:")
        for i in inputs_1:
            print("%s : %d" % (i.name, node_to_literal_map[i]))
        for o in outputs_1:
            print("%s : %d" % (o.name, node_to_literal_map[o]))


if __name__ == '__main__':
    main(sys.argv)
