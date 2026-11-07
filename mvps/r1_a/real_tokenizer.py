"""R1-A — REAL tokenizer validation via tiktoken (R2-05).

This module is the only place in R1-A that counts tokens with a REAL
tokenizer. ``validator.count_tokens_for_model`` / ``count_tokens_gpt4``
remain deterministic APPROXIMATIONS (same counter for every non-OpenAI
model name) and must never be presented as real tokenizers.

What is real here
-----------------
``tiktoken`` ships the actual BPE merge tables for OpenAI models, so
``count_tokens_real`` returns the true token count for a named OpenAI
model — no approximation, no fixture. The substitution check
(``validate_token_count_real``) therefore detects a REAL default
substitution: a count that matches the GPT-4 (cl100k_base) tokenizer
while differing from the named model's own real tokenizer by more than
the PRD's 2% tolerance.

What is NOT real here
---------------------
* Only OpenAI models have a tiktoken encoding. For any other model
  (e.g. ``litellm/qwen3-coder-30b`` from AgentLab #340) there is NO real
  tokenizer in this module: ``count_tokens_real`` returns ``None`` and
  ``validate_token_count_real`` raises ``ValueError``. The #340 Qwen
  substitution is still only demonstrated with the approximation in
  ``validator.py`` — that claim stays NOT_REAL_WORLD_VALIDATED.
* Substitution is only DETECTABLE where the two real encodings differ
  by more than 2% on the text. Measured on the #340 fixture texts
  (tiktoken 0.14.0, 2026-11-06): Chinese cl100k 51 vs o200k 34 (+50%),
  Japanese 54 vs 43 (+25.6%) — detectable; English 19 vs 19 and code
  13 vs 13 — identical, so a GPT-4 count reported for gpt-4o on those
  texts is indistinguishable from the correct count. The tests assert
  exactly that.
* The encoding tables are downloaded from OpenAI's public blob store
  the first time ``tiktoken.get_encoding`` runs (cached under
  ``TIKTOKEN_CACHE_DIR`` / ``~/.cache``). Without network on first run
  the real path is unavailable; the tests skip with a clear reason
  instead of failing or faking a count.

Versions used for the R2-05 measurements: tiktoken 0.14.0, Python 3.12.3.
"""

# Model name -> tiktoken encoding name. Only models whose encoding is
# documented by tiktoken are listed; anything else has no real tokenizer.
REAL_ENCODINGS = {
    "gpt-4": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4-32k": "cl100k_base",
    "gpt-3.5-turbo": "cl100k_base",
    "gpt-3.5-turbo-16k": "cl100k_base",
    "text-embedding-ada-002": "cl100k_base",
    "gpt-4o": "o200k_base",
    "gpt-4o-mini": "o200k_base",
    "gpt-4.1": "o200k_base",
    "text-davinci-003": "p50k_base",
    "code-davinci-002": "p50k_base",
}

# The tokenizer AgentLab #340 silently substituted (GPT-4's cl100k_base).
SUBSTITUTED_ENCODING = "cl100k_base"

TOKEN_TOLERANCE = 0.02  # PRD acceptance test 1: within 2% of the true tokenizer

_cache: dict[str, object] = {}


def real_tokenizer_available() -> bool:
    """True iff tiktoken imports (the encoding tables may still need a download)."""
    try:
        import tiktoken  # noqa: F401
    except ImportError:
        return False
    return True


def _encoding(name: str):
    if name not in _cache:
        import tiktoken

        _cache[name] = tiktoken.get_encoding(name)
    return _cache[name]


def count_tokens_real(text: str, model: str) -> int | None:
    """Real token count for a named OpenAI model, or None if unknown.

    Returns None (never an approximation) when tiktoken is not installed
    or the model has no known tiktoken encoding.
    """
    if not real_tokenizer_available():
        return None
    encoding_name = REAL_ENCODINGS.get(model)
    if encoding_name is None:
        return None
    return len(_encoding(encoding_name).encode(text))


def count_tokens_encoding(text: str, encoding_name: str) -> int | None:
    """Real token count under a named tiktoken encoding, or None if unavailable."""
    if not real_tokenizer_available():
        return None
    return len(_encoding(encoding_name).encode(text))


def validate_token_count_real(
    text: str, model: str, reported: int, substituted_encoding: str = SUBSTITUTED_ENCODING,
) -> dict:
    """Check a reported count against the named model's REAL tokenizer.

    Raises ValueError if the model has no real tokenizer (callers must
    not fall back to the approximation silently). If the named model's
    own encoding IS the substituted one, substitution cannot be
    distinguished and the detail says so.
    """
    if not real_tokenizer_available():
        raise ValueError("tiktoken is not installed: no real tokenizer available")
    if model not in REAL_ENCODINGS:
        raise ValueError(f"no real tokenizer for model {model!r} (not an OpenAI model)")
    true = count_tokens_real(text, model)
    substituted = count_tokens_encoding(text, substituted_encoding)
    rel_true = abs(reported - true) / true if true else 1.0
    rel_sub = abs(reported - substituted) / substituted if substituted else 1.0
    if rel_true <= TOKEN_TOLERANCE:
        return {
            "outcome": "ok", "passed": True, "true_count": true,
            "substituted_count": substituted, "reported": reported,
            "detail": f"reported {reported} matches the real {model} tokenizer ({true})",
        }
    if substituted_encoding != REAL_ENCODINGS[model] and rel_sub <= TOKEN_TOLERANCE \
            and rel_true > TOKEN_TOLERANCE:
        return {
            "outcome": "default-substituted", "passed": False, "true_count": true,
            "substituted_count": substituted, "reported": reported,
            "detail": (
                f"reported {reported} matches the real {substituted_encoding} "
                f"tokenizer ({substituted}), not {model} ({true}): "
                f"overcount {(substituted - true) / true:+.1%}"
            ),
        }
    return {
        "outcome": "wrong-result", "passed": False, "true_count": true,
        "substituted_count": substituted, "reported": reported,
        "detail": (
            f"reported {reported} matches neither the real {model} tokenizer "
            f"({true}) nor {substituted_encoding} ({substituted})"
        ),
    }
