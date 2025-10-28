import os, sys, json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from task2.cfg.cfg import basic_blocks, cfg, reachable_cfg
from task4.worklist import flip_cfg
from task5.dominators import dominators
from task8.natural_loops import natural_loops

SIDE_EFFECT_OPS = ("call", "div", "set")

def create_preheaders(func):
    blocks, labels = basic_blocks(func["instrs"], quiet=True)
    entry = 0  # Assuming the first block is the entry block
    graph = reachable_cfg(cfg(blocks, labels), entry)
    doms = dominators(graph, entry)
    headers_loops = natural_loops(graph, doms)
    reverse_graph = flip_cfg(graph)
    for (h, l) in headers_loops:
        outside_loop_preds = []
        for i in reverse_graph[h]:
            if i not in l:
                outside_loop_preds.append(i)
        if len(outside_loop_preds) != 1 or len(graph[outside_loop_preds[0]]) > 1:
            # create preheader
            label = blocks[h][0]["label"]
            blocks[h].insert(0, {"label": label+"__preheader"})
            # point everything to preheader instead
            for b in outside_loop_preds:
                if "labels" in blocks[b][-1]:
                    idx = blocks[b][-1]["labels"].index(label)
                    blocks[b][-1]["labels"][idx] = label+"__preheader"
    func["instrs"] = [instr for block in blocks for instr in block]

def single_loop_licm(all_blocks, cfg, doms, loop, preheader_idx):
    loop = list(loop)
    # add everything defined in loop to non-LI list
    li_instrs = []
    non_li_vars = set()
    var_num_defs = {}
    uses = {}
    for block in loop:
        for instr in all_blocks[block]:
            if "dest" in instr:
                non_li_vars.add(instr["dest"])
                if instr["dest"] in var_num_defs:
                    var_num_defs[instr["dest"]] += 1
                else:
                    var_num_defs[instr["dest"]] = 1
            if "args" in instr:
                for a in instr["args"]:
                    if a in uses:
                        uses[a].append(block)
                    else:
                        uses[a] = [block]
    
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
    # until convergence:
    changed = True
    while changed:
        # add all unique-dest instrs with no non-LI args to LI instr list and remove from non_li
        changed = False
        for block in loop:
            to_move_now = []
            for j, instr in enumerate(all_blocks[block]):
                unique_def = "dest" in instr and var_num_defs[instr["dest"]] == 1
                dominates_uses = False
                if "dest" in instr:
                    if instr["dest"] not in uses:
                        dominates_uses = True
                    else:
                        dominates_uses = all([block in doms[b] for b in uses[instr["dest"]]])
                if (block, j) not in li_instrs and unique_def and dominates_uses:
                    if "args" not in instr or all([a not in non_li_vars for a in instr["args"]]):
                        # loop invariant instr
                        move = False
                        if all([block in doms[e] for e in exits]):
                            move = True
                        elif instr["op"] not in SIDE_EFFECT_OPS:
                            if "dest" not in blocks[block][j] or blocks[block][j]["dest"] not in used_outside_loop:
                                move = True
                        if move:
                            li_instrs.append((block,j))
                            non_li_vars.remove(instr["dest"])
                            to_move_now.append(j)
                            changed = True
            ph_end = len(all_blocks[preheader_idx])
            for j in to_move_now[::-1]:
                # delete jth element of block
                # add it to the end of preheader
                all_blocks[preheader_idx].insert(ph_end, all_blocks[block].pop(j))

if __name__ == "__main__":
    full_bril = json.load(sys.stdin)
    for func in full_bril["functions"]:
        create_preheaders(func)
        blocks, labels = basic_blocks(func["instrs"], quiet=True)
        entry = 0  # Assuming the first block is the entry block
        graph = reachable_cfg(cfg(blocks, labels), entry)
        reverse_graph = flip_cfg(graph)
        doms = dominators(graph, entry)
        for l in natural_loops(graph, doms):
            single_loop_licm(blocks, graph, doms, l[1], reverse_graph[l[0]][0])
        func["instrs"] = [instr for block in blocks for instr in block]
    print(json.dumps(full_bril))
