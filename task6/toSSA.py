import os, sys, json
import argparse, logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from task2.cfg.cfg import basic_blocks, cfg, reachable_cfg
from task5.dominators import dominators, postorder
from task5.dominator_tree import dominator_tree
from task5.dominance_frontier import dominance_frontier

def get_defs(func) -> dict:
    """Get the set of variables defined in a function, including function arguments.

    Args:
        func: a function in bril JSON format.
    
    Returns:
        A dict of (str: List) pairs of var names and blocks where var is assigned.
        If var is passed as argument, block is -1.
    """
    vars = {}
    for arg in func.get("args", []):
        vars[arg["name"]] = [-1]
    
    blocks, _ = basic_blocks(func["instrs"], quiet=False)
    for i, block in enumerate(blocks):
        for instr in block:
            if "dest" in instr:
                if instr["dest"] not in vars:
                    vars[instr["dest"]] = []
                vars[instr["dest"]].append(i)

    return vars

def phi_nodes(func, df, vars):
    """Insert phi nodes (get's only) for variables in blocks in their dominance frontiers.

    Args:
        func: a function in bril JSON format.
        df: dominance frontier as returned by dominance_frontier.
        vars: dict of (str: List) pairs of var names and blocks where var is assigned.

    Returns:
        phi: dict of (str: List) pairs of var names and blocks where phi nodes were inserted.

    """
    phi = {}
    blocks, _ = basic_blocks(func["instrs"], quiet=True)
    for var, def_blocks in vars.items():
        worklist = def_blocks[:]
        has_already = set()  # blocks that already have a phi node for var
        while worklist:
            b = worklist.pop()
            for d in df[b]:
                if d not in has_already:
                    if var not in phi:
                        phi[var] = []
                    phi[var].append(d)
                    blocks[d].insert(0, {"op": "get", "args": [], "dest": var, "type": "int"}) #TODO: need types!
                    has_already.add(d)
                    if d not in def_blocks:
                        worklist.append(d)
    
    # flatten blocks back into instrs
    func["instrs"] = [instr for block in blocks for instr in block]
    
