import os, sys, json
import argparse, logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from task2.cfg.cfg import basic_blocks, cfg, reachable_cfg
from task4.worklist import flip_cfg
from task5.dominators import dominators
from task8.natural_loops import natural_loops

SIDE_EFFECT_OPS = ("call", "div")

def create_preheaders(func):
    blocks, labels = basic_blocks(func["instrs"], quiet=True)
    entry = 0  # Assuming the first block is the entry block
    graph = reachable_cfg(cfg(blocks, labels), entry)
    doms = dominators(graph, entry)
    headers_loops = natural_loops(graph, doms)
    reverse_graph = flip_cfg(graph)
    all_headers = set()
    for (h, l) in headers_loops:
        all_headers.add(h)
    for h in all_headers:
        outside_loop_preds = []
        for i in reverse_graph[h]:
            if i not in l:
                outside_loop_preds.append(i)
        if len(outside_loop_preds) > 1:
            # create preheader
            label = blocks[h][0]["label"]
            blocks[h].insert(0, {"label": label+"__preheader"})
            # point everything to preheader instead
            for b in outside_loop_preds:
                if "labels" in blocks[b][-1]:
                    idx = blocks[b][-1]["labels"].index(label)
                    blocks[b][-1]["labels"][idx] = label+"__preheader"
    func["instrs"] = [instr for block in blocks for instr in block]

def single_loop_licm(all_blocks, cfg, doms, loop, preheader): # DOES NOT WORK ON SSA
    loop = list(loop)
    # add everything defined in loop to non-LI list
    li_instrs = []
    non_li_vars = set()
    var_num_defs = {}
    for block in loop:
        for instr in all_blocks[block]:
            if "dest" in instr:
                non_li_vars.add(instr["dest"])
                if instr["dest"] in var_num_defs:
                    var_num_defs[instr["dest"]] += 1
                else:
                    var_num_defs[instr["dest"]] = 1
    # until convergence:
    changed = True
    while changed:
        # add all unique-dest instrs with no non-LI args to LI instr list and remove from non_li
        changed = False
        for block in loop:
            for j, instr in enumerate(all_blocks[block]):
                if (block, j) not in li_instrs and "dest" in instr and var_num_defs[instr["dest"]] == 1:
                    if "args" not in instr or all([a not in non_li_vars for a in instr["args"]]):
                        li_instrs.append((block,j))
                        non_li_vars.remove(instr["dest"])
                        changed = True
    print(li_instrs)
    # move all to preheader if:
        # instr dominates exits OR BOTH
        # instr has no side effects AND
        # value is dead after loop
    to_move = []
    exits = []
    for block in loop:
        if any([c not in loop for c in cfg[block]]):
            exits.append(block)
    used_outside_loop = set()
    for i, block in enumerate(all_blocks):
        if i not in loop:
            for instr in block:
                if "args" in instr:
                    used_outside_loop.update(instr["args"])
    for i, j in li_instrs:
        if all([i in doms[e] for e in exits]):
            to_move.append((i, j))
        elif blocks[i][j]["op"] not in SIDE_EFFECT_OPS:
            if "dest" not in blocks[i][j] or blocks[i][j]["dest"] not in used_outside_loop:
                            to_move.append((i, j))
    print(to_move)

if __name__ == "__main__":
    full_bril = json.load(sys.stdin)
    for func in full_bril["functions"]:
        create_preheaders(func)
        blocks, labels = basic_blocks(func["instrs"], quiet=True)
        entry = 0  # Assuming the first block is the entry block
        graph = reachable_cfg(cfg(blocks, labels), entry)
        print(graph)
        reverse_graph = flip_cfg(graph)
        doms = dominators(graph, entry)
        print(labels)
        for l in natural_loops(graph, doms):
            print(l)
            single_loop_licm(blocks, graph, doms, l[1], None)
