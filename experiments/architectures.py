"""E3 encodings of published multi-agent designs (one round; loops unrolled once).

Encoding protocol (Section 4.3 of the paper):
 P1 each documented role or pipeline stage is a node; a step the paper describes as a
    program (test execution, compilation, sample-I/O check) is a deterministic gate;
    every LLM role is an agent whose oracle is the backbone model used in the paper's
    main configuration (one shared backbone unless the design uses several models);
 P2 edges follow the documented hand-off order; parallel roles fork; aggregation steps
    are joins with the documented policy (concatenate/synthesize = all, majority = quorum,
    first/selected candidate = any); a manager that picks the next speaker is a switch;
 P3 a role guarantees the artifact it produces; it requires the artifacts it consumes;
    goals are the quality claims the design's evaluation relies on; the claim resting on
    executed tests is critical (fault budget f = 1: one oracle may fail per run);
 P4 iterative loops are unrolled once (bounded unrolling).
Contracts are declared by us from public descriptions; they are not measured behaviour.
"""
from slicing.model import build

DESIGNS = {}


def design(key, source, note):
    def deco(fn):
        DESIGNS[key] = {'build': fn, 'source': source, 'note': note}
        return fn
    return deco


@design('MetaGPT', 'hong2024metagpt', 'PM -> Architect -> ProjectMgr -> Engineer -> QA (writes tests) -> test run')
def metagpt(o):
    return build([('PM', 'agent', [], ['prd'], o('PM')), ('Architect', 'agent', ['prd'], ['design'], o('Architect')),
                  ('ProjMgr', 'agent', ['design'], ['tasks'], o('ProjMgr')),
                  ('Engineer', 'agent', ['tasks', 'design'], ['code', 'implemented'], o('Engineer')),
                  ('QA', 'agent', ['code'], ['unit_tests'], o('QA')), ('TestRun', 'gate', ['unit_tests', 'code'], ['tests_pass'])],
                 [('IN', 'PM'), ('PM', 'Architect'), ('Architect', 'ProjMgr'), ('ProjMgr', 'Engineer'), ('Engineer', 'QA'),
                  ('QA', 'TestRun'), ('TestRun', 'OUT')], goals=['implemented', 'tests_pass'], critical=['tests_pass'], f=1)


@design('ChatDev', 'qian2024chatdev', 'design -> coding -> code complete -> review -> execution -> testing')
def chatdev(o):
    return build([('Design', 'agent', [], ['spec'], o('Design')), ('Coding', 'agent', ['spec'], ['code'], o('Coding')),
                  ('Complete', 'agent', ['code'], ['code_complete'], o('Complete')),
                  ('Review', 'agent', ['code'], ['reviewed'], o('Review')), ('Execute', 'gate', ['code'], ['runs']),
                  ('Testing', 'agent', ['runs'], ['correct'], o('Testing'))],
                 [('IN', 'Design'), ('Design', 'Coding'), ('Coding', 'Complete'), ('Complete', 'Review'), ('Review', 'Execute'),
                  ('Execute', 'Testing'), ('Testing', 'OUT')], goals=['code_complete', 'runs', 'reviewed', 'correct'], critical=['correct'], f=1)


@design('AgentCoder', 'huang2023agentcoder', 'programmer || test designer -> test executor (script)')
def agentcoder(o, join='all'):
    return build([('Programmer', 'agent', [], ['code'], o('Programmer')), ('TestDesigner', 'agent', [], ['tests'], o('TestDesigner')),
                  ('Executor', 'gate', ['tests', 'code'], ['tests_pass'], None, 'fork', join)],
                 [('IN', 'Programmer'), ('IN', 'TestDesigner'), ('Programmer', 'Executor'), ('TestDesigner', 'Executor'),
                  ('Executor', 'OUT')], goals=['tests_pass'], critical=['tests_pass'], f=1)


@design('MapCoder', 'islam2024mapcoder', 'retrieval -> planning -> coding -> sample I/O check (from the problem statement) -> debugging')
def mapcoder(o):
    return build([('Retrieval', 'agent', [], ['examples'], o('Retrieval')), ('Planning', 'agent', ['examples'], ['plan'], o('Planning')),
                  ('Coding', 'agent', ['plan'], ['code'], o('Coding')), ('SampleIO', 'gate', ['code'], ['samples_pass']),
                  ('Debugging', 'agent', ['code'], ['debugged'], o('Debugging'))],
                 [('IN', 'Retrieval'), ('Retrieval', 'Planning'), ('Planning', 'Coding'), ('Coding', 'SampleIO'),
                  ('SampleIO', 'Debugging'), ('Debugging', 'OUT')], goals=['samples_pass', 'debugged'], critical=['samples_pass'], f=1)


