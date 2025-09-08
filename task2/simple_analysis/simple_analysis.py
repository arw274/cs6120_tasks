import sys
import json

def call_graph(full_bril):
    ret = {}
    for f in full_bril["functions"]:
        ret[f["name"]] = set()
        for i in f["instrs"]:
            if "op" in i and i["op"] == "call":
                ret[f["name"]].update(i["funcs"])
    return ret

if __name__ == "__main__":
    full_bril = json.load(sys.stdin)
    cg = call_graph(full_bril)
    print(cg)