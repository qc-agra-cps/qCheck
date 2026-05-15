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
# @file    ckt.py
# @brief   Abstract syntax tree representation for Boolean circuits.
#
# @details
# This module defines the AST node hierarchy used by qCheck to represent
# Boolean circuits. It provides node classes for constants, inputs, and
# logic gates such as AND, OR, NOT, BUF, XOR, XNOR, NAND, NOR, MUX, and MAJ.
#
# The module also provides helper constructors, simplification routines,
# support and transitive fanin cone computation, level computation, and
# miter construction for equivalence checking.
#
# This representation is used as the circuit front-end for CNF and
# quantum-compatible ESOP/qCNF encodings in the qCheck/qSAT flow.
#
# Reference:
#   A. Kole, M. E. Djeridane, L. Weingarten, K. Datta, and R. Drechsler,
#   "qSAT: Design of an Efficient Quantum Satisfiability Solver for
#   Hardware Equivalence Checking," ACM Journal on Emerging Technologies
#   in Computing Systems, 2025.
#   DOI: 10.1145/3729229
#
# @date    23.10.2023
# @version 1.1
# @author  Mohammed Elkacem Djeridane
#
# -------------------------------------------------------------------------
# Modification History
#
# 30.01.2025 Abhoy Kole
#   - Added majority-gate support through ASTNode.MAJ_GATE.
#   - Added "MAJ" entry to ASTNode.NAMES.
#   - Added ASTNode.is_maj_gate() helper method.
#   - Added MajGate class with construction, cloning, string conversion,
#     and constant-propagation simplification.
#   - Added maj(a, b, c) helper constructor.
#   - Renamed/updated MUX type-check helper from is_mux() to is_mux_gate()
#     for consistency with the other gate predicates.
#   - Extended XOR and XNOR gates from strictly two-input gates to
#     multi-input gates.
#   - Updated XOR/XNOR string conversion for multi-input display.
#   - Updated XOR/XNOR simplification to handle multiple fanins and
#     constant propagation across all constant inputs.
#
# -------------------------------------------------------------------------
name_counter = 1
class ASTNode(object):
    CONST0      = 0
    CONST1      = 1
    INPUT       = 2
    AND_GATE    = 3
    NOT_GATE    = 4
    BUF_GATE    = 5
    OR_GATE     = 6
    XOR_GATE    = 7
    XNOR_GATE   = 8
    NAND_GATE   = 9
    NOR_GATE    = 10
    MUX_GATE    = 11
    MAJ_GATE    = 12

    NAMES = [
        "GND",
        "VDD",
        "INPUT",
        "AND",
        "NOT",
        "BUF",
        "OR",
        "XOR",
        "XNOR",
        "NAND",
        "NOR",
        "MUX",
        "MAJ"
    ]



    # Constructor.
    def __init__(self, t):
        "Construct an abstract ASTNode. Should never be called directly."
        self.node_type = t
        self.fanins = ()
        global name_counter
        self.name = "__n%d" % name_counter
        name_counter += 1
        self.value = None
        self.hash_code = None

    # Matching functions for node types.
    def is_const0(self):
        "Is this a constant 0?"
        return self.node_type == ASTNode.CONST0
    def is_const1(self):
        "Is this a constant 1?"
        return self.node_type == ASTNode.CONST1
    def is_const(self):
        "Is this any type of constant?"
        return self.is_const0() or self.is_const1()
    def is_input(self):
        "Is this an input node?"
        return self.node_type == ASTNode.INPUT
    def is_and_gate(self):
        "Is this an and gate?"
        return self.node_type == ASTNode.AND_GATE
    def is_not_gate(self):
        "Is this a not gate?"
        return self.node_type == ASTNode.NOT_GATE
    def is_buf_gate(self):
        "Is this a buffer? (output = input)?"
        return self.node_type == ASTNode.BUF_GATE
    def is_or_gate(self):
        "Is this an or gate?"
        return self.node_type == ASTNode.OR_GATE
    def is_xor_gate(self):
        "Is this an eXclusive or gate?"
        return self.node_type == ASTNode.XOR_GATE
    def is_xnor_gate(self):
        "Is this an eXclusive nor gate?"
        return self.node_type == ASTNode.XNOR_GATE
    def is_nand_gate(self):
        "Is this a nand gate?"
        return self.node_type == ASTNode.NAND_GATE
    def is_nor_gate(self):
        "Is this a nor gate?"
        return self.node_type == ASTNode.NOR_GATE
    def is_mux_gate(self):
        "Is this a mux?"
        return self.node_type == ASTNode.MUX_GATE
    def is_maj_gate(self):
        "Is this a maj gate?"
        return self.node_type == ASTNode.MAJ_GATE

    # Operator overloading.
    def __and__(self, other):
        "Overload a & b"
        return AndGate(self, other)
    def __or__(self, other):
        "Overload a | b"
        return OrGate(self, other)
    def __invert__(self):
        "Overload ~a"
        return NotGate(self)
    def __xor__(self, other):
        "Overload a ^ b"
        return XorGate(self, other)
    def __ne__(self, other):
        "Overload a != b. Just delegates to __eq__ in subclasses."
        return not self.__eq__(other)
    def __eq__(self, other):
        "Is this node equal to 'other'?"
        if hash(self) == hash(other):
            return other.node_type == self.node_type and self.fanins == other.fanins
        else:
            return False
    def __hash__(self):
        "Hashcode for this node."
        if self.hash_code is None:
            f_hashes = tuple(hash(fi) for fi in self.fanins)
            self.hash_code = hash((self.node_type, f_hashes))
        return self.hash_code
    def __repr__(self):
        "repr just defaults to str."
        return str(self)

    # Utility methods.
    def simplify(self):
        "Simplifier: does constant propagation."
        memo = {}
        return self._simplify(memo)

    def _simplify(self, memo):
        "Simplifier memoized implementation."
        if self not in memo:
            faninsP = [fi._simplify(memo) for fi in self.fanins]
            gP = self._simplifyGate(faninsP)
            memo[self] = gP
        return memo[self]

    def _simplifyGate(self, fanins):
        return self.clone(fanins)

    def support(self):
        stack = [self]
        support = set() # Track list of support nodes.
        visited = set() # Track visited nodes.
        # This is pretty standard DFS.
        while len(stack) > 0:
            n = stack.pop()
            if n in visited: continue
            visited.add(n)
            # Add to support?
            if n.is_input(): support.add(n)
            # Visit child nodes.
            for f in n.fanins: stack.append(f)
        return support

    def transitiveFaninCone(self):
        "Find the transitive fanin cone for this node."
        stack = [self]
        visited = set()
        # This is pretty standard DFS.
        while len(stack) > 0:
            n = stack.pop()
            if n in visited: continue
            visited.add(n)
            for f in n.fanins: stack.append(f)
        return visited

    def transitiveFaninConeTuples(self):
        "Find the transitive fanin cone for this node."
        stack = [(self.name, self)]
        visited = set()
        # This is pretty standard DFS.
        while len(stack) > 0:
            (name, n) = stack.pop()
            if (name, n) in visited: continue
            visited.add((name, n))
            for f in n.fanins:
                stack.append((f.name, f))
        return visited

    def size(self):
        "The size of this circuit."
        return len(self.transitiveFaninCone())

    def __len__(self):
        "The size of this circuit."
        return len(self.transitiveFaninCone())

    def subst(self, rewrites):
        "Substitute according to the map 'rewrite'."
        memo = {}
        return self._subst(rewrites, memo)

    def _subst(self, rewrites, memo):
        "Substitute according to the map 'rewrite' with memoization."
        if self in memo:
            return memo[self]
        if self in rewrites:
            result = rewrites[self]
        else:
            fanins = tuple(fi._subst(rewrites, memo) for fi in self.fanins)
            result = self.clone(fanins)
        memo[self] = result
        assert isinstance(result, ASTNode)
        return result

