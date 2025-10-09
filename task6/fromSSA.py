import sys, json

def get_types(func):
    types = {}
    for arg in func.get("args", []):
        types[arg["name"]] = arg["type"]
    for instr in func["instrs"]:
        if "dest" in instr:
            types[instr["dest"]] = instr["type"]

    return types

def from_ssa(instrs, var_types):
    for i in range(len(instrs)):
        if "op" in instrs[i]:
            if instrs[i]["op"] == "set":
                instrs[i] = {
                    "op": "id",
                    "dest": "shadow_" + instrs[i]["args"][0],
                    "type": var_types[instrs[i]["args"][0]],
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
    full_bril = json.load(sys.stdin)
    for func in full_bril["functions"]:
        from_ssa(func["instrs"], get_types(func))
    print(json.dumps(full_bril))