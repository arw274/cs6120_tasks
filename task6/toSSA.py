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


def add_phi_nodes(func, df, vars) -> dict:
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
            if b == -1: # function argument, skip
                continue
            for d in df[b]:
                if d not in has_already:
                    if var not in phi:
                        phi[var] = []
                    phi[var].append(d)
                    blocks[d].insert(0, {"op": "get", "args": [], "dest": var, "type": "int"}) # TODO: need types!
                    has_already.add(d)
                    if d not in def_blocks:
                        worklist.append(d)
    
    # flatten blocks back into instrs
    func["instrs"] = [instr for block in blocks for instr in block]
    

# TODO: handle cases where var is undefined along some paths (add undef?)
def rename_vars(func, dom_tree, vars) -> None:
    """Rename variables in a function to ensure each variable is assigned exactly once.

    Args:
        func: a function in bril JSON format.
        dom_tree: dominator tree as returned by dominator_tree.
        vars: dict of (str: List) pairs of var names and blocks where var is assigned.
    """
    blocks, labels = basic_blocks(func["instrs"], quiet=True)
    cfg = reachable_cfg(cfg(blocks, labels), 0)
    counters = {v: 0 for v in vars.keys()}  # current version of each var
    stacks = {v: [] for v in vars.keys()}   # stack of versions of each var

    def rename_block(b):
        assigned_in_block = []  # list of (var, new_name) assigned in this block
        for instr in blocks[b]:
            if "args" in instr and instr["args"]:
                instr["args"] = [f"{arg}.{stacks[arg][-1]}" for arg in instr["args"]]
            if "dest" in instr:
                var = instr["dest"]
                new_name = f"{var}.{counters[var]}"
                stacks[var].append(counters[var])
                counters[var] += 1
                instr["dest"] = new_name
                assigned_in_block.append((var, new_name))
        
        for child in cfg:
            # TODO: for p in child's get instructions, add set instruction in b with current version of p(var)
        
        for child in dom_tree.get(b, []):
            rename_block(child)
        
        for var, _ in assigned_in_block:
            stacks[var].pop()
    
    for v in vars.keys():
        if -1 in vars[v]:  # function argument
            stacks[v].append(-1)
    rename_block(0)  # assuming entry block is 0
    func["instrs"] = [instr for block in blocks for instr in block]