class Const0Node(ASTNode):
    def __init__(self):
        "Construct a constant 0 node."
        ASTNode.__init__(self, ASTNode.CONST0)
        self.value = 0
    def __str__(self):
        "Return a string representation of this node."
        return '0'
    def clone(self, fanins):
        "Create a clone of this node."
        return Const0Node()

class Const1Node(ASTNode):
    def __init__(self):
        "Construct a constant 1 node."
        ASTNode.__init__(self, ASTNode.CONST1)
        self.value = 1
    def __str__(self):
        "Return a string representation of this node."
        return '1'
    def clone(self, fanins):
        "Create a clone of this node."
        return Const1Node()

class InputNode(ASTNode):
    def __init__(self, name):
        "Construct an input node."
        ASTNode.__init__(self, ASTNode.INPUT)
        self.name = name
    def __str__(self):
        "Return a string representation of this node."
        return self.name
    def clone(self, fanins):
        "Create a clone of this node."
        return InputNode(self.name)
    def __hash__(self):
        "Hashcode for this node."
        if self.hash_code is None:
            self.hash_code = hash((self.node_type, self.name))
        return self.hash_code
    def __eq__(self, other):
        "Is this node equal to 'other'?"
        return other.node_type == self.node_type and other.name == self.name
    def is_keyinput(self):
        "Does this name of this input start with the lower case string 'keyinput'?"
        return self.name.startswith('keyinput')