@design('SelfCollab', 'dong2024selfcollab', 'analyst -> coder -> tester (LLM-simulated testing)')
def selfcollab(o):
    return build([('Analyst', 'agent', [], ['analysis'], o('Analyst')), ('Coder', 'agent', ['analysis'], ['code'], o('Coder')),
                  ('Tester', 'agent', ['code'], ['tested'], o('Tester'))],
                 [('IN', 'Analyst'), ('Analyst', 'Coder'), ('Coder', 'Tester'), ('Tester', 'OUT')],
                 goals=['tested'], critical=['tested'], f=1)


@design('Debate', 'du2024debate', 'three agents answer, then each revises after reading all answers (one debate round) -> majority vote')
def debate(o, join=2):
    r1 = [(f'A{i}', 'agent', [], [f'ans{i}'], o(f'A{i}')) for i in range(1, 4)]
    r2 = [(f'R{i}', 'agent', ['ans1', 'ans2', 'ans3'], ['answer_ok'], o(f'R{i}')) for i in range(1, 4)]
    edges = [('IN', f'A{i}') for i in range(1, 4)] + [(f'A{i}', f'R{j}') for i in range(1, 4) for j in range(1, 4)] + \
            [(f'R{i}', 'Vote') for i in range(1, 4)] + [('Vote', 'OUT')]
    return build(r1 + r2 + [('Vote', 'gate', [], [], None, 'fork', join)], edges, goals=['answer_ok'], critical=['answer_ok'], f=1)


@design('MoA', 'wang2024moa', 'two proposer layers (different LLMs) -> aggregator')
def moa(o, join='all'):
    nodes = [(f'P{i}', 'agent', [], [f'cand{i}'], o(f'P{i}', f'llm{i}')) for i in range(3)]
    nodes += [(f'Q{i}', 'agent', ['cand0', 'cand1', 'cand2'], [f'refined{i}'], o(f'Q{i}', f'llm{i}'), 'fork', join) for i in range(3)]
    nodes += [('Aggregator', 'agent', ['refined0', 'refined1', 'refined2'], ['answer_ok'], o('Aggregator', 'llm0'), 'fork', join)]
    edges = [('IN', f'P{i}') for i in range(3)] + [(f'P{i}', f'Q{j}') for i in range(3) for j in range(3)] + \
            [(f'Q{i}', 'Aggregator') for i in range(3)] + [('Aggregator', 'OUT')]
    return build(nodes, edges, goals=['answer_ok'], critical=['answer_ok'], f=1)


@design('AutoGenGroup', 'wu2024autogen', 'manager selects coder or critic -> merge -> code executor')
def autogen(o):
    return build([('Manager', 'agent', [], ['task'], o('Manager'), 'switch'), ('Coder', 'agent', ['task'], ['code'], o('Coder')),
                  ('Critic', 'agent', ['task'], ['reviewed'], o('Critic')), ('Merge', 'gate', [], [], None, 'fork', 'any'),
                  ('Executor', 'gate', ['code'], ['runs'])],
                 [('IN', 'Manager'), ('Manager', 'Coder'), ('Manager', 'Critic'), ('Coder', 'Merge'), ('Critic', 'Merge'),
                  ('Merge', 'Executor'), ('Executor', 'OUT')], goals=['runs', 'reviewed'], critical=['runs'], f=1)


@design('Agentless', 'xia2025agentless', 'localize -> sampled repairs; reproduction-test generation; each candidate validated by regression and reproduction runs -> select')
def agentless(o, join='any'):
    return build([('Localize', 'agent', [], ['locations'], o('Localize')),
                  ('Repair1', 'agent', ['locations'], ['patch'], o('Repair1')), ('Repair2', 'agent', ['locations'], ['patch'], o('Repair2')),
                  ('ReproGen', 'agent', [], ['repro_test'], o('ReproGen')),
                  ('Validate1', 'gate', ['patch', 'repro_test'], ['regression_pass', 'issue_fixed']),
                  ('Validate2', 'gate', ['patch', 'repro_test'], ['regression_pass', 'issue_fixed']),
                  ('Select', 'gate', [], [], None, 'fork', join)],
                 [('IN', 'Localize'), ('IN', 'ReproGen'), ('Localize', 'Repair1'), ('Localize', 'Repair2'),
                  ('Repair1', 'Validate1'), ('ReproGen', 'Validate1'), ('Repair2', 'Validate2'), ('ReproGen', 'Validate2'),
                  ('Validate1', 'Select'), ('Validate2', 'Select'), ('Select', 'OUT')],
                 goals=['regression_pass', 'issue_fixed'], critical=['issue_fixed'], f=1)
