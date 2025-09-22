from collections import deque

def flip_cfg(cfg) -> dict:
    '''
    Given a control flow graph as a dict mapping block to list of successor blocks,
    return the reverse graph mapping block to list of predecessor blocks.
    '''
    rev = {b: [] for b in cfg}
    for b, succs in cfg.items():
        for s in succs:
            rev[s].append(b)
    return rev

def worklist(blocks, cfg, transfer, meet, initial) -> dict:
    '''
    A generic worklist algorithm for dataflow analysis.
    blocks: list of blocks
    cfg: control flow graph as a dict mapping block to list of successor blocks
    transfer: function(block_idx, state) -> new_state
    meet: function(list_of_states) -> combined_state
    initial: initial state for each block
    '''
    worklist = deque(range(len(blocks)))
    in_state = {blocks.index(b): initial for b in blocks}
    out_state = {blocks.index(b): initial for b in blocks}
    rev = flip_cfg(cfg)
    while worklist:
        b_idx = worklist.popleft()
        if rev[b_idx]: in_state[b_idx] = meet([out_state[p] for p in rev[b_idx]]) 
        new_state = transfer(b_idx, in_state[b_idx])
        if new_state != out_state[b_idx]:
            out_state[b_idx] = new_state
            for s in cfg[b_idx]:
                worklist.append(s)
    return in_state, out_state