class AndGate(ASTNode):
    def __init__(self, *fanins):
        "Construct an and gate."
        ASTNode.__init__(self, ASTNode.AND_GATE)
        assert len(fanins) >= 2
        self.fanins = tuple(fanins[:])
    def __str__(self):
        "Return a string representation of this node."
        return '(%s)' % (' & '.join('%s' % str(gi) for gi in self.fanins))
    def clone(self, fanins):
        "Create a clone of this node."
        return AndGate(*fanins)
    def _simplifyGate(self, fanins):
        fanins0 = [f for f in fanins if f.is_const0()]
        faninsP = [f for f in fanins if not f.is_const1()]
        if len(fanins0) > 0: return Const0Node()
        elif len(faninsP) == 0: return Const1Node()
        elif len(faninsP) == 1: return faninsP[0]
        else: return AndGate(*faninsP)

class NotGate(ASTNode):
    def __init__(self, *fanins):
        "Construct a not gate."
        ASTNode.__init__(self, ASTNode.NOT_GATE)
        assert len(fanins) == 1
        self.fanins = tuple(fanins[:])
    def __str__(self):
        "Return a string representation of this node."
        #TODO: for some reason buf and not gates both used '~' symbol, so I changed not to '!', keep an eye out for this

        return '!(%s)' % str(self.fanins[0])
    def clone(self, fanins):
        "Create a clone of this node."
        return NotGate(*fanins)
    def _simplifyGate(self, fanins):
        assert len(fanins) == 1
        f0 = fanins[0]
        if f0.is_const0(): return Const1Node()
        elif f0.is_const1(): return Const0Node()
        else: return NotGate(f0)

class BufGate(ASTNode):
    def __init__(self, *fanins):
        "Construct a not gate."
        ASTNode.__init__(self, ASTNode.BUF_GATE)
        assert len(fanins) == 1
        self.fanins = tuple(fanins[:])
    def __str__(self):
        "Return a string representation of this node."
        return '~(%s)' % str(self.fanins[0])
    def clone(self, fanins):
        "Create a clone of this node."
        return BufGate(*fanins)
    def _simplifyGate(self, fanins):
        assert len(fanins) == 1
        f0 = fanins[0]
        if f0.is_const0(): return Const0Node()
        elif f0.is_const1(): return Const1Node()
        else: return BufGate(f0)

class OrGate(ASTNode):
    def __init__(self, *fanins):
        "Construct an or gate."
        ASTNode.__init__(self, ASTNode.OR_GATE)
        #print(fanins)
        assert len(fanins) >= 2 # TODO: why is this here?
        self.fanins = fanins[:]
    def __str__(self):
        "Return a string representation of this node."
        return '(%s)' % (' | '.join('%s' % str(gi) for gi in self.fanins))
    def clone(self, fanins):
        "Create a clone of this node."
        return OrGate(*fanins)
    def _simplifyGate(self, fanins):
        fanins1 = [f for f in fanins if f.is_const1()]
        faninsP = [f for f in fanins if not f.is_const0()]
        if len(fanins1) > 0: return Const1Node()
        elif len(faninsP) == 0: return Const0Node()
        elif len(faninsP) == 1: return faninsP[0]
        else: return OrGate(*faninsP)


