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
# @file    readbench.py
# @brief   BENCH parser and writer for qCheck Boolean circuits.
#
# @details
# This module reads BENCH-format circuit files and converts them into the
# qCheck circuit representation defined in ckt.py. It returns circuit
# inputs, outputs, and a node-name-to-AST-node map.
#
# The module also provides a BENCH writer that serializes qCheck AST
# circuits back into BENCH format while preserving topological order.
#
# Supported gate types include:
#   - AND, OR, NOT, BUF/BUFF
#   - XOR, XNOR
#   - NAND, NOR
#   - MUX/ITE
#   - MAJ
#
# In miter mode, copied circuit inputs are wrapped with buffer nodes and
# renamed using the provided suffix. This allows construction of equivalent
# but separately named circuit copies for equivalence checking.
#
# Reference:
#   A. Kole, M. E. Djeridane, L. Weingarten, K. Datta, and R. Drechsler,
#   "qSAT: Design of an Efficient Quantum Satisfiability Solver for
#   Hardware Equivalence Checking," ACM Journal on Emerging Technologies
#   in Computing Systems, 2025.
#   DOI: 10.1145/3729229
#
# @date    04.11.2023
# @version 1.1
# @author  Mohammed Elkacem Djeridane
#
# -------------------------------------------------------------------------
# Modification History
#
# 30.01.2025 Abhoy Kole
#   - Added BENCH parsing support for MUX gates.
#   - Added BENCH parsing support for ITE as an alias of MUX.
#   - Added BENCH parsing support for MAJ gates.
#   - Extended the parser to construct ckt.MuxGate for MUX/ITE nodes.
#   - Extended the parser to construct ckt.MajGate for MAJ nodes.
#   - Preserved existing parsing support for AND, OR, NOT, BUF/BUFF,
#     XOR, XNOR, NAND, and NOR gates.
#
# -------------------------------------------------------------------------
from __future__ import print_function

import ckt
import sys
from natsort import index_natsorted, natsorted

def readBenchFile(filename, suffix ='', miter = False):
    "Reads a bench file and returns the tuple (inps, outs, node_map)."
    with open(filename, 'rt') as fobj:
        return readFileObject(fobj, suffix, miter)

def readFileObject(fobj, suffix, miter):
    "Reads a bench file and returns the tuple (inps, outs, node_map)."
    fanins = {}
    node_map = {}
    output_names = []
    inputs = []
    for l in fobj.readlines():
        f = []
        l = l.strip()
        if len(l) == 0 or l.startswith('#'):
            continue
        if 'INPUT(' in l:
            name = l.replace("INPUT(", "").replace(")", "")
            if miter:
                node = ckt.BufGate(ckt.InputNode(name))
                name += suffix
            else:
                node = ckt.InputNode(name)
            node_map[name] = node
            inputs.append(node)
        elif 'OUTPUT(' in l:
            name = l.replace("OUTPUT(", "").replace(")", "") + suffix
            output_names.append(name)
        elif '=' in l:
            parts = [p.strip() for p in l.split('=')]
            assert len(parts) == 2
            gate_name = parts[0] + suffix
            rhs = parts[1]
            if rhs == 'VDD':
                node_map[gate_name] = ckt.Const1Node()
            else:
                gate_type = rhs[:rhs.find('(')]
                within_bracket = rhs[rhs.find('(')+1:rhs.find(')')]
                fanin_names = [p.strip()+suffix for p in within_bracket.split(',')]
                fanins = [node_map[fn] for fn in fanin_names]
                if gate_type == 'AND' or gate_type == 'and':
                    g = ckt.AndGate(*fanins)
                elif gate_type == 'OR' or gate_type == 'or':
                    g = ckt.OrGate(*fanins)
                elif gate_type == 'NOT' or gate_type == 'not':
                    g = ckt.NotGate(*fanins)
                elif gate_type == 'XOR' or gate_type == 'xor':
                    g = ckt.XorGate(*fanins)
                elif gate_type == 'XNOR' or gate_type == 'xnor':
                    g = ckt.XnorGate(*fanins)
                elif gate_type == 'NAND' or gate_type == 'nand':
                    g = ckt.NandGate(*fanins)
                elif gate_type == 'NOR' or gate_type == 'nor':
                    g = ckt.NorGate(*fanins)
                elif gate_type == 'BUF' or gate_type == 'BUFF' or gate_type == 'buf' or gate_type == 'buff':
                    g = ckt.BufGate(*fanins)
                elif gate_type == 'ITE' or gate_type == 'ite' or gate_type == 'MUX' or gate_type == 'mux':
                    g = ckt.MuxGate(*fanins)
                elif gate_type == 'MAJ' or gate_type == 'maj':
                    g = ckt.MajGate(*fanins)
                else:
                    assert False, gate_type
                node_map[gate_name] = g
                g.name = gate_name
        else:
            assert False, l
    outputs = []
    for out_name in output_names:
        output = node_map[out_name]
        output.name = out_name
        outputs.append(output)

    return inputs, outputs, node_map

def writeBench(f, inputs, outputs):
    counter = 1

    gates = { g.name: g for g in inputs + outputs }
    for out in outputs:
        tfc = out.transitiveFaninConeTuples()
        for (name, g) in tfc:
            if name in gates:
                assert gates[name] == g
            else:
                gates[name] = g

    level = {name: 0 for name in gates}
    changed = True
    while changed:
        changed = False
        for name in gates:
            g = gates[name]
            if g.is_input():
                new_level = 0
            else:
                new_level = max(level[fi.name] for fi in g.fanins) + 1

            if new_level > level[g.name]:
                level[g.name] = new_level
                changed = True

    gates = [gates[n] for n in gates]
    gates = natsorted(gates, key=lambda g: g.name)
    gates.sort(key=lambda g:level[g.name])
    for inp in inputs:
        print ('INPUT(%s)' % inp.name, file=f)
    for out in outputs:
        print ('OUTPUT(%s)' % out.name, file=f)
    for g in gates:
        if not g.is_input():
            gate_type = ckt.ASTNode.NAMES[g.node_type]
            input_string = ', '.join(fi.name for fi in g.fanins)
            line = '%s\t= %s(%s)' % (g.name, gate_type, input_string)
            print (line, file=f)

def main(argv):
    for arg in argv[1:]:
        inputs, outputs, node_map = readBenchFile(arg)
        max_fanins = max(len(node_map[n].fanins) for n in node_map)
        for n in node_map:
            node = node_map[n]
            if len(node.fanins) > 2:
                assert node.is_and_gate() or node.is_or_gate() or node.is_nand_gate() or node.is_nor_gate()

        print ('%-30s %5d' % (arg, max_fanins))

if __name__ == '__main__':
    main(sys.argv)
