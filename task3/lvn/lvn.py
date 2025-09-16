import sys, os
import json
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from task2.cfg.cfg import basic_blocks

NO_VALUE_OPS = ("jmp", "nop")
COMMUTATIVE_OPS = ("add", "mul", "eq", "and", "or")

def lvn_block(block, semantics = True):
    emitted_instrs = []
    values = []
    new_names = []
    map_from_orig_names = {}

    definitions_left = {}

    for inst in block:
        # initialize values with variables defined in previous blocks
        if "args" in inst:
            for a in inst["args"]:
                # insert in table as literal if not already there
                if a not in map_from_orig_names:
                    values.append({"op": "_literal", "name": a})
                    new_names.append(a)
                    map_from_orig_names[a] = len(values) - 1
        # initialize definitions_left with how many times each variable is (re)defined in this block
        if "dest" in inst:
            if inst["dest"] in definitions_left:
                definitions_left[inst["dest"]] += 1
            else:
                definitions_left[inst["dest"]] = 1

    for inst in block:
        if ("label" in inst or inst["op"] in NO_VALUE_OPS):
            # does not handle values at all
            emitted_instrs.append(inst)
        elif "dest" in inst: # computes a value
            value = {}
            if inst["op"] == "const":
                value = {"op": inst["op"], "type": inst["type"], "value": inst["value"]}
            else:
                arg_nums = [map_from_orig_names[a] for a in inst["args"]]
                if semantics and inst["op"] in COMMUTATIVE_OPS:
                    arg_nums = sorted(arg_nums)
                value = {"op": inst["op"],
                         "type": inst["type"],
                         "args": arg_nums}
            # whether this is an extraneous id we should bypass
            # DO NOT BYPASS IDS OF LITERALS; we may lose copies since we don't rename literals
            # (deleting ids of literals broke core/euclid)
            remap_id = (semantics 
                        and inst["op"] == "id" 
                        and values[map_from_orig_names[inst["args"][0]]]["op"] != "_literal")
            # check to see if value already computed, if so:
            if inst["op"] != "call" and (remap_id or value in values):
                # update table and emit id (will be dead code unless used in future block)
                if remap_id:
                    map_from_orig_names[inst["dest"]] = map_from_orig_names[inst["args"][0]]
                else:
                    map_from_orig_names[inst["dest"]] = values.index(value)
                
                definitions_left[inst["dest"]] -= 1
                suffix = ""
                if definitions_left[inst["dest"]] > 0:
                    suffix = "_" + str(definitions_left[inst["dest"]])
                new_name = inst["dest"] + suffix

                emitted_instrs.append(
                    {"op": "id",
                     "type": inst["type"],
                     "dest": new_name,
                     "args": [new_names[map_from_orig_names[inst["dest"]]]]
                     })
            # else:
            else:
                # RENAME HERE
                definitions_left[inst["dest"]] -= 1
                suffix = ""
                if definitions_left[inst["dest"]] > 0:
                    suffix = "_" + str(definitions_left[inst["dest"]])
                new_name = inst["dest"] + suffix
                # add value to table, update mapping, emit renamed instr
                values.append(value)
                new_names.append(new_name)

                new_inst = inst.copy()
                new_inst["dest"] = new_name
                if "args" in inst:
                    renamed_args = [new_names[map_from_orig_names[a]] for a in inst["args"]]
                    new_inst["args"] = renamed_args
                emitted_instrs.append(new_inst)

                # have to update map down here so it doesn't get captured in renamed args
                map_from_orig_names[inst["dest"]] = len(values)-1
        else:
            # emit with renamed
            new_inst = inst.copy()
            if "args" in inst:
                    renamed_args = [new_names[map_from_orig_names[a]] for a in inst["args"]]
                    new_inst["args"] = renamed_args
            emitted_instrs.append(new_inst)
    return emitted_instrs

def lvn(full_bril, semantics=True):
    for f in full_bril["functions"]:
        blocks, _ = basic_blocks(f["instrs"], quiet=True)
        new_instrs = []
        for b in blocks:
            new_instrs.extend(lvn_block(b, semantics))
        f["instrs"] = new_instrs

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no_semantics", action="store_true")
    args = parser.parse_args()
    full_bril = json.load(sys.stdin)
    lvn(full_bril, not args.no_semantics)
    print(json.dumps(full_bril, indent=2))

