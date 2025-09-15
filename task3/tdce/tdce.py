import sys, os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from task2.cfg.cfg import basic_blocks 

def globally_unused_vars(func):
    """Remove all variables that are defined but never used."""
    used = set()
    for instr in func["instrs"]:
        if "args" in instr and instr["args"]:
            used.update(instr["args"])
    
    filtered_instrs = []
    for instr in func["instrs"]:
        if "dest" in instr and instr["dest"] not in used:
            continue
        filtered_instrs.append(instr)
    func["instrs"] = filtered_instrs

def iterate(func):
    """Iteratively apply optimizations until no changes occur."""
    while True:
        before = len(func["instrs"])
        globally_unused_vars(func)
        after = len(func["instrs"])
        if before == after:
            break

def locally_killed_instrs(func):
    """Remove instructions that are reassigned before they are used within the same block."""
    blocks, _ = basic_blocks(func["instrs"], quiet=True)
    for block in blocks:
        assigned = {}
        for instr in reversed(block):
            if "args" in instr and instr["args"]:
                for arg in instr["args"]:
                    assigned[arg] = False
            if "dest" in instr:
                if instr["dest"] in assigned and assigned[instr["dest"]]:
                    block.remove(instr)
                else:
                    assigned[instr["dest"]] = True
            
    func["instrs"] = [instr for block in blocks for instr in block]
    
def dce(full_bril):
    for func in full_bril["functions"]:
        iterate(func)
        locally_killed_instrs(func)
    return full_bril

if __name__ == "__main__":
    full_bril = json.load(sys.stdin)
    optimized_bril = dce(full_bril)
    print(json.dumps(optimized_bril, indent=2))