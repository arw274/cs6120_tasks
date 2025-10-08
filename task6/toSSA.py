import os, sys, json
import argparse, logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from task4.worklist import flip_cfg
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
    
    blocks, _ = basic_blocks(func["instrs"], quiet=True)
    for i, block in enumerate(blocks):
        for instr in block:
            if "dest" in instr:
                if instr["dest"] not in vars:
                    vars[instr["dest"]] = []
                vars[instr["dest"]].append(i)

    return vars

def get_uses(func) -> dict:
    """Get the set of variables used in a function.

    Args:
        func: a function in bril JSON format.
    
    Returns:
        A dict of (str: List) pairs of var names and blocks where var is used.
    """
    vars = {}
    
    blocks, _ = basic_blocks(func["instrs"], quiet=True)
    for i, block in enumerate(blocks):
        defined = set()
        for instr in block:
            if "args" in instr:
                for arg in instr["args"]:
                    if arg not in vars and arg not in defined:
                        vars[arg] = []
                    if arg not in defined:
                        vars[arg].append(i)
            if "dest" in instr:
                defined.add(instr["dest"])
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
                    insert_pt = 0
                    if "label" in blocks[d][0]:
                        insert_pt = 1
                    if var not in phi:
                        phi[var] = []
                    phi[var].append(d)
                    blocks[d].insert(insert_pt, {"op": "get", "args": [], "dest": var, "type": "int"}) # TODO: need types!
                    has_already.add(d)
                    if d not in def_blocks:
                        worklist.append(d)
    
    # flatten blocks back into instrs
    func["instrs"] = [instr for block in blocks for instr in block]
    
def add_phi_nodes_new(func, def_blocks, use_blocks) -> dict:
    blocks, labels = basic_blocks(func["instrs"], quiet=True)
    graph = cfg(blocks, labels)
    flipped_graph = flip_cfg(graph)
    phi_placed = {}
    def place_nodes(block_idx, var):
        if var in phi_placed and block_idx in phi_placed[var]:
            return
        # place phi node in block
        insert_pt = 0
        if "label" in blocks[block_idx][0]:
            insert_pt = 1
        blocks[block_idx].insert(insert_pt, {"op": "get", "args": [], "dest": var, "type": "int"}) # TODO: need types!
        # add block to list of placed
        if var not in phi_placed:
            phi_placed[var] = []
        phi_placed[var].append(block_idx)
        # recurse on predecessors not in def_blocks:
        for b in flipped_graph[block_idx]:
            if b not in def_blocks[var]:
                place_nodes(b, var)
    
    for v in use_blocks:
        for b in use_blocks[v]:
            place_nodes(b, v)
    
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
    graph = reachable_cfg(cfg(blocks, labels), 0)
    counters = {v: 0 for v in vars.keys()}  # current version of each var
    stacks = {v: [] for v in vars.keys()}   # stack of versions of each var
    gets = [[] for b in range(len(blocks))]
    # which variables each block has to get and what the new name is
    defs_rename = [{} for b in range(len(blocks))]
    # which variables each block defines and what the new name is

    def rename_block(b):
        assigned_in_block = []  # list of (var, new_name) assigned in this block
        for instr in blocks[b]:
            if "args" in instr and instr["args"]:
                new_args = []
                for arg in instr["args"]:
                    if stacks[arg][-1] >= 0:
                        new_args.append(f"{arg}.{stacks[arg][-1]}")
                    else:
                        new_args.append(arg)
                instr["args"] = new_args
            if "dest" in instr:
                var = instr["dest"]
                new_name = f"{var}.{counters[var]}"
                stacks[var].append(counters[var])
                counters[var] += 1
                instr["dest"] = new_name
                assigned_in_block.append((var, new_name))
                if instr["op"] == "get":
                    gets[b].append((var, new_name))
        
        for child in dom_tree.get(b, []):
            rename_block(child)

        for var, new_name in assigned_in_block:
            defs_rename[b][var] = new_name
            # might overwrite; this is intended; get last new_name used in block
        
        for var, _ in assigned_in_block:
            stacks[var].pop()
    
    for v in vars.keys():
        if -1 in vars[v]:  # function argument
            stacks[v].append(-1)
    rename_block(0)  # assuming entry block is 0

    for b in range(len(blocks)):
        insert_pt = len(blocks[b])
        if "op" in blocks[b][-1] and blocks[b][-1]["op"] in ("jmp", "br"):
            insert_pt -= 1
        for child in graph[b]:
            for v, new_name in gets[child]:
                blocks[b].insert(insert_pt,
                {
                    "op": "set",
                    "args": [new_name, defs_rename[b][v]]
                })

    func["instrs"] = [instr for block in blocks for instr in block]

if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-v', '--verbose', action='store_true')
    # args = parser.parse_args()
    # logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)

    full_bril = json.load(sys.stdin)
    for func in full_bril["functions"]:
        # add new entry block so it can set up the args
        if "label" not in func["instrs"][0]:
            func["instrs"].insert(0, {"label": "__entry__"}) # make space for set-only block
        blocks, labels = basic_blocks(func["instrs"], quiet=True)
        entry = 0  # Assuming the first block is the entry block
        graph = reachable_cfg(cfg(blocks, labels), entry)
        dom_tree = dominator_tree(graph, entry)
        defs = get_defs(func)
        uses = get_uses(func)
        add_phi_nodes_new(func, defs, uses)
        rename_vars(func, dom_tree, defs)
        if "args" in func:
            for v in func["args"]:
                orig_name = v["name"]
                func["instrs"].insert(0, {"op": "set", "args": [f"{orig_name}.0", orig_name]})
    print(json.dumps(full_bril))