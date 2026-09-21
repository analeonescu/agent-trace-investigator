"""Optional Inspect AI bridge.

This stays intentionally thin: the forensic pipeline owns parsing and candidate
selection; Inspect AI can be used to evaluate/judge the compact evidence packets.
"""


def make_task():
    try:
        from inspect_ai import Task, task
        from inspect_ai.dataset import Sample
        from inspect_ai.solver import generate
        from inspect_ai.scorer import model_graded_qa
    except ImportError as e:
        raise RuntimeError("Install with: pip install -e '.[inspect]'") from e

    @task
    def evidence_review():
        return Task(
            dataset=[],
            solver=generate(),
            scorer=model_graded_qa(),
        )
    return evidence_review
