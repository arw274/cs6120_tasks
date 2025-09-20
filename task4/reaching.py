from worklist import worklist
import os, sys, json

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from task2.cfg.cfg import basic_blocks, cfg

# Perform reaching definitions analysis on the given function.
def reaching_defs(func):
    blocks, labels = basic_blocks(func["instrs"], quiet=False)
    graph = cfg(blocks, labels)

    def transfer(b_idx, state): # kill and gen
        new_state = state.copy()
        block = blocks[b_idx]
        for curr_instr_idx, curr_instr in enumerate(block):
            if "dest" in curr_instr:
                # kill previous definitions of the same variable
                new_state = [(instr_idx, block_idx) for instr_idx, block_idx in new_state if blocks[block_idx][instr_idx]["dest"] != curr_instr["dest"]]
                new_state.append((curr_instr_idx, b_idx))
        return new_state

    def meet(states): # union of all reaching definitions
        result = set()
        for s in states:
            result.update(s)
        return list(result)

    initial = []
    state = worklist(blocks, graph, transfer, meet, initial)
    return state

if __name__ == "__main__":
    full_bril = json.load(sys.stdin)
    for func in full_bril["functions"]:
        print("Function:", func["name"])
        print()
        state = reaching_defs(func)
        for b, s in state.items():
            print("Block", b, "reaching definitions:")
            for instr, idx in s:
                print("  From block", idx, ": instr", instr)
        print()