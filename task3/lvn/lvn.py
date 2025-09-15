import sys, os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from task2.cfg.cfg import basic_blocks

NO_VALUE_OPS = ("jmp", "nop")


def lvn_block(block):
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
                value = {"op": inst["op"],
                         "type": inst["type"],
                         "args": [map_from_orig_names[a] for a in inst["args"]]}
            # check to see if value already computed, if so:
            if inst["op"] != "call" and value in values:
                # update table and emit id (will be dead code unless used in future block)
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

def lvn(full_bril):
    for f in full_bril["functions"]:
        blocks, _ = basic_blocks(f["instrs"], quiet=True)
        new_instrs = []
        for b in blocks:
            new_instrs.extend(lvn_block(b))
        f["instrs"] = new_instrs

if __name__ == "__main__":
    full_bril = json.load(sys.stdin)
    lvn(full_bril)
    print(json.dumps(full_bril, indent=2))

