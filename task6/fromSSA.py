import sys, json

def from_ssa(instrs, var_types):
    for i in range(len(instrs)):
        if "op" in instrs[i]:
            if instrs[i]["op"] == "set":
                instrs[i] = {
                    "op": "id",
                    "dest": "shadow_" + instrs[i]["args"][0],
                    "type": "int", # TODO: FIX TYPE
                    "args": [instrs[i]["args"][1]]
                }
            elif instrs[i]["op"] == "get":
                instrs[i] = {
                    "op": "id",
                    "dest": instrs[i]["dest"],
                    "type": instrs[i]["type"],
                    "args": ["shadow_" + instrs[i]["dest"]]
                }

if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-v', '--verbose', action='store_true')
    # args = parser.parse_args()
    # logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)

    full_bril = json.load(sys.stdin)
    for func in full_bril["functions"]:
        from_ssa(func["instrs"], {})
    print(json.dumps(full_bril))