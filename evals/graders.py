import re

from evals.types import Case, Run, Verdict


def numbers_in(text: str) -> list[float]:
    t = text.replace("\u00a0", " ")
    t = re.sub(r"(?<=\d)[ ,.](?=\d{3}(?!\d))", "", t)   # thousands separators
    t = re.sub(r"(?<=\d),(?=\d)", ".", t)               # decimal comma
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", t)]


def number(expected: float):
    def check(run: Run, case: Case) -> Verdict:
        found = numbers_in(run.reply)
        ok = any(abs(n - expected) < 0.01 for n in found)
        return Verdict(ok, "" if ok else f"expected {expected}, reply numbers: {found}")
    return check


def tool(name: str):
    def check(run: Run, case: Case) -> Verdict:
        used = [c["name"] for c in run.tool_calls]
        return Verdict(name in used, "" if name in used else f"expected {name}, used {used}")
    return check


def no_tool():
    def check(run: Run, case: Case) -> Verdict:
        return Verdict(not run.tool_calls, f"unexpected tool calls: {run.tool_calls}")
    return check


def mentions(*words: str):
    def check(run: Run, case: Case) -> Verdict:
        ok = all(w.lower() in run.reply.lower() for w in words)
        return Verdict(ok, "" if ok else f"missing words from {words}")
    return check


def says_nothing_found():
    """Empty result: must say so, and must not invent a positive amount."""
    phrases = ("no transactions", "nothing", "did not find", "didn't find", "no data",
               "žádn", "nenašel")
    def check(run: Run, case: Case) -> Verdict:
        said = any(p in run.reply.lower() for p in phrases)
        invented = [n for n in numbers_in(run.reply) if n >= 1 and not _is_date_like(n)]
        return Verdict(said and not invented, f"said={said}, suspicious numbers={invented}")
    return check


def _is_date_like(n: float) -> bool:
    return n == int(n) and (1 <= n <= 31 or 2000 <= n <= 2100)


def grounded():
    """Every number in the reply must come from a tool result (or the question itself)."""
    def check(run: Run, case: Case) -> Verdict:
        allowed = set()
        for text in [*run.tool_outputs, *case.questions]:
            allowed.update(round(n, 2) for n in numbers_in(text))
        ungrounded = [n for n in numbers_in(run.reply)
                      if round(n, 2) not in allowed and not _is_date_like(n)]
        return Verdict(not ungrounded, f"numbers not in any tool output: {ungrounded}")
    return check