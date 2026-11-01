"""Explicit execution plans for Compiler 1.0's otherwise unbound repetition.

Plans are host proposals, challenged against the immutable contract. They are
never inferred from document order, node names, prose similarity or source text.
"""
import copy
from .io import require


class IterationPlans:
    def bind_iteration(self, control_id, task_refs, basis):
        record = {'binding_version': '1.0', 'control_id': control_id,
                  'task_refs': list(task_refs), 'basis': basis}
        self._bind_iteration(record)
        self._record('iteration_binding', record)

    def _bind_iteration(self, r):
        require(self.lifecycle in {'RUNNING', 'RUN_HELD'} and not self.executions
                and not self.pending, 'Bind iteration before task execution')
        c = self.index.get(r['control_id'], {})
        require(c in self.ir['iteration_controls'] and c['mode'] in
                {'BOUNDED_COUNT', 'UNTIL_CONDITION'}, 'Not a repeated control')
        require(c['mode'] != 'BOUNDED_COUNT' or 1 <= c['count'] <= 100,
                'Only positive bounded counts within the 100-round resource cap are executable')
        require(r['binding_version'] == '1.0' and isinstance(r['basis'], str)
                and r['basis'].strip(), 'Explicit binding justification required')
        refs = r['task_refs']
        require(refs and len(refs) == len(set(refs)) and set(refs) <= self.task_ids,
                'Explicit nonempty unique task body required')
        require(r['control_id'] not in self.iteration_bindings, 'Binding is immutable')
        require(all(self.index[t]['scope_ref'] == 'GLOBAL' for t in refs),
                'Branch-local repeated bodies require a richer interface')
        require(not any(set(refs) & set(b['task_refs']) for b in self.iteration_bindings.values()),
                'Overlapping/nested repeated bodies unsupported')
        # A dependent cannot be outside the body and then feed back into it.
        outside = {t for t in self.task_ids - set(refs)
                   if self.prerequisites(t) & set(refs)}
        require(not any(self.prerequisites(t) & outside for t in refs),
                'Iteration body is not dependency-convex')
        self.pending = {'kind': 'iteration_binding', 'response': copy.deepcopy(r)}
        self._issued = None
        self.lifecycle, self.hold_reason = 'RUNNING', None

    def _repeat_action(self):
        """Advance only reviewed body receipts; return (handled, packet)."""
        for c in self.ir['iteration_controls']:
            cid = c['id']
            if cid not in self.iteration_bindings or cid not in self.controls:
                continue
            progress = self.iteration_progress[cid]
            if progress['done']:
                continue
            refs = self.iteration_bindings[cid]['task_refs']
            if not all(t in self.receipts for t in refs):
                continue
            if len(progress['rounds']) < progress['round']:
                progress['rounds'].append({t: copy.deepcopy(self.receipts[t]) for t in refs})
            if c['mode'] == 'UNTIL_CONDITION':
                return True, self._packet('control', {'control': c, 'context': self.context(),
                    'completed_round': progress['round'], 'body_receipts': progress['rounds'][-1]})
            if progress['round'] >= c['count']:
                progress['done'] = True
            else:
                self._next_round(cid)
        return False, None

    def _next_round(self, cid):
        p = self.iteration_progress[cid]
        require(p['round'] < 100, 'Iteration resource cap: preserve checkpoint; no forced stop success')
        p['round'] += 1
        for t in self.iteration_bindings[cid]['task_refs']:
            self.receipts.pop(t, None)
            self.tasks[t] = 'PENDING'

    def _iteration_allows(self, tid):
        for cid, b in self.iteration_bindings.items():
            p = self.iteration_progress.get(cid)
            if not p or not p['done']:
                if tid not in b['task_refs'] and self.prerequisites(tid) & set(b['task_refs']):
                    return False
        return True

    def all_task_receipts(self):
        return list(self.receipts.values()) + [r for p in self.iteration_progress.values()
                    for round_ in p['rounds'] for r in round_.values()]
