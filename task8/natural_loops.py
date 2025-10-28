import os, sys, json
import argparse, logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from task4.worklist import flip_cfg
from task2.cfg.cfg import basic_blocks, cfg, reachable_cfg
from task5.dominators import dominators

def natural_loops(cfg, dominators):
    """Get all the natural loops in a function.

    Args:
        cfg: the cfg of basic blocks in the function
        dominators: a map from each cfg node to the nodes which dominate it

    Returns:
        A list of (node, Set[node]) for the header of each loop and all the nodes in it
    """
    # from lesson 5 page:
    # A natural loop is the smallest set of vertices L including A and B such that, 
    # for every v in L, either all the predecessors of v are in L or v=B.
    flipped_cfg = flip_cfg(cfg)
    
    # find all backedges
    backedges = []
    for u in cfg:
        for v in cfg[u]:
            if v in dominators[u]:
                backedges.append((u,v))

    loops = []
    # for each: 
    for u, v in backedges:
        if u == v:
            loops.append((u, {u}))
            continue
        # Add all predecessors of tail, and so on, and so on, until header is reached
        loop_nodes = {u, v}
        added = {u}
        to_add = set()
        while(len(added) > 0):
            for n in added:
                for p in flipped_cfg[n]:
                    if p not in loop_nodes:
                        to_add.add(p)
            loop_nodes.update(to_add)
            added = to_add
            to_add = set()
        loops.append((v, loop_nodes))
    # merge all overlapping non-nested loops with the same header
    for i in range(len(loops)-1, -1, -1):
        for j in range(i-1, -1, -1):
            if loops[i][0] == loops[j][0]:
                # possible merge
                blocks_union = loops[i][1] | loops[j][1]
                if len(blocks_union) > max(len(loops[i][1]), len(loops[j][1])):
                    # merge
                    loops[j] = (loops[j][0], blocks_union)
                    del loops[i]
    return loops


if __name__ == "__main__":
    full_bril = json.load(sys.stdin)
    for func in full_bril["functions"]:
        blocks, labels = basic_blocks(func["instrs"], quiet=True)
        entry = 0  # Assuming the first block is the entry block
        graph = reachable_cfg(cfg(blocks, labels), entry)
        doms = dominators(graph, entry)
        print(labels)
        print(natural_loops(graph, doms))
