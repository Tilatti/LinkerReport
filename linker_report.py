#! /usr/bin/env python3

import re
import subprocess
import sys
import os
import json

# 'Node' definitions for symbols (functions, constants, variables, ...) or
# symbole containers (archives, object files, ...)

class Node:
    def __init__(self, name, program_size, ro_data_size, data_size):
        self.name = name
        self.program_size = program_size
        self.ro_data_size = ro_data_size
        self.data_size = data_size
        self.type = "any"

    def __repr__(self):
        return "Node({0.name}, {0.program_size}, {0.ro_data_size}, {0.data_size})".format(self)
    def __hash__(self):
        return self.name.__hash__()
    def __eq__(self, other):
        return self.name == other.name
    def __neq__(self, other):
        return self.name != other.name

    @property
    def size(self):
        return self.program_size + self.ro_data_size + self.data_size

class FunctionNode(Node):
    def __init__(self, name, program_size):
        super().__init__(name, program_size, 0, 0)
        self.type = "function"

class ConstantNode(Node):
    def __init__(self, name, ro_data_size):
        super().__init__(name, 0, ro_data_size, 0)
        self.type = "constant"

class VariableNode(Node):
    def __init__(self, name, data_size):
        super().__init__(name, 0, 0, data_size)
        self.type = "variable"

class ContainerNode(Node):
    def __init__(self, name):
        super().__init__(name, 0, 0, 0)
        self.nodes = set()
        self.type = "any"

    def compute_sizes(self):
        self.program_size = 0
        self.ro_data_size = 0
        self.data_size = 0
        for n in self.nodes:
            if isinstance(n, ContainerNode):
                n.compute_sizes()
            self.program_size += n.program_size
            self.ro_data_size += n.ro_data_size
            self.data_size += n.data_size

    def add_sub_node(self, node):
        self.program_size += node.program_size
        self.ro_data_size += node.ro_data_size
        self.data_size += node.data_size
        self.nodes.add(node)

    def __iter__(self):
        yield from self.nodes

class ObjectNode(ContainerNode):
    def __init__(self, name):
        super().__init__(name)
        self.type = "object"

class ArchiveNode(ContainerNode):
    def __init__(self, name):
        super().__init__(name)
        self.type = "archive"

class ExecutableNode(ContainerNode):
    def __init__(self, name):
        super().__init__(name)
        self.type = "executable"

# Encoder definitions

class NodeEncoder:
    class Filter:
        def __call__(self, n):
            return True

    class NameFilter(Filter):
        def __init__(self, name):
            self.name = name
        def __call__(self, n):
            return re.fullmatch(self.name, n.name) is not None

    class LeafFilter(Filter):
        def __call__(self, n):
            return (not isinstance(n, ContainerNode))

    class LeafBiggerFilter(LeafFilter):
        def __init__(self, min_size):
            self.min_size = min_size
        def __call__(self, n):
            return (super().__call__(n) and (n.size > self.min_size))

    class LeafSmallerFilter(LeafFilter):
        def __init__(self, max_size):
            self.max_size = max_size
        def __call__(self, n):
            return (super().__call__(n) and (n.size < self.max_size))

    is_recursive = True
    recursion_level = 16
    is_human_readable = False
    filters = []

    @classmethod
    def apply_filters(cls, n):
        return all(map(lambda f: f(n), cls.filters))

    @staticmethod
    def sizeof_fmt(num, suffix='B'):
        import math
        def num_fmt(num, unit):
            if math.modf(num)[0] == 0.0:
                fmt = "%3.0f%sB"
            else:
                fmt = "%3.1f%sB"
            return fmt % (num, unit)
        for unit in ['','K','M','G','T','P','E','Z']:
            if abs(num) < 1024.0:
                return num_fmt(num, unit)
            num /= 1024.0
        return num_fmt(num, "Y")

    @classmethod
    def to_fmt_dict(cls, n):
        d = {"name": n.name, "type": n.type}
        if cls.is_human_readable:
            d["program_size"], d["ro_data_size"], d["data_size"] = \
                cls.sizeof_fmt(n.program_size), cls.sizeof_fmt(n.ro_data_size), cls.sizeof_fmt(n.data_size)
        else:
            d["program_size"], d["ro_data_size"], d["data_size"] = n.program_size, n.ro_data_size, n.data_size
        return d

