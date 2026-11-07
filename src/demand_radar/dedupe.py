"""Dedupe suggestions only — never silently merge/delete."""
from rapidfuzz.fuzz import token_sort_ratio


def suggest_merge(job_a: str, blocker_a: str, job_b: str, blocker_b: str, threshold: int = 90) -> bool:
    return token_sort_ratio(f"{job_a} {blocker_a}", f"{job_b} {blocker_b}") >= threshold
