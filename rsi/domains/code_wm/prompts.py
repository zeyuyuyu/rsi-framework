"""CRUXEval-format prompts and answer parsing for execution prediction.

The output/input CoT prompts follow the CRUXEval paper's released format
([PYTHON] ... [THOUGHT] ... [ANSWER] assert ... [/ANSWER]). Generation starts
right after "[THOUGHT]\n" and stops at "[/ANSWER]".
"""

import ast

OUTPUT_COT = '''You are given a Python function and an assertion containing an input to the function. Complete the assertion with a literal (no unsimplified expressions, no function calls) containing the output when executing the provided code on the given input, even if the function is incorrect or incomplete. Do NOT output any extra information. Execute the program step by step before arriving at an answer, and provide the full assertion with the correct output in [ANSWER] and [/ANSWER] tags, following the examples.

[PYTHON]
def f(s):
    s = s + s
    return "b" + s + "a"
assert f("hi") == ??
[/PYTHON]
[THOUGHT]
Let's execute the code step by step:

1. The function f is defined, which takes a single argument s.
2. The function is called with the argument "hi", so within the function, s is initially "hi".
3. Inside the function, s is concatenated with itself, so s becomes "hihi".
4. The function then returns a new string that starts with "b", followed by the value of s (which is now "hihi"), and ends with "a".
5. The return value of the function is therefore "bhihia".
[/THOUGHT]
[ANSWER]
assert f("hi") == "bhihia"
[/ANSWER]

[PYTHON]
{code}
assert {call} == ??
[/PYTHON]
[THOUGHT]
'''

INPUT_COT = '''You will be given a function f and an output in the form f(??) == output. Your task is to find any input such that executing f on the input leads to the given output. There may be multiple answers, but only output one. First, think step by step. You MUST surround the answer with [ANSWER] and [/ANSWER] tags. Express your answer as a passing assertion containing the input and the given output.

[PYTHON]
def f(x):
    return x + 1
assert f(??) == 17
[/PYTHON]
[THOUGHT]
To find an input such that executing f on the input leads to the given output, we can work backwards from the given assertion. We know that f(??) == 17.

Since the function f(x) returns x + 1, for f(??) to be equal to 17, the value of ?? should be 16.
[/THOUGHT]
[ANSWER]
assert f(16) == 17
[/ANSWER]

[PYTHON]
{code}
assert f(??) == {output}
[/PYTHON]
[THOUGHT]
'''

PROPOSE_INSTRUCTION = ("Below are short Python functions, each followed by an assertion with a concrete "
    "input. Write one NEW function in exactly the same format. Requirements: the function is named f, is 3 to "
    "15 lines long, uses only built-in types and operations (strings, lists, dicts, sets, tuples, integers, "
    "booleans), has no imports, does no printing, file access or randomness, and always terminates quickly. "
    "Make it different from the examples and non-trivial: predicting its output for the given input should "
    "require carefully tracing loops, conditionals, indexing, or string/list/dict methods.")


def propose_prompt(instruction, examples):
    return f"{instruction}\n\n{examples}\n[PYTHON]\n"

STOP_ANSWER = ["[/ANSWER]"]
STOP_PYTHON = ["[/PYTHON]"]


def fill(template, **values):
    """str.format would choke on braces inside code; substitute fields literally."""
    for key, value in values.items():
        template = template.replace("{" + key + "}", value)
    return template


def example_block(code, args):
    return f"[PYTHON]\n{code}\nassert f({args}) == ??\n[/PYTHON]\n"


def _answer_section(text):
    if "[ANSWER]" not in text:
        return None
    body = text.split("[ANSWER]")[-1]
    return body.split("[/ANSWER]")[0].strip()


def _assert_compare(section):
    """Return the Compare node of 'assert X == Y' (first assert line), or None."""
    if section is None:
        return None, None
    line = next((l.strip() for l in section.splitlines() if l.strip().startswith("assert")),
                section.strip())
    try:
        tree = ast.parse(line)
    except SyntaxError:
        return None, line
    node = tree.body[0] if tree.body else None
    if (isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare)
            and len(node.test.ops) == 1 and isinstance(node.test.ops[0], ast.Eq)):
        return node.test, line
    return None, line


def parse_output_answer(text):
    """Literal source of the predicted output, or None if unparseable."""
    compare, line = _assert_compare(_answer_section(text))
    if compare is not None:
        return ast.get_source_segment(line, compare.comparators[0])
    if line and "==" in line:
        return line.split("==", 1)[1].strip()
    return None


def parse_input_answer(text):
    """Literal source of the predicted positional arguments, or None."""
    compare, line = _assert_compare(_answer_section(text))
    if compare is None or not isinstance(compare.left, ast.Call) or compare.left.keywords:
        return None
    return ", ".join(ast.get_source_segment(line, a) for a in compare.left.args)


def parse_proposal(text):
    """Split a generated '[PYTHON] code + assert f(args) == ?? [/PYTHON]' block."""
    body = text.split("[/PYTHON]")[0].rstrip()
    lines = body.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines or not lines[-1].strip().startswith("assert f("):
        return None
    last = lines[-1].strip()
    code = "\n".join(lines[:-1]).rstrip()
    if not last.endswith("== ??"):
        return None
    call = last[len("assert "):-len("== ??")].strip()
    try:
        node = ast.parse(call).body[0].value
    except (SyntaxError, IndexError, AttributeError):
        return None
    if not isinstance(node, ast.Call) or node.keywords or not node.args:
        return None
    args = ", ".join(ast.get_source_segment(call, a) for a in node.args)
    return code, args