class XorGate(ASTNode):
    def __init__(self, *fanins):
        "Construct an eXclusive or gate."
        ASTNode.__init__(self, ASTNode.XOR_GATE)
        # assert len(fanins) == 2 # Removed
        assert len(fanins) >= 2 # Added
        #self.fanins = tuple(fanins[:]) # Removed
        self.fanins = fanins[:] # Added
    def __str__(self):
        "Return a string representation of this node."
        #s0 = str(self.fanins[0]) # Removed
        #s1 = str(self.fanins[1]) # Removed
        #return '(%s ^ %s)' % (s0, s1) # Removed
        return '(%s)' % (' ^ '.join('%s' % str(gi) for gi in self.fanins))
    def clone(self, fanins):
        "Create a clone of this node."
        return XorGate(*fanins)
    def _simplifyGate(self, fanins):
        #assert len(fanins) == 2 # Removed
        #f0 = fanins[0] # Removed
        #f1 = fanins[1] # Removed
        fanins1 = [f for f in fanins if f.is_const()]
        faninsP = [f for f in fanins if not f.is_const()]
        ''' #Removed
        if f0.is_const() and f1.is_const():
            r = f0.value ^ f1.value
            if r == 0: return Const0Node()
            elif r == 1: return Const1Node()
            else: assert False
        elif f0.is_const():
            if f0.value == 0: return f1
            elif f0.value == 1: return NotGate(f1)
            else: assert False
        elif f1.is_const():
            if f1.value == 0: return f0
            elif f1.value == 1: return NotGate(f0)
            else: assert False
        else:
            return XorGate(f0, f1) '''
        if len(fanins1) > 0:
            r = 0
            for f in fanins1:
                r = r ^ f.value
            if r == 0: 
                if len(faninsP) == 0: return Const0Node()
                elif len(faninsP) == 1: return faninsP[0]
                else: return XorGate(*faninsP)
            elif r== 1: 
                if len(faninsP) == 0: return Const1Node()
                elif len(faninsP) == 1: return NotGate(faninsP[0])
                else: return XnorGate(*faninsP)
            else: assert False
        else: return XorGate(*faninsP)


class XnorGate(ASTNode):
    def __init__(self, *fanins):
        "Construct an eXclusive nor gate."
        ASTNode.__init__(self, ASTNode.XNOR_GATE)
        # assert len(fanins) == 2 # Removed
        assert len(fanins) >= 2 # Added
        #self.fanins = tuple(fanins[:]) # Removed
        self.fanins = fanins[:] # Added
    def __str__(self):
        fanin_str = ', '.join(str(fi) for fi in self.fanins)
        return "xnor(%s)" % (fanin_str)
    def clone(self, fanins):
        "Create a clone of this node."
        return XnorGate(*fanins)
    def _simplifyGate(self, fanins):
        #assert len(fanins) == 2 # Removed
        #f0 = fanins[0] # Removed
        #f1 = fanins[1] # Removed
        fanins1 = [f for f in fanins if f.is_const()]
        faninsP = [f for f in fanins if not f.is_const()]
        ''' #Removed
        if f0.is_const() and f1.is_const():
            r = not (f0.value ^ f1.value)
            if r == 0: return Const0Node()
            elif r == 1: return Const1Node()
            else: assert False
        elif f0.is_const():
            if f0.value == 1: return f1
            elif f0.value == 0: return NotGate(f1)
            else: assert False
        elif f1.is_const():
            if f1.value == 1: return f0
            elif f1.value == 0: return NotGate(f0)
            else: assert False
        else:
            return XnorGate(f0, f1) '''
        if len(fanins1) > 0:
            r = 0
            for f in fanins1:
                r = r ^ f.value
            if r == 0: 
                if len(faninsP) == 0: return Const1Node()
                elif len(faninsP) == 1: return NotGate(faninsP[0])
                else: return XnorGate(*faninsP)
            elif r== 1: 
                if len(faninsP) == 0: return Const0Node()
                elif len(faninsP) == 1: return faninsP[0]
                else: return XorGate(*faninsP)
            else: assert False
        else: return XnorGate(*faninsP)
        

class NandGate(ASTNode):
    def __init__(self, *fanins):
        "Construct a nand gate."
        ASTNode.__init__(self, ASTNode.NAND_GATE)
        assert len(fanins) >= 2
        self.fanins = tuple(fanins[:])
    def __str__(self):
        fanin_str = ', '.join(str(fi) for fi in self.fanins)
        return "nand(%s)" % (fanin_str)
    def clone(self, fanins):
        "Create a clone of this node."
        return NandGate(*fanins)
    def _simplifyGate(self, fanins):
        fanins0 = [f for f in fanins if f.is_const0()]
        faninsP = [f for f in fanins if not f.is_const1()]
        if len(fanins0) > 0: return Const1Node()
        elif len(faninsP) == 0: return Const0Node()
        elif len(faninsP) == 1: return NotGate(faninsP[0])
        else: return NandGate(*faninsP)


