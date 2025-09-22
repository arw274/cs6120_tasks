import sys
import json

def basic_blocks(instrs, quiet=False):
    blocks = [[]]
    labels = {}
    for inst in instrs:
        if "label" in inst and len(blocks[-1]) > 0:
            blocks.append([])
        blocks[-1].append(inst)
        if "label" not in inst and inst["op"] in ("br, jmp"):
            blocks.append([])
    for i, b in enumerate(blocks): 
        if len(b) == 0:
            if not quiet: print("Warning: empty block detected")
        elif "label" in b[0]:
            if not quiet: print("Block {}: {}".format(i, b))
            labels[b[0]["label"]] = i
        else:
            if not quiet: print("Block {}: {}".format(i, b))
    return [b for b in blocks if len(b) > 0], labels

def cfg(blocks, labels):
    graph = {}
    for i, b in enumerate(blocks):
        if "op" in b[-1] and b[-1]["op"] in ("br", "jmp"):
            graph[i] = [labels[l] for l in b[-1]["labels"]]
        elif len(blocks) > i+1 and "op" in b[-1] and b[-1]["op"] != "ret":
            graph[i] = [i+1]
        else:
            graph[i] = []
    return graph

def all_cfgs(full_bril):
    ret = {}
    for f in full_bril["functions"]:
        if len(full_bril) > 1: print("Function:", f["name"])
        ret[f["name"]] = cfg(*basic_blocks(f["instrs"]))
    return ret

if __name__ == "__main__":
    full_bril = json.load(sys.stdin)
    cfgs = all_cfgs(full_bril)
    print(cfgs)
