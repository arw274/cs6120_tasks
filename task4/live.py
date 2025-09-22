from worklist import worklist, flip_cfg
import os, sys, json

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from task2.cfg.cfg import basic_blocks, cfg

# Perform reaching definitions analysis on the given function.
def live_vars(func):
    blocks, labels = basic_blocks(func["instrs"], quiet=True)
    graph = cfg(blocks, labels)
    print(graph)
    graph = flip_cfg(graph) # live vars should be done backwards

    def transfer(b_idx, state):
        new_state = set(state)
        block = blocks[b_idx]
        for curr_instr in block[::-1]:
            if "dest" in curr_instr:
                # var defined here not live before this point
                new_state.discard(curr_instr["dest"])
            if "args" in curr_instr:
                # vars used here live before this point even if redefined here
                new_state.update(curr_instr["args"])
        return new_state

    def meet(states): # union of all live variables
        result = set()
        for s in states:
            result.update(s)
        return result

    initial = set()
    state = worklist(blocks, graph, transfer, meet, initial)
    return state[1]

if __name__ == "__main__":
    full_bril = json.load(sys.stdin)
    for func in full_bril["functions"]:
        print("Function:", func["name"])
        print()
        state = live_vars(func)
        blocks, labels = basic_blocks(func["instrs"], quiet=True)
        block_names = []
        for i in range(len(blocks)):
            block_names.append(blocks[i][0]["label"] if "label" in blocks[i][0] else str(i))
        for b, s in state.items():
            print("Block", block_names[b], "live variables at input:")
            print(s)
        print()