class NorGate(ASTNode):
    def __init__(self, *fanins):
        "Construct a nor gate."
        ASTNode.__init__(self, ASTNode.NOR_GATE)
        assert len(fanins) >= 2
        self.fanins = tuple(fanins[:])
    def __str__(self):
        fanin_str = ', '.join(str(fi) for fi in self.fanins)
        return "nor(%s)" % (fanin_str)
    def clone(self, fanins):
        "Create a clone of this node."
        return NorGate(*fanins)
    def _simplifyGate(self, fanins):
        fanins1 = [f for f in fanins if f.is_const1()]
        faninsP = [f for f in fanins if not f.is_const0()]
        if len(fanins1) > 0: return Const0Node()
        elif len(faninsP) == 0: return Const1Node()
        elif len(faninsP) == 1: return NotGate(faninsP[0])
        else: return NorGate(*faninsP)

class MuxGate(ASTNode):
    def __init__(self, *fanins):
        "Construct a multiplexer."
        ASTNode.__init__(self, ASTNode.MUX_GATE)
        assert len(fanins) == 3
        self.fanins = tuple(fanins[:])
    def __str__(self):
        fanin_str = ', '.join(str(fi) for fi in self.fanins)
        return "mux(%s)" % (fanin_str)
    def clone(self, fanins):
        "Create a clone of this node."
        return MuxGate(*fanins)
    def _simplifyGate(self, fanins):
        "Simplify mux."
        [s, a, b]  = [f for f in fanins]
        if s.is_const1():
            return b
        elif s.is_const0():
            return a
        elif a.is_const0():
            return AndGate(s, b)._simplifyGate([s, b])
        else:
            return MuxGate(s, a, b)

class MajGate(ASTNode):
    def __init__(self, *fanins):
        "Construct a majority gate."
        ASTNode.__init__(self, ASTNode.MAJ_GATE)
        assert len(fanins) == 3
        self.fanins = tuple(fanins[:])
    def __str__(self):
        fanin_str = ', '.join(str(fi) for fi in self.fanins)
        return "maj(%s)" % (fanin_str)
    def clone(self, fanins):
        "Create a clone of this node."
        return MajGate(*fanins)
    def _simplifyGate(self, fanins):
        "Simplify mux."
        [a, b, c]  = [f for f in fanins]
        if a.is_const1():
            return OrGate(b, c)._simplifyGate([b, c])
        elif a.is_const0():
            return AndGate(b, c)._simplifyGate([b, c])
        elif b.is_const1():
            return OrGate(a, c)._simplifyGate([a, c])
        elif b.is_const0():
            return AndGate(a, c)._simplifyGate([a, c])
        elif c.is_const1():
            return OrGate(a, b)._simplifyGate([a, b])
        elif c.is_const0():
            return AndGate(a, b)._simplifyGate([a, b])
        else:
            return MajGate(a, b, c)

def notEqual(n1, n2):
    return XorGate(n1, n2)

def xnor(n1, n2):
    return XnorGate(n1, n2)

def equal(n1, n2):
    return xnor(n1, n2)

def nand(*ns):
    return NandGate(*ns)

def nor(*ns):
    return NorGate(*ns)

def mux(s, a, b):
    return MuxGate(s, a, b)

def maj(a, b, c):
    return MajGate(a, b, c)

def computeLevels(gates):
    for g in gates:
        g.level = 0

    while True:
        changed = False
        for g in gates:
            if len(g.fanins):
                levelP = max(fi.level for fi in g.fanins) + 1
            else:
                levelP = g.level
            if g.level != levelP:
                changed = True
                assert g.level < levelP
                g.level = levelP
        if not changed: break


class Miter:
    def __init__(self, inputs_1, node_map_1, outputs_1, inputs_2, node_map_2, outputs_2):

        miter_outputs = []
        self.miter_output = None
        assert len(outputs_1) == len(outputs_2), "Outputs of the two circuits are not equal"
        assert len(inputs_1) == len(inputs_2), "Inputs of the two circuits are not equal"

        miter_outputs = [(o1 ^ o2) for (o1, o2) in zip(outputs_1, outputs_2)]

        if len(miter_outputs) > 1:
            self.miter_output = OrGate(*miter_outputs)
        else:
            assert len(miter_outputs) == 1
            self.miter_output = miter_outputs[0]


class Miter_without_or:
    def __init__(self, inputs_1, node_map_1, outputs_1, inputs_2, node_map_2, outputs_2, or_outputs = True):

        self.miter_outputs = []
        assert len(outputs_1) == len(outputs_2), "Outputs of the two circuits are not equal"
        assert len(inputs_1) == len(inputs_2), "Inputs of the two circuits are not equal"

        self.miter_outputs = [(o1 ^ o2) for (o1, o2) in zip(outputs_1, outputs_2)]