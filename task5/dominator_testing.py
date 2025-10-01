import os, sys, json
import argparse, logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from task2.cfg.cfg import basic_blocks, cfg, reachable_cfg
from dominators import dominators
from dominator_tree import dominator_tree
from dominance_frontier import dominance_frontier

def reachable_without(graph, entry, without):
    # do DFS from entry, except do not interact with node "without"
    visited = set()

    def visit(node):
        if node in visited or node == without:
            return
        visited.add(node)
        for succ in graph[node]:
            visit(succ)

    visit(entry)
    return visited

def brute_force_dominators(graph, entry):
    cfg = reachable_cfg(graph, entry)
    all_nodes = set(cfg.keys())
    dominators = {n: set() for n in all_nodes}
    for n in all_nodes:
        # n dominates all nodes not in reachable_without
        reachable = reachable_without(graph, entry, n)
        for m in all_nodes:
            if m not in reachable:
                dominators[m].add(n)
    return dominators

def dominators_from_tree(tree, entry):
    # walk tree collecting path
    doms = {}
    def doms_from_subtree(root, accumulated_doms):
        accumulated_doms.append(root)
        doms[root] = set(accumulated_doms)
        for c in tree[root]:
            doms_from_subtree(c, accumulated_doms[:])
    doms_from_subtree(entry, [])
    return doms

# uses only dominators
def brute_force_dominance_frontier(graph, dom, entry):
    cfg = reachable_cfg(graph, entry)
    dominated = {b: set() for b in cfg.keys()}
    for b in cfg.keys():
        for d in dom[b]:
            dominated[d].add(b)

    df = {b: set() for b in cfg.keys()}
    for b in cfg.keys():
        for d in dominated[b]:
            for s in cfg[d]:
                if b not in dom[s]:
                    df[b].add(s)
        
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)

    full_bril = json.load(sys.stdin)
    for func in full_bril["functions"]:
        print("Function:", func["name"])
        blocks, labels = basic_blocks(func["instrs"], quiet=True)
        graph = cfg(blocks, labels)
        entry = 0  # Assuming the first block is the entry block
        doms_orig = dominators(graph, entry)
        doms_bf = brute_force_dominators(graph, entry)
        tree = dominator_tree(graph, entry)
        doms_from_tree = dominators_from_tree(tree, entry)
        df_bf = brute_force_dominance_frontier(graph, doms_orig, entry)
        df_from_tree = dominance_frontier(graph, doms_from_tree, tree, entry)
        print(" Doms valid:", doms_orig == doms_bf)
        print(" Tree valid:", doms_orig == doms_from_tree)
        print(" DF valid:", df_bf == df_from_tree)
        if df_bf != df_from_tree:
            print(reachable_cfg(graph, entry))
            print("DF brute force:", df_bf)
            print("DF from tree:", df_from_tree)