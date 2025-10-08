import os, sys, json
import argparse, logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from task2.cfg.cfg import basic_blocks, cfg, reachable_cfg
from .dominators import dominators, postorder
from .dominator_tree import dominator_tree

def dominance_frontier(cfg, dom, dom_tree, entry) -> dict:
    """Compute the dominance frontier for each block in a control flow graph.

    The dominance frontier of a block B is the set of all blocks D such that
    B dominates a predecessor of D but does not strictly dominate D. 

    Args:
        cfg: A control flow graph represented as a dictionary mapping block
            labels to lists of successor block labels.
        dom: A dictionary mapping each block label to the set of labels of blocks
            that dominate it.
        dom_tree: A dictionary mapping each block label to the set of labels of children 
            in the dominator tree.
        entry: The label of the entry block.
    
    Returns:
        A dictionary mapping each block label to the set of labels in its dominance frontier.
    """
    cfg = reachable_cfg(cfg, entry)
    df = {b: set() for b in cfg.keys()}

    # single pass in postorder should be sufficient?
    post = postorder(cfg, entry)

    for b in post:
        if dom_tree[b]: 
            # for each child c of b in dominator tree
            for c in dom_tree[b]:
                # add the blocks in c's dominance frontier and children of c 
                # that b does not strictly dominate to b's dominance frontier
                for g in df[c].union(cfg[c]):
                    if b not in dom[g]:
                        df[b].add(g)
        # look at its successors
        for s in cfg[b]:
            if b not in dom[s]:
                df[b].add(s)
        logging.debug(f"Block {b}, DF: {df[b]}")

    return df


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
        print("CFG:", graph)
        dom = dominators(graph, entry)
        print("Dominators:", dom)
        dom_tree = dominator_tree(graph, entry)
        print("Dominator Tree:", dom_tree)
        df = dominance_frontier(graph, dom, dom_tree, entry)
        print("Dominance Frontier:", df)
        print()        

