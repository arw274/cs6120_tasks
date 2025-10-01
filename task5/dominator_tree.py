import os, sys, json
import argparse, logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from task2.cfg.cfg import basic_blocks, cfg, reachable_cfg
from dominators import dominators

def dominator_tree(cfg, entry) -> dict:
    """Compute the dominator tree for a control flow graph.

    The dominator tree represents dominators exactly: 
    each node is a (strict) dominator for all and only its (strict) descendants in the tree.

    Args:
        cfg: A control flow graph represented as a dictionary mapping block
            labels to lists of successor block labels.
        entry: The label of the entry block.

    Returns:
        A dictionary mapping each block label to the labels of its children in the tree.
    """
    cfg = reachable_cfg(cfg, entry)
    doms = dominators(cfg, entry)
    tree = {entry: []}
    # If both A and B dominate C, it must be that A dominates B or vice versa
    # Thus, any nodes' dominators form a path in the tree.
    for block in cfg.keys():
        # if it's not added:
        if block not in tree.keys():
            # get all its dominators, put them in order (more dominators means later in path)
            dominators_ordered = sorted(doms[block], key=lambda d: len(doms[d]))
            # add them to the tree in order
            for i in range(len(dominators_ordered)-1):
                if dominators_ordered[i+1] not in tree.keys():
                    tree[dominators_ordered[i+1]] = []
                    tree[dominators_ordered[i]].append(dominators_ordered[i+1])
    return tree



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)

    full_bril = json.load(sys.stdin)
    for func in full_bril["functions"]:
        print("Function:", func["name"])
        blocks, labels = basic_blocks(func["instrs"], quiet=False)
        entry = 0  # Assuming the first block is the entry block
        graph = cfg(blocks, labels)
        dom_tree = dominator_tree(graph, entry)
        for b, d in dom_tree.items():
            print("Block", b, "children:", d)
        print()