class JsonNodeEncoder(json.JSONEncoder, NodeEncoder):
    def default(self, n):
        """Transform a Node instance to a serializable structure for json encoder."""
        if isinstance(n, ContainerNode):
            d = self.to_fmt_dict(n)
            if self.is_recursive and (self.recursion_level > 0):
                self.recursion_level = self.recursion_level - 1
                d["sub_nodes"] = []
                for sn in n.nodes:
                    sub_encoded = self.default(sn)
                    if sub_encoded is not None:
                        d["sub_nodes"].append(sub_encoded)
            return d
        elif isinstance(n, Node):
            if self.apply_filters(n):
                return self.to_fmt_dict(n)
            else:
                return None
        else:
            return json.JSONEncoder.default(self, o)

class WikiTableNodeEncoder(NodeEncoder):
    def dumps(self, node_list):
        def table_line(name, size1, size2, size3):
            return "|{}|{}|{}|{}|\n".format(name, size1, size2, size3)
        def rec(node_list):
            s = ""
            for n in node_list:
                if isinstance(n, ContainerNode):
                    d = self.to_fmt_dict(n)
                    s += table_line(n.name, d["program_size"], d["data_size"], d["ro_data_size"])
                    if self.is_recursive and (self.recursion_level > 0):
                        self.recursion_level = self.recursion_level - 1
                        s += rec(list(n.nodes))
                elif isinstance(n, Node):
                    if self.apply_filters(n):
                        d = self.to_fmt_dict(n)
                        s += table_line(n.name, d["program_size"], d["data_size"], d["ro_data_size"])
                else:
                    raise Exception("Unknown type to encode")
            return s
        s = "||Name||Program size||Data size||Read-only data size||\n"
        s += rec(node_list)
        return s

# Binary utilities output parsing functions

def parse_nm(filepath):
    """
    nm can be called to .o, .a or .elf.
    With .o and .elf it is simply a list of symbols, in this case the function parse_sym_line() would be enough.
    With .a, there is for each .o a list of symbols.
    """

    def parse_sym_line(l):
        fields = l.strip(" \t\n").split(" ")
        if len(fields) != 4:
            return None
        size = int(fields[1], 16)
        stype = fields[2]
        name = fields[3]
        if stype in ["T", "t"]: # Text code section (.text)
            return FunctionNode(name, size)
        elif stype in ["D", "d"]: # Initialized data section (.data)
            return VariableNode(name, size)
        elif stype in ["B", "b"]: # Unintialized data section (.bss)
            return VariableNode(name, size)
        elif stype in ["R", "r"]: # Read only data section (.rodata)
            return ConstantNode(name, size)
        else:
            return None # Unknown symbol type

    with subprocess.Popen(["nm", "-S", filepath], stdout=subprocess.PIPE) as p:
        object_node = None
        for l in [str(le, 'utf-8') for le in p.stdout.readlines()]:
            if l == "\n": # End of an object file
                if object_node is not None:
                    yield object_node
                object_node = None
            else:
                match = re.search("([_A-Za-z0-9]+.o):", l)
                if match: # Begin of an object file
                    object_node = ObjectNode(match.group(1))
                else:
                    node = parse_sym_line(l)
                    if node is not None:
                        if object_node is not None:
                            object_node.add_sub_node(node)
                        else:
                            yield node
        if object_node is not None:
            yield object_node

