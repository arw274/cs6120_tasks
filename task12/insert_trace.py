import sys, json

def insert_trace(instrs:list, start_label, end_label, trace, guard_label_name):
    insert_pt = instrs.index({'label': start_label}) + 1
    to_insert = [{'op':'speculate'}] + trace
    to_insert.extend([
        {'op':'commit'},
        {'labels':[end_label],'op':'jmp'},
        {'label': guard_label_name}
    ])
    instrs = instrs[:insert_pt] + to_insert + instrs[insert_pt:]
    return instrs

def preprocess_trace(trace, guard_label_name):
    assert 'label' in trace[0] and 'label' in trace[-1]
    processed_trace = []
    for i in range(len(trace)):
        instr = trace[i]
        if 'label' in instr:
            continue
        if 'op' in instr:
            if instr['op'] == 'jmp':
                continue
            if instr['op'] == 'br':
                assert 'label' in trace[i+1] and trace[i+1]['label'] in instr['labels']
                if trace[i+1]['label'] == instr['labels'][0]:
                    processed_trace.append(
                        {'op': 'guard', 'args': instr['args'], 'labels':[guard_label_name]}
                    )
                else:
                    cond = instr['args'][0]
                    inverted_cond = cond+'_TRACE_INVERTED__'
                    processed_trace.append(
                        {'type': 'bool', 'dest': inverted_cond, 'op': 'not', 'args': [cond]}
                    )
                    processed_trace.append(
                        {'op': 'guard', 'args': [inverted_cond], 'labels':[guard_label_name]}
                    )
                continue
            if instr['op'] == 'div':
                zero = '__TRACE_CONST_ZERO__'
                zero_cond = '__TRACE_ZERO_COND__'
                nonzero_cond = '__TRACE_NONZERO_COND__'
                processed_trace.extend([
                    {'type': 'int', 'dest': zero, 'op': 'const', 'value': 0},
                    {'type': 'bool', 'dest': zero_cond, 'op': 'eq', 'args': [instr['args'][1], zero]},
                    {'type': 'bool', 'dest': nonzero_cond, 'op': 'not', 'args': [zero_cond]}
                ])
                processed_trace.append(
                    {'op': 'guard', 'args': [nonzero_cond], 'labels':[guard_label_name]}
                )
                processed_trace.append(instr)
                continue
            assert instr['op'] != 'call'
            processed_trace.append(instr)
    return trace[0]['label'], trace[-1]['label'], processed_trace


if __name__ == "__main__":
    full_bril = json.load(sys.stdin)
    with open(sys.argv[1]) as f:
        lines = f.readlines()
    assert lines[0][:4] == 'FUNC', lines[0]
    func_name = lines[0][5:].strip()
    trace = [json.loads(l) for l in lines[1:]]

    guard_label = '_TRACING_FAILED__'
    for i in range(len(full_bril['functions'])):
        if full_bril['functions'][i]['name'] == func_name:
            full_bril['functions'][i]['instrs'] = insert_trace(
                full_bril['functions'][i]['instrs'],
                *preprocess_trace(trace, guard_label),
                guard_label
            )
    print(json.dumps(full_bril))
