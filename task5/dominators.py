import os, sys, json
import argparse, logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from task2.cfg.cfg import basic_blocks, cfg
from task4.worklist import flip_cfg

def dominators(cfg, entry) -> dict:
    """Compute the dominator sets for each block in a control flow graph.

    A block D is said to dominate a block B if every path from the entry block
    to B must go through D. The entry block is considered to dominate itself.

    Args:
        cfg: A control flow graph represented as a dictionary mapping block
            labels to lists of successor block labels.
        entry: The label of the entry block.

    Returns:
        A dictionary mapping each block label to the set of labels of blocks
        that dominate it.
    """
    # Initialize dominator sets
    dom = {block: set(cfg.keys()) for block in cfg}
    dom[entry] = {entry}
    flipped_cfg = flip_cfg(cfg)
    rev_post = reverse_postorder(cfg, entry)
    logging.debug(f"Reverse postorder: {rev_post}")

    for block in rev_post:
        if block == entry:
            continue
        if flipped_cfg[block]:
            logging.debug(f"Block {block}, predecessors: {flipped_cfg[block]}") 
            dom[block] = set.intersection(*[dom[pred] for pred in flipped_cfg[block]]) | {block}
        else:
            logging.debug(f"Warning: block {block} has no predecessors")

    return dom

def reverse_postorder(cfg, entry) -> list:
    """Compute a reverse postorder traversal of the control flow graph.

    Args:
        cfg: A control flow graph represented as a dictionary mapping block
            labels to lists of successor block labels.
        entry: The label of the entry block.

    Returns:
        A list of block labels in reverse postorder.
    """
    visited = set()
    postorder = []

    def visit(node):
        if node in visited:
            return
        visited.add(node)
        for succ in cfg[node]:
            visit(succ)
        postorder.append(node)

    visit(entry)
    return postorder[::-1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)

    full_bril = json.load(sys.stdin)
    for func in full_bril["functions"]:
        print("Function:", func["name"])
        blocks, labels = basic_blocks(func["instrs"], quiet=False)
        graph = cfg(blocks, labels)
        entry = 0  # Assuming the first block is the entry block
        doms = dominators(graph, entry)
        for b, d in doms.items():
            print("Block", b, "is dominated by:", d)
        print()