def parse_readelf(filepath):
    def parse_sym_line(l):
        fields = list(filter(lambda e: e != "", l.strip(" \t\n").expandtabs().split(" ")))
        if (len(fields) != 8) or not (all(map(lambda c: ('0' <= c) and (c <= '9'), fields[2]))):
            return None
        addr = fields[1]
        size = int(fields[2])
        stype = fields[3]
        section = fields[6]
        name = fields[7]
        if stype == "FUNC":
            return FunctionNode(name, size)
        elif stype == "OBJECT":
            # It could be possible with help of the section number ("Ndx") to
            # make the difference between VariableNode and ConstantNode.
            return VariableNode(name, size)
        else:
            return None
    with subprocess.Popen(["readelf", "--syms", "--wide", filepath], stdout=subprocess.PIPE) as p:
        for l in [str(le, 'utf-8') for le in p.stdout.readlines()]:
            n = parse_sym_line(l)
            if n is not None:
                yield n

def populate_container_with_nm(filepath, container):
    for n in parse_nm(filepath):
        c.add_sub_node(n)
    c.compute_sizes()

def populate_container_with_readelf(filepath, container):
    for n in parse_readelf(filepath):
        c.add_sub_node(n)
    c.compute_sizes()

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description='LinkerReport')

    parser.add_argument('--object', dest='objectfile', nargs="+", type=str, help='Input object file', default=[])
    parser.add_argument('--archive', dest='archivefile', nargs="+", type=str, help='Input archive file', default=[])
    parser.add_argument('--elf', dest='elffile', nargs="+", type=str, help='Input ELF file', default=[])

    parser.add_argument('--human-readable', dest='human_readable', action='store_true', help='Human readable output', default=False)
    parser.add_argument('--summarize', dest='summarize', action='store_true', help='Sumarize output', default=False)
    parser.add_argument('--filter', dest='filter', nargs="+", help='Filter to apply on nodes list (only with table output).', default=[])

    parser.add_argument('--out-format', dest='output_format', nargs="?", type=str, help='Output format (json, table)', default="json")
    parser.add_argument('--out', dest='output_file', nargs="?", type=argparse.FileType('w'), help='Output file', default=sys.stdout)

    args = parser.parse_args()

    # Build the list of filters
    fs = []
    for fstr in args.filter:
        m = re.fullmatch("size>([0-9]+)", fstr)
        if (m is not None) and (len(m.groups()[0]) > 0):
            fs.append(NodeEncoder.LeafBiggerFilter(int(m.groups()[0])))
        m = re.fullmatch("size<([0-9]+)", fstr)
        if (m is not None) and (len(m.groups()[0]) > 0):
            fs.append(NodeEncoder.LeafSmallerFilter(int(m.groups()[0])))
        m = re.fullmatch("name=(.+)", fstr)
        if (m is not None) and (len(m.groups()[0]) > 0):
            fs.append(NodeEncoder.NameFilter(str(m.groups()[0])))

    # Build the list of ContainerNodes (executable, archive or object files) corresponding to the given arguments.
    cs = []
    for files, node_type in [(args.objectfile, ObjectNode), (args.archivefile, ArchiveNode)]:
        for filename in files:
            c = node_type(os.path.basename(filename))
            populate_container_with_nm(filename, c)
            cs.append(c)
    for files, node_type in [(args.elffile, ExecutableNode)]:
        for filename in files:
            c = node_type(os.path.basename(filename))
            populate_container_with_readelf(filename, c)
            cs.append(c)

    # Configure the encoders
    NodeEncoder.is_recursive = True
    NodeEncoder.recursion_level = 1 if args.summarize else 32
    NodeEncoder.is_human_readable = args.human_readable
    NodeEncoder.filters = fs

    # Encode the list of ContainerNodes in the selected output format.
    output_str = ""
    if args.output_format == "table":
        output_str = WikiTableNodeEncoder().dumps(cs)
    elif args.output_format == "json":
        for c in cs:
            output_str += json.dumps(c, cls=JsonNodeEncoder, indent=4, sort_keys=False)
    else:
        parser.print_help()

    if len(output_str) > 0:
        args.output_file.write(output_str)
        print("")
