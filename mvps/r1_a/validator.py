"""R1-A — fault-injection validator for AI agent / API reliability.

PRD 6513d051954cbe1b5027 (AI: drive an AI agent / API reliably).
This is NOT an issue list viewer. It runs recorded/realistic API call traces
through a simulated transport that injects faults locally (no network, no
paid calls, deterministic virtual clock) and classifies every outcome:
ok / timeout / rate-limited / server-error / wrong-result /
default-substituted / token-budget.

Recorded reproducers used as fixtures:
- AgentLab #340: count_tokens() silently substitutes the GPT-4 tokenizer for
  every non-bare-OpenAI model name; measured error 0% code, +11.7% English,
  +18.5% Japanese, +108.3% Chinese. The two tokenizers below are small
  deterministic approximations of that behaviour (CJK ideograph 2 tokens
  under GPT-4 vs 1 under the named model; long English words split in two
  under GPT-4 only; code identical) — they reproduce the *direction and
  magnitude* of the reported error, they are NOT the real tokenizers.
  The validator's job is to DETECT the substitution, not to tokenize.
- LangChain #41708: Responses API streaming never emits a completed event
  for function_call (closed not_planned; same bug still open as #41710).
  The recorded event sequences in data/fixtures.json are replayed through
  the REAL StreamingHandler (tests/test_real_paths.py) — no simulated
  transport is involved in the streaming path.
- AgentLab #182: 60s pause per missed attempt, ~16 min worst case per step.
- HN #50382039: an OpenRouter response that is false or errors after a long
  wait must be classified, never returned as a normal result. Factual
  correctness is judged by CONTENT comparison against a known-good
  expected answer supplied in the fixture (see check_factual_content),
  never by trusting a factual=False flag in the payload — the flag was
  removed in R2-05 because it let the transport grade its own homework.
- Tokenizers: the two counters in this file are small deterministic
  approximations (see below). REAL tokenizer validation lives in
  real_tokenizer.py (tiktoken): it detects a real default substitution
  for OpenAI models (gpt-4o vs cl100k_base), and raises for any model
  with no real tokenizer instead of silently approximating.
"""

import csv
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path

OUTCOMES = (
    "ok",
    "timeout",
    "rate-limited",
    "server-error",
    "wrong-result",
    "default-substituted",
    "token-budget",
)

# "server-error" (HTTP 500) and "token-budget" extend the five outcomes named
# in the R06 brief, because a 500 is neither a wrong result nor a timeout,
# and a token-budget failure must not be lumped in with wrong results.

PER_ATTEMPT_WAIT_MS = 60_000  # AgentLab #182: 60s pause per missed attempt
MAX_ATTEMPTS = 3
TOKEN_TOLERANCE = 0.02  # PRD acceptance test 1: within 2% of the true tokenizer

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_KANA_RE = re.compile(r"[\u3040-\u30ff]")
_CODE_MARKERS = ("def ", "import ", "class ", "{", "}", "return ")


class SimulatedFault(Exception):
    """A fault injected by the simulated transport (local, no network)."""

    def __init__(self, kind: str):
        super().__init__(kind)
        self.kind = kind


@dataclass
class CallResult:
    scenario: str
    kind: str
    step: str
    outcome: str
    passed: bool
    attempts: int
    elapsed_ms: int
    source_url: str
    detail: str
    # P2-A (sixth-round audit): request-level completion. Streaming rows
    # fill all three from ``validate_stream``; non-streaming rows fill the
    # last two via ``_request_completion`` and leave ``termination`` empty
    # (not a stream). ``request_completed_successfully`` is the field the
    # UI counts as "passed"; ``request_status`` is "completed" /
    # "pending" / "failed" / "not-checked".
    termination: str = ""
    request_completed_successfully: bool = False
    request_status: str = ""


# ---------------------------------------------------------------------------
# Tokenizers (deterministic approximations — see module docstring)
# ---------------------------------------------------------------------------


def _looks_like_code(text: str) -> bool:
    return any(m in text for m in _CODE_MARKERS)


def _count_code(text: str) -> int:
    return len([t for t in re.split(r"[^A-Za-z0-9_]+", text) if t])


def _count_text(text: str, gpt4: bool) -> int:
    total, i = 0, 0
    while i < len(text):
        ch = text[i]
        if ch.isspace():
            i += 1
        elif _CJK_RE.match(ch):
            total += 2 if gpt4 else 1
            i += 1
        elif _KANA_RE.match(ch):
            total += 1
            i += 1
        elif ch.isascii() and ch.isalpha():
            j = i
            while j < len(text) and text[j].isascii() and text[j].isalpha():
                j += 1
            word = text[i:j]
            total += 2 if (gpt4 and len(word) > 6) else 1
            i = j
        else:
            total += 1
            i += 1
    return total


def count_tokens_gpt4(text: str) -> int:
    """Approximation of the GPT-4 tokenizer's count (the substituted one)."""
    return _count_code(text) if _looks_like_code(text) else _count_text(text, True)


def count_tokens_for_model(text: str, model: str) -> int:
    """Approximation of the named model's own tokenizer count.

    `model` is accepted (and recorded) but the counter is the same for
    every non-OpenAI model name: the point under test is whether the
    caller used the GPT-4 counter instead of this one. This is an
    APPROXIMATION, not a real tokenizer — it is model-aware only in
    name. Real tokenizer validation (actual tiktoken counts, real
    substitution detection, and a hard error for models with no real
    tokenizer) lives in real_tokenizer.py (R2-05).
    """
    _ = model
    return _count_code(text) if _looks_like_code(text) else _count_text(text, False)


def overcount_pct(text: str) -> float:
    """(gpt4 - true) / true, as a fraction — the #340 error measure."""
    true = count_tokens_for_model(text, "litellm/qwen3-coder-30b")
    gpt4 = count_tokens_gpt4(text)
    return (gpt4 - true) / true if true else 0.0


def validate_token_count(text: str, model: str, reported: int) -> dict:
    """Check a reported token count against the named model's tokenizer.

    Returns outcome ok / default-substituted / wrong-result with the measured
    counts. A count that matches the GPT-4 counter (within 2%) while differing
    from the true counter by more than 2% is a silent default substitution
    (AgentLab #340), not a rounding error.
    """
    true = count_tokens_for_model(text, model)
    gpt4 = count_tokens_gpt4(text)
    rel_true = abs(reported - true) / true if true else 1.0
    rel_gpt4 = abs(reported - gpt4) / gpt4 if gpt4 else 1.0
    if rel_true <= TOKEN_TOLERANCE:
        outcome, passed = "ok", True
        detail = f"reported {reported} matches {model} tokenizer ({true})"
    elif rel_gpt4 <= TOKEN_TOLERANCE and rel_true > TOKEN_TOLERANCE:
        outcome, passed = "default-substituted", False
        detail = (
            f"reported {reported} matches GPT-4 tokenizer ({gpt4}), not "
            f"{model} ({true}): overcount {overcount_pct(text):.1%}"
        )
    else:
        outcome, passed = "wrong-result", False
        detail = f"reported {reported} matches neither {model} ({true}) nor GPT-4 ({gpt4})"
    return {
        "outcome": outcome,
        "passed": passed,
        "true_count": true,
        "gpt4_count": gpt4,
        "reported": reported,
        "detail": detail,
    }


# ---------------------------------------------------------------------------
# Strict JSON parsing (REWORK4 fix, audit P1-A)
# ---------------------------------------------------------------------------


def _reject_nonstandard_constant(name: str):
    """parse_constant hook: NaN / Infinity / -Infinity are not JSON.

    ``json.loads`` accepts them by default; this hook makes the parse
    fail instead. It is only called for BARE constants — the string
    "NaN" inside a JSON string value is legal text and is preserved
    (no regex is used anywhere here, so string contents are untouched).
    """
    raise ValueError(f"non-standard JSON constant {name!r} is not valid JSON")


def _check_finite(value, path: str = "$") -> None:
    """Recursively reject non-finite floats in a parsed JSON value.

    ``json.loads('1e999')`` succeeds and yields ``inf`` — a number that
    is not valid JSON. This catches it (and nested cases) after parsing.
    Ints are finite by definition and are never checked.
    """
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite number at {path} is not valid JSON")
    elif isinstance(value, dict):
        for key, item in value.items():
            _check_finite(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_finite(item, f"{path}[{index}]")


def _parse_strict_json(text: str):
    """Parse JSON strictly. Raises ValueError on any rejection.

    Rejects the three non-standard constants (NaN, Infinity,
    -Infinity) and any non-finite float the parser produces
    (e.g. ``1e999`` -> inf), at any nesting depth. All other JSON —
    including strings that merely CONTAIN those words — parses
    normally. Every path in this module that claims a payload or
    argument string is "valid JSON" must use this function, never a
    bare ``json.loads``.
    """
    data = json.loads(text, parse_constant=_reject_nonstandard_constant)
    _check_finite(data)
    return data


# Terminal event types for a Responses API stream (POST-R4, fifth-round
# audit P1). Verified against the OpenAI Python SDK event contract
# (openai-python main, src/openai/types/responses/response_stream_event.py):
# ResponseCompletedEvent, ResponseFailedEvent, ResponseIncompleteEvent
# and ResponseErrorEvent (type "error"). A response ends with exactly
# one of these; the first one wins, and anything after it is a violation.
_TERMINAL_EVENTS = {
    "response.completed": "completed",
    "response.failed": "failed",
    "response.incomplete": "incomplete",
    "error": "error",
}
_DATA_EVENTS = (
    "response.output_item.added",
    "response.function_call_arguments.delta",
    "response.output_item.done",
)


# ---------------------------------------------------------------------------
# Streaming handler (LangChain #41708)
# ---------------------------------------------------------------------------


class StreamingHandler:
    """Responses-API streaming state machine for function_call items.

    Canonical identity (verified against the OpenAI Python SDK event
    contract — see below): the output item's ``item.id`` from
    ``response.output_item.added``. The handler keeps one mapping per
    namespace — ``item.id``, ``item.call_id`` and ``event.output_index``
    — each pointing at the canonical key, so a delta that carries both
    ``item_id`` and ``output_index`` must resolve through BOTH maps to
    the SAME call; if the two keys disagree, or name a call that was
    never added, the delta is dropped and recorded as an anomaly —
    never silently attributed to another call.

    SDK reference (fetched 2026-11-06, openai-python main):
    - ResponseFunctionCallArgumentsDeltaEvent: ``delta: str``,
      ``item_id: str`` (the ID of the output item), ``output_index: int``,
      ``sequence_number: int``.
    - ResponseOutputItemAddedEvent: ``item: ResponseOutputItem``,
      ``output_index: int``, ``sequence_number: int``.
    - The SDK's own streaming helper resolves deltas by
      ``output_index`` (``_get_output_item``) and raises on a content
      event for an unknown output index; this handler records the same
      condition as an anomaly instead of raising, because a validator
      must report bad input, not crash on it.

    A delta with NO key at all (the recorded #41708 fixtures carry
    neither item_id nor output_index) is attributed to the single
    pending call ONLY when exactly one call is pending — with one
    pending call that is unambiguous. With zero or several pending
    calls a keyless delta is ambiguous: it is dropped and recorded,
    never silently given to the most recently added call.

    Duplicate ``sequence_number`` deltas for the same call are dropped
    (recorded); a delta for a call that already completed is dropped
    and recorded as ``delta_after_done``.

    Done handling: ``response.output_item.done`` carries the final
    ``item.arguments``. When present and non-empty it is the
    authoritative arguments string and must equal the accumulated
    deltas; a mismatch, or non-JSON arguments, marks the completed
    chunk ``arguments_valid=False`` and records an anomaly. Empty
    final arguments with empty accumulated arguments is a legal
    no-argument call. A duplicate done emits once (recorded in
    ``duplicate_dones``); a done for a call never added is an orphan
    (recorded in ``orphan_dones``, no completed emitted).

    emit_on_done=False reproduces the recorded #41708 behaviour: the
    handler consumes added/delta events but never emits a completed
    chunk on done.

    Termination (REWORK4 fix, audit P2-C; extended POST-R4, fifth-round
    audit P1): a response ends with exactly ONE terminal event.
    The terminal events are ``response.completed``,
    ``response.failed``, ``response.incomplete`` and ``error``
    (verified against the OpenAI Python SDK event contract —
    openai-python main, response_stream_event.py, which lists
    ResponseCompletedEvent, ResponseFailedEvent,
    ResponseIncompleteEvent and ResponseErrorEvent; the SDK's
    websocket example treats failed/incomplete as errors, never as
    success). The handler records the first terminal event in
    ``_terminal`` (``completed`` / ``failed`` / ``incomplete`` /
    ``error``); ``failed`` / ``incomplete`` / ``error`` are failure
    terminals, NEVER an "open" stream still in progress. Any
    streaming event (added / delta / done) that arrives AFTER a
    terminal event is recorded as an anomaly (``event_after_completed``
    after ``response.completed`` — the kind name the R4 contract
    tests assert — ``event_after_terminal`` after any other terminal)
    — the response had already ended. A second terminal event that
    CONTRADICTS the first (a different kind) is a
    ``conflicting_terminal`` anomaly and fails validation; an
    identical repeat is tolerated but recorded in
    ``duplicate_terminals`` (same precedent as duplicate done
    events). ``validate_stream`` reports the stream's termination
    state (``completed`` / ``failed`` / ``incomplete`` / ``error`` /
    ``open`` / ``none``): only a normal ``completed`` with no pending
    call can pass; a failure terminal always fails; a stream with no
    terminal signal at all is reported as ``open`` (incomplete) and
    its detail says the request's success is not yet proven — never
    silently treated as finished.
    """

    def __init__(self, emit_on_done: bool = True):
        self._emit_on_done = emit_on_done
        self._pending: dict[str, dict] = {}
        # Namespace-separated identity maps: item.id / item.call_id /
        # event output_index each point at the canonical key. Keeping
        # them separate is what makes a dual-key delta checkable: both
        # keys must agree, and a key from one namespace can never be
        # mistaken for a key from another (e.g. item_id "0" vs index 0).
        self._by_id: dict[str, str] = {}
        self._by_call_id: dict[str, str] = {}
        self._by_index: dict[int, str] = {}
        self._completed: list = []
        self._completed_keys: list[str] = []
        self._done_keys: list[str] = []
        self._duplicate_dones: list[str] = []
        self._orphan_dones: list[str] = []
        self._anomalies: list[dict] = []
        self._saw_stream_events = False
        # Terminal state (POST-R4): the first terminal event's kind
        # ('completed' / 'failed' / 'incomplete' / 'error'), or None
        # while the stream is still open. _terminal_event keeps the
        # event itself so validate_stream can explain WHY the stream
        # ended (error code/message, incomplete reason).
        self._terminal: str | None = None
        self._terminal_event: dict | None = None
        self._duplicate_terminals: list[str] = []
        self._anon = 0

    def _register(self, item: dict, event: dict) -> str | None:
        """Register an added function_call; returns its canonical key.

        Canonical key: item.id, else item.call_id, else
        ``output_index:<n>`` (prefixed so an index can never collide
        with a raw id/call_id string), else an anonymous counter.
        A re-added identity, or a namespace value already bound to a
        different call, is a duplicate/conflict: recorded, not merged.
        """
        item_id = item.get("id")
        call_id = item.get("call_id")
        output_index = event.get("output_index")
        if item_id is not None and item_id != "":
            key = str(item_id)
        elif call_id is not None and call_id != "":
            key = str(call_id)
        elif output_index is not None:
            key = f"output_index:{output_index}"
        else:
            self._anon += 1
            key = f"__anon_{self._anon}"
        if key in self._pending or key in self._done_keys:
            self._anomalies.append(
                {
                    "kind": "duplicate_added",
                    "key": key,
                    "detail": f"output item {key!r} added twice",
                }
            )
            return None
        for namespace, value, mapping in (
            ("id", item_id, self._by_id),
            ("call_id", call_id, self._by_call_id),
            ("output_index", output_index, self._by_index),
        ):
            if value is None or value == "":
                continue
            bound = mapping.get(str(value) if namespace != "output_index" else value)
            if bound is not None and bound != key:
                self._anomalies.append(
                    {
                        "kind": "key_conflict",
                        "key": key,
                        "detail": (
                            f"added item {key!r} reuses {namespace} "
                            f"{value!r}, already bound to {bound!r}"
                        ),
                    }
                )
                return None
        self._pending[key] = {"item": item, "arguments": "", "seen_sequences": set()}
        if item_id is not None and item_id != "":
            self._by_id[str(item_id)] = key
        if call_id is not None and call_id != "":
            self._by_call_id[str(call_id)] = key
        if output_index is not None:
            self._by_index[output_index] = key
        return key

    def _resolve(self, item: dict | None, event: dict) -> tuple[str | None, str | None]:
        """Resolve an event to one canonical key.

        Returns ``(key, problem)``: ``key`` is the canonical key when
        the event resolves to exactly one call; ``problem`` is None on
        success, ``"unknown"`` when no key field resolves to any call,
        and ``"conflict"`` when the event's key fields disagree — either
        by resolving to different calls, or by naming a value that was
        never registered while another key field resolves to a call.
        A key field present but unregistered is itself a disagreement:
        the event claims two different identities at once.
        """
        item = item or {}
        event = event or {}
        candidates: set[str] = set()
        unresolved = False
        for namespace, value in (
            ("id", item.get("id")),
            ("call_id", item.get("call_id")),
            ("item_id", event.get("item_id")),
            ("output_index", event.get("output_index")),
        ):
            if value is None or value == "":
                continue
            if namespace in ("id", "item_id"):
                found = self._by_id.get(str(value))
            elif namespace == "call_id":
                found = self._by_call_id.get(str(value))
            else:
                found = self._by_index.get(value)
            if found is None:
                unresolved = True
            else:
                candidates.add(found)
        if not candidates:
            return None, "unknown"
        if len(candidates) > 1 or unresolved:
            return None, "conflict"
        return candidates.pop(), None

    @staticmethod
    def _has_key(event: dict) -> bool:
        return event.get("item_id") not in (None, "") or event.get("output_index") is not None

    def _handle_delta(self, event: dict) -> None:
        key, problem = self._resolve(None, event)
        if problem == "conflict":
            self._anomalies.append(
                {
                    "kind": "key_conflict",
                    "detail": (
                        "delta keys disagree: "
                        f"item_id={event.get('item_id')!r} "
                        f"output_index={event.get('output_index')!r}"
                    ),
                }
            )
            return
        if key is None:
            if not self._has_key(event) and len(self._pending) == 1:
                # Keyless delta with exactly one pending call: the
                # recorded #41708 shape. Unambiguous — no other call
                # exists to misattribute it to.
                key = next(iter(self._pending))
            else:
                kind = "unknown_delta" if self._has_key(event) else "ambiguous_delta"
                self._anomalies.append(
                    {
                        "kind": kind,
                        "detail": (
                            f"delta for unknown item: "
                            f"item_id={event.get('item_id')!r} "
                            f"output_index={event.get('output_index')!r}; "
                            f"{len(self._pending)} call(s) pending"
                        ),
                    }
                )
                return
        pending = self._pending.get(key)
        if pending is None:
            # Resolved to a call that already completed: the delta
            # arrived too late. Drop it, never re-open the call.
            self._anomalies.append(
                {
                    "kind": "delta_after_done",
                    "key": key,
                    "detail": f"delta arrived after done for call {key!r}",
                }
            )
            return
        seq = event.get("sequence_number")
        if seq is not None:
            if seq in pending["seen_sequences"]:
                self._anomalies.append(
                    {
                        "kind": "duplicate_sequence",
                        "key": key,
                        "sequence_number": seq,
                        "detail": f"delta sequence {seq} repeated for call {key!r}",
                    }
                )
                return
            pending["seen_sequences"].add(seq)
        delta = event.get("delta", "")
        if isinstance(delta, str):
            pending["arguments"] += delta

    def _handle_done(self, event: dict) -> None:
        item = event.get("item") or {}
        key, problem = self._resolve(item, event)
        if problem == "conflict":
            self._anomalies.append(
                {
                    "kind": "key_conflict",
                    "detail": (
                        "done keys disagree: "
                        f"item.id={item.get('id')!r} "
                        f"item.call_id={item.get('call_id')!r} "
                        f"output_index={event.get('output_index')!r}"
                    ),
                }
            )
            return
        if key is None:
            label = str(
                item.get("id")
                or item.get("call_id")
                or event.get("item_id")
                or event.get("output_index")
                or "?"
            )
            self._orphan_dones.append(label)
            return
        if key in self._done_keys:
            self._duplicate_dones.append(key)
            return
        if key not in self._pending:
            self._orphan_dones.append(key)
            return
        pending = self._pending.pop(key)
        self._done_keys.append(key)
        accumulated = pending["arguments"]
        final_args = item.get("arguments")
        arguments_valid = True
        if final_args is not None and final_args != "":
            # The done item's arguments are authoritative: they must be
            # valid JSON, and must equal the accumulated deltas when
            # deltas arrived. A mismatch means the stream lost or
            # corrupted arguments — the completed chunk is not valid.
            if not isinstance(final_args, str):
                arguments_valid = False
                self._anomalies.append(
                    {
                        "kind": "invalid_arguments_json",
                        "key": key,
                        "detail": f"done arguments for call {key!r} are not a string",
                    }
                )
                arguments = accumulated
            else:
                try:
                    _parse_strict_json(final_args)
                except ValueError as exc:
                    arguments_valid = False
                    self._anomalies.append(
                        {
                            "kind": "invalid_arguments_json",
                            "key": key,
                            "detail": f"done arguments for call {key!r} are not valid JSON: {exc}",
                        }
                    )
                if accumulated and accumulated != final_args:
                    arguments_valid = False
                    self._anomalies.append(
                        {
                            "kind": "arguments_mismatch",
                            "key": key,
                            "detail": (
                                f"done arguments {final_args!r} differ from "
                                f"accumulated deltas {accumulated!r} for call {key!r}"
                            ),
                        }
                    )
                arguments = final_args
        else:
            # No final arguments: the accumulated deltas stand. Empty
            # accumulated + empty final is a legal no-argument call.
            arguments = accumulated
            if accumulated:
                try:
                    _parse_strict_json(accumulated)
                except ValueError as exc:
                    arguments_valid = False
                    self._anomalies.append(
                        {
                            "kind": "invalid_arguments_json",
                            "key": key,
                            "detail": (
                                f"accumulated arguments for call {key!r} are not valid JSON: {exc}"
                            ),
                        }
                    )
        if self._emit_on_done:
            self._completed.append(
                {
                    "type": "completed",
                    "key": key,
                    "function_call": {"item": pending["item"], "arguments": arguments},
                    "arguments_valid": arguments_valid,
                }
            )
            self._completed_keys.append(key)

    def _record_terminal(self, etype: str, event: dict) -> None:
        """Record a terminal event. The first one ends the response.

        A second terminal of the SAME kind is tolerated but recorded
        (a duplicated completion is harmless — same precedent as a
        duplicate done). A second terminal of a DIFFERENT kind
        contradicts the first: a response ends exactly once, so it is
        a ``conflicting_terminal`` anomaly and fails validation.
        """
        terminal = _TERMINAL_EVENTS[etype]
        if self._terminal is None:
            self._terminal = terminal
            self._terminal_event = event
            return
        if terminal == self._terminal:
            self._duplicate_terminals.append(terminal)
            return
        self._anomalies.append(
            {
                "kind": "conflicting_terminal",
                "detail": (
                    f"response already terminated with {self._terminal!r}; "
                    f"got a second terminal event {terminal!r}"
                ),
            }
        )

    def handle(self, event: dict) -> None:
        etype = event.get("type")
        if etype in _DATA_EVENTS or etype in _TERMINAL_EVENTS:
            self._saw_stream_events = True
        if etype in _TERMINAL_EVENTS:
            # A terminal event ends the response. Anything that
            # arrives afterwards is a protocol violation, not a late
            # event — including a second terminal event.
            self._record_terminal(etype, event)
            return
        if self._terminal is not None:
            kind = (
                "event_after_completed" if self._terminal == "completed" else "event_after_terminal"
            )
            self._anomalies.append(
                {
                    "kind": kind,
                    "detail": (
                        f"{etype} arrived after response terminated with {self._terminal!r}"
                    ),
                }
            )
        if etype == "response.output_item.added":
            item = event.get("item") or {}
            if item.get("type") == "function_call":
                self._register(item, event)
        elif etype == "response.function_call_arguments.delta":
            self._handle_delta(event)
        elif etype == "response.output_item.done":
            self._handle_done(event)

    @property
    def response_completed(self) -> bool:
        return self._terminal == "completed"

    @property
    def terminal(self) -> str | None:
        """'completed' / 'failed' / 'incomplete' / 'error', or None while open."""
        return self._terminal

    @property
    def terminal_event(self) -> dict | None:
        return self._terminal_event

    @property
    def duplicate_terminals(self) -> list[str]:
        return list(self._duplicate_terminals)

    @property
    def termination(self) -> str:
        """'completed' / 'failed' / 'incomplete' / 'error' / 'open' / 'none'."""
        if self._terminal is not None:
            return self._terminal
        return "open" if self._saw_stream_events else "none"

    @property
    def completed(self) -> list:
        return list(self._completed)

    @property
    def completed_keys(self) -> list[str]:
        return list(self._completed_keys)

    @property
    def done_keys(self) -> list[str]:
        return list(self._done_keys)

    @property
    def duplicate_dones(self) -> list[str]:
        return list(self._duplicate_dones)

    @property
    def orphan_dones(self) -> list[str]:
        return list(self._orphan_dones)

    @property
    def anomalies(self) -> list[dict]:
        return list(self._anomalies)

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def done_seen(self) -> bool:
        return bool(self._done_keys)


def _terminal_reason(event: dict | None, terminal: str) -> str:
    """Short human-readable reason for a failure terminal, or "".

    - ``error``: the event's ``code`` and ``message`` (SDK
      ResponseErrorEvent).
    - ``incomplete``: ``response.incomplete_details.reason``
      (e.g. ``content_filter`` / ``max_output_tokens``).
    - ``failed``: ``response.error`` code/message when present.
    """
    if not event:
        return ""
    if terminal == "error":
        code = event.get("code")
        message = event.get("message")
        if code or message:
            return f" ({code}: {message})" if code and message else f" ({code or message})"
        return ""
    response = event.get("response") or {}
    if terminal == "incomplete":
        reason = (response.get("incomplete_details") or {}).get("reason")
        return f" (reason: {reason})" if reason else ""
    if terminal == "failed":
        err = response.get("error") or {}
        code = err.get("code")
        message = err.get("message")
        if code or message:
            return f" ({code}: {message})" if code and message else f" ({code or message})"
    return ""


def validate_stream(events: list, emit_on_done: bool) -> dict:
    """One completed chunk per UNIQUE function_call done event; none otherwise.

    Passes iff ALL of these hold:
    - the set of completed calls equals the set of calls whose done
      event arrived (a duplicate done is tolerated — the handler emits
      once — but recorded on the handler, not here);
    - no orphan dones;
    - no handler anomalies (key conflicts, unknown/ambiguous deltas,
      duplicate sequences, deltas after done, arguments mismatches,
      invalid JSON arguments, events after a terminal event,
      conflicting terminal events);
    - every completed chunk's arguments are valid;
    - the response did not terminate while a function_call was still
      pending: ``response.completed`` with an added-but-never-done call
      is a failure (REWORK4 fix, audit P2-C), never a pass;
    - the response ended NORMALLY: a failure terminal
      (``response.failed`` / ``response.incomplete`` / ``error``)
      always fails (POST-R4 fix, fifth-round audit P1) — a failed or
      incomplete response is never a pass, even when every call
      completed first. The outcome is ``"wrong-result"`` (the
      OUTCOMES vocabulary has no "failed"/"incomplete" value) and the
      detail names the terminal kind and its reason.
    A call that was added but never done does NOT fail validation when
    no terminal signal arrived: the handler correctly emitted nothing
    for it — the stream is truncated, and the detail says so; the
    returned ``termination`` field reports ``"open"`` for such a
    partial stream, and the detail says the request's success is not
    yet proven — an open stream is never silently treated as a
    verified success. If the event list contains no streaming events
    at all, there is nothing to validate: outcome ``"not-checked"``.
    Any other failure is ``"wrong-result"`` — never ``"ok"``.

    The returned dict also carries the P2-A split (sixth-round audit):
    ``call_chunk_valid`` is the chunk-coherence verdict (identical to
    ``passed``), ``request_completed_successfully`` is true only for a
    normally terminated, chunk-valid stream, and ``request_status`` is
    ``"completed"`` / ``"pending"`` / ``"failed"`` / ``"not-checked"``.
    A chunk-valid open stream is ``"pending"`` (PENDING/INDETERMINATE)
    and is never counted as a completed success; a failed terminal, a
    terminated-with-pending stream, or any chunk incoherence is
    ``"failed"``.
    """
    handler = StreamingHandler(emit_on_done=emit_on_done)
    for ev in events:
        handler.handle(ev)
    done = handler.done_keys
    emitted = handler.completed_keys
    anomalies = handler.anomalies
    termination = handler.termination
    if not handler._saw_stream_events:
        return {
            "outcome": "not-checked",
            "passed": False,
            "emitted": 0,
            "termination": termination,
            "call_chunk_valid": False,
            "request_completed_successfully": False,
            "request_status": "not-checked",
            "detail": "no streaming events received — nothing to validate",
        }
    terminated_with_pending = handler.response_completed and handler.pending_count > 0
    terminal_failed = termination in ("failed", "incomplete", "error")
    passed = (
        sorted(emitted) == sorted(done)
        and not handler.orphan_dones
        and not anomalies
        and all(c.get("arguments_valid", False) for c in handler.completed)
        and not terminated_with_pending
        and not terminal_failed
    )
    # P2-A (sixth-round audit): split chunk coherence from request
    # success. ``passed`` keeps its long-standing meaning — chunk
    # coherence — so the frozen regression files, which assert an open
    # stream passes, stay green. Only a normally terminated,
    # chunk-valid stream counts as a completed successful request.
    call_chunk_valid = passed
    request_completed_successfully = passed and termination == "completed"
    if request_completed_successfully:
        request_status = "completed"
    elif termination == "open" and call_chunk_valid:
        request_status = "pending"
    else:
        request_status = "failed"
    detail = (
        f"done event(s) for {len(done)} call(s), {len(emitted)} completed "
        f"chunk(s) emitted (expected {len(done)})"
    )
    if handler.pending_count:
        detail += f"; {handler.pending_count} call(s) added but never done"
    if terminated_with_pending:
        detail += (
            "; response completed with "
            f"{handler.pending_count} call(s) still pending "
            "(function_call never done)"
        )
    if terminal_failed:
        reason = _terminal_reason(handler.terminal_event, termination)
        detail += f"; response terminated with {termination}{reason}"
    elif termination == "open":
        detail += "; stream still open (no terminal event) — request success not yet proven"
    if handler.duplicate_terminals:
        detail += f"; duplicate terminal event(s): {sorted(set(handler.duplicate_terminals))}"
    if handler.orphan_dones:
        detail += f"; orphan done(s): {handler.orphan_dones}"
    if anomalies:
        kinds = sorted({a["kind"] for a in anomalies})
        detail += f"; anomalies ({len(anomalies)}): {kinds}"
    return {
        "outcome": "ok" if passed else "wrong-result",
        "passed": passed,
        "emitted": len(emitted),
        "termination": termination,
        "call_chunk_valid": call_chunk_valid,
        "request_completed_successfully": request_completed_successfully,
        "request_status": request_status,
        "detail": detail,
    }


# ---------------------------------------------------------------------------
# Simulated transport + scenario runner
# ---------------------------------------------------------------------------


def _fault_for(step: dict, attempt: int) -> str | None:
    fault = step.get("fault")
    if isinstance(fault, list):
        return fault[attempt - 1] if attempt - 1 < len(fault) else None
    return fault


class SimulatedTransport:
    """Deterministic local transport. `fault` may be one kind or a per-attempt list."""

    def call(self, step: dict, attempt: int) -> dict:
        fault = _fault_for(step, attempt)
        if fault == "timeout":
            raise SimulatedFault("timeout")
        if fault == "http429":
            raise SimulatedFault("rate-limited")
        if fault == "http500":
            raise SimulatedFault("server-error")
        if fault == "token_budget":
            raise SimulatedFault("token-budget")
        if fault == "malformed_json":
            return {"raw": "{not valid json", "model": step.get("model", "")}
        if fault == "false_response":
            return {
                "content": "The capital of France is Berlin.",
                "model": step.get("model", ""),
            }
        payload = {
            "content": step.get("response_content", "ok"),
            "model": step.get("model", ""),
            "usage": {"prompt_tokens": step.get("prompt_tokens", 0)},
        }
        if step.get("wrong_schema"):
            payload.pop("content")
        if step.get("silent_trim"):
            payload["trimmed"] = True
        if step.get("substitute_model"):
            payload["model"] = "gpt-4"
            payload["usage"] = {"prompt_tokens": step.get("gpt4_tokens", 0)}
        return payload


class SchemaConfigError(ValueError):
    """A schema spec names a type this validator does not support.

    Raised by ``_matches_type`` so a misspelled or unknown type is a
    readable configuration error, never a silent pass.
    """


# JSON Schema standard type names (plus the short names the R06
# fixtures already use). Contract — written here so it is testable:
# - "integer" / "int": a Python int, never a bool, never a float
#   (2.0 does NOT satisfy "integer": a float is not an integer here,
#   even though JSON Schema would allow a zero-fraction number);
# - "number" / "float": a Python int or float, never a bool, and
#   always FINITE — NaN and +/-inf are not valid JSON numbers, so
#   they never satisfy a numeric type;
# - "boolean" / "bool": only a Python bool;
# - "string" / "str": only a str; "array" / "list": only a list;
# - "object" / "dict": only a dict; "null": only None.
# Any other type name raises SchemaConfigError (fail-closed).
_SUPPORTED_SCALAR_TYPES = (
    "int",
    "integer",
    "float",
    "number",
    "bool",
    "boolean",
    "str",
    "string",
    "list",
    "array",
    "dict",
    "object",
    "null",
)


def _matches_scalar_type(value, spec: str) -> bool:
    """Type check for one scalar schema name (see the contract above)."""
    if spec in ("int", "integer"):
        return isinstance(value, int) and not isinstance(value, bool)
    if spec in ("float", "number"):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False
        # math.isfinite raises OverflowError on huge ints, and an int
        # is finite by definition — only floats need the check.
        return math.isfinite(value) if isinstance(value, float) else True
    if spec in ("bool", "boolean"):
        return isinstance(value, bool)
    if spec in ("str", "string"):
        return isinstance(value, str)
    if spec in ("list", "array"):
        return isinstance(value, list)
    if spec in ("dict", "object"):
        return isinstance(value, dict)
    if spec == "null":
        return value is None
    raise SchemaConfigError(
        f"unsupported schema type {spec!r} — supported types: {', '.join(_SUPPORTED_SCALAR_TYPES)}"
    )


def _matches_type(value, spec) -> bool:
    """Type check for a schema spec. REWORK2 fix (review P1-02): in Python
    ``isinstance(True, int)`` is True, so a bare ``isinstance(value, int)``
    lets a bool satisfy an int field. bool is therefore excluded from int
    (and from float/number) explicitly. ``float``/``number`` accept int
    (JSON numbers), but never bool, and never a non-finite float (NaN,
    +/-inf are not valid JSON numbers — REWORK3 fix, review P2-02).
    A spec may also be a nested dict: {"type": "object",
    "properties": {...}} or {"type": "array", "items": <spec>}, so nested
    payloads are checked recursively; an unknown type name raises
    SchemaConfigError (fail-closed, REWORK3 fix, review P2-01) instead
    of silently passing."""
    if isinstance(spec, str):
        return _matches_scalar_type(value, spec)
    if isinstance(spec, dict):
        t = spec.get("type")
        if t is None:
            raise SchemaConfigError(
                f"schema object without a 'type' field is not supported: {spec!r}"
            )
        if t in ("object", "dict"):
            if not isinstance(value, dict):
                return False
            props = spec.get("properties") or {}
            return all(k in value and _matches_type(value[k], s) for k, s in props.items())
        if t in ("array", "list"):
            if not isinstance(value, list):
                return False
            item_spec = spec.get("items")
            return all(_matches_type(v, item_spec) for v in value) if item_spec else True
        if t in _SUPPORTED_SCALAR_TYPES:
            return _matches_scalar_type(value, t)
        raise SchemaConfigError(
            f"unsupported schema type {t!r} — supported types: {', '.join(_SUPPORTED_SCALAR_TYPES)}"
        )
    raise SchemaConfigError(
        f"schema spec must be a type name or a {{'type': ...}} object, got: {spec!r}"
    )


# ---------------------------------------------------------------------------
# Factual content check (R2-05: content comparison, never a payload flag)
# ---------------------------------------------------------------------------


def _normalize_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace — for keyword matching."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.lower())).strip()


def _normalized_words(text: str) -> list[str]:
    """Normalized word multiset (sorted) — for the expected-answer check."""
    return sorted(_normalize_text(text).split())


def check_factual_content(
    content: str,
    expected_answer: str | None = None,
    expected_keywords: list[str] | None = None,
    forbidden_claims: list[str] | None = None,
) -> tuple[str, bool, str]:
    """Judge a response by its CONTENT against a known-good expected answer.

    The three rules are separate checks with separate meanings — they
    must not be conflated (REWORK3 fix, review P1-02):
    - ``expected_answer`` — the full correct sentence. When supplied it
      is ACTUALLY COMPARED: the response passes only when its
      normalized word multiset equals the expected answer's
      (case-, punctuation- and word-order-insensitive). Anything else
      fails: a paraphrase is not verified, a contradiction is wrong,
      and a refusal is wrong. General natural language semantics —
      including logical negation — are NOT judged by substring
      matching, so ``"Paris is NOT the capital"`` never passes
      against ``"The capital of France is Paris."`` (its word
      multiset differs: it adds "not" and drops "of"/"france").
      Known limit, stated here and in the reports: word ORDER is
      ignored, so this check verifies the response says the same
      words, not the same sentence structure — it is a lexical
      match, not a semantic verification.
    - ``expected_keywords`` — a keyword rule only. Keywords present
      proves the words appear, nothing more. With no expected_answer
      to compare against, a keyword pass is reported as
      ``"not-checked"`` with the detail saying exactly that: factual
      truth was NOT checked. It is never claimed as verified factual
      correctness.
    - ``forbidden_claims`` — strings that must not appear. Present
      means the response states a false claim: ``"wrong-result"``.
      Absent, on its own, proves nothing about the answer: with no
      other rule it is ``"not-checked"``.
    If no expected content is supplied at all, factual correctness is
    NOT CHECKED and the detail says so — the validator never claims to
    detect a false statement it was never given the truth for.
    Every ``"not-checked"`` return carries ``passed=False`` (REWORK4
    fix, audit P1-B): "not checked" is not a verified pass and must
    never be counted as one — neither by ``run_step`` nor by the UI.
    """
    expected_keywords = expected_keywords or []
    forbidden_claims = forbidden_claims or []
    if expected_answer is None and not expected_keywords and not forbidden_claims:
        return (
            "not-checked",
            False,
            "no expected answer supplied — factual content not checked",
        )
    norm = _normalize_text(content)
    present_forbidden = [c for c in forbidden_claims if _normalize_text(c) in norm]
    if present_forbidden:
        return (
            "wrong-result",
            False,
            f"response states a forbidden (false) claim: {present_forbidden}"
            + (f" — expected answer: {expected_answer!r}" if expected_answer else ""),
        )
    if expected_answer:
        if _normalized_words(content) == _normalized_words(expected_answer):
            missing = [k for k in expected_keywords if _normalize_text(k) not in norm]
            if missing:
                return (
                    "wrong-result",
                    False,
                    (
                        "response matches the expected answer but is missing "
                        f"expected keyword(s): {missing}"
                    ),
                )
            return (
                "ok",
                True,
                (
                    "response matches the expected answer"
                    f" {expected_answer!r} (normalized word-multiset match)"
                    + ("; expected keywords present" if expected_keywords else "")
                ),
            )
        return (
            "wrong-result",
            False,
            (
                "response does not match the expected answer"
                f" {expected_answer!r} (normalized word-multiset match required; "
                "paraphrase and semantic equivalence are not assessed)"
            ),
        )
    # No expected_answer: only keyword / forbidden rules remain.
    missing = [k for k in expected_keywords if _normalize_text(k) not in norm]
    if missing:
        return (
            "wrong-result",
            False,
            (f"response is missing expected keyword(s): {missing} — factual truth not checked"),
        )
    if expected_keywords:
        return (
            "not-checked",
            False,
            (
                "expected keywords present; factual truth not checked — "
                "keyword match does not verify factual correctness"
            ),
        )
    return (
        "not-checked",
        False,
        (
            "no forbidden claim stated; factual truth not checked — "
            "absence of a forbidden claim does not verify the answer"
        ),
    )


def _validate_payload(step: dict, payload: dict) -> tuple[str, bool, str]:
    if "raw" in payload:
        try:
            _parse_strict_json(payload["raw"])
        except ValueError as exc:
            return "wrong-result", False, f"response body is not valid JSON: {exc}"
    schema = step.get("expected_schema") or {}
    missing = [k for k in schema if k not in payload]
    try:
        wrong_type = [
            k for k, t in schema.items() if k in payload and not _matches_type(payload[k], t)
        ]
    except SchemaConfigError as exc:
        # An unknown or malformed schema type is a configuration error:
        # fail-closed as NOT_CHECKED, never a silent pass (REWORK3).
        return "not-checked", False, f"schema configuration error: {exc}"
    if missing:
        return "wrong-result", False, f"response missing required field(s): {missing}"
    if wrong_type:
        return "wrong-result", False, f"response field(s) wrong type: {wrong_type}"
    if payload.get("trimmed") and not step.get("trim_allowed"):
        return "wrong-result", False, "prompt was silently trimmed, no error raised"
    if step.get("substitute_model"):
        check = validate_token_count(
            step.get("prompt_text", ""),
            step.get("model", ""),
            payload.get("usage", {}).get("prompt_tokens", -1),
        )
        if check["outcome"] == "default-substituted":
            return "default-substituted", False, check["detail"]
        if not check["passed"]:
            return "wrong-result", False, check["detail"]
    # Factual correctness is judged by CONTENT against the fixture's
    # expected answer (R2-05). A payload flag is never trusted: a
    # transport that admits its own response is false proves nothing
    # about detecting real factual errors. A "not-checked" factual
    # result is propagated, not swallowed into "ok" (REWORK3): the
    # scenario must not claim a validation that never happened.
    if any(k in step for k in ("expected_answer", "expected_keywords", "forbidden_claims")):
        outcome, passed, detail = check_factual_content(
            payload.get("content", ""),
            expected_answer=step.get("expected_answer"),
            expected_keywords=step.get("expected_keywords"),
            forbidden_claims=step.get("forbidden_claims"),
        )
        if not passed or outcome == "not-checked":
            return outcome, passed, detail
    return "ok", True, "response valid"


def _request_completion(outcome: str, passed: bool) -> tuple[bool, str]:
    """Request-level completion for a non-streaming check (P2-A).

    A request completed successfully iff its check outcome is ``"ok"``
    and it passed. ``request_status`` is ``"completed"`` then,
    ``"failed"`` for any other checked outcome, and ``"not-checked"``
    when the check never ran. Streaming checks compute the same pair
    inside ``validate_stream``, where ``termination`` decides between
    ``"completed"`` and ``"pending"``.
    """
    rcs = outcome == "ok" and passed
    if rcs:
        return True, "completed"
    if outcome == "not-checked":
        return False, "not-checked"
    return False, "failed"


def run_step(
    scenario: dict,
    step: dict,
    transport: SimulatedTransport,
    max_attempts: int = MAX_ATTEMPTS,
) -> CallResult:
    """Run one API-call step with a bounded retry budget (never exceeded)."""
    name = scenario["name"]
    url = scenario.get("source_url", "")
    prompt_tokens = step.get("prompt_tokens", 0)
    max_tokens = step.get("max_tokens", 0)
    budget = step.get("token_budget")
    if budget is not None and prompt_tokens + max_tokens > budget:
        return CallResult(
            name,
            scenario["kind"],
            step.get("call", "call"),
            "token-budget",
            False,
            0,
            0,
            url,
            f"prompt {prompt_tokens} + max {max_tokens} > budget {budget}",
            termination="",
            request_completed_successfully=False,
            request_status="failed",
        )
    attempts, elapsed = 0, 0
    latency = step.get("latency_ms", 0)
    while attempts < max_attempts:
        attempts += 1
        try:
            payload = transport.call(step, attempts)
        except SimulatedFault as exc:
            wait = PER_ATTEMPT_WAIT_MS if exc.kind == "timeout" else 1000 * attempts
            elapsed += wait
            if attempts >= max_attempts:
                return CallResult(
                    name,
                    scenario["kind"],
                    step.get("call", "call"),
                    exc.kind,
                    False,
                    attempts,
                    elapsed + latency,
                    url,
                    f"{exc.kind} on every attempt ({attempts}/{max_attempts}); "
                    "retry budget exhausted, failure reported not hidden",
                    termination="",
                    request_completed_successfully=False,
                    request_status="failed",
                )
            continue
        outcome, passed, detail = _validate_payload(step, payload)
        rcs, status = _request_completion(outcome, passed)
        return CallResult(
            name,
            scenario["kind"],
            step.get("call", "call"),
            outcome,
            passed,
            attempts,
            elapsed + latency,
            url,
            detail,
            termination="",
            request_completed_successfully=rcs,
            request_status=status,
        )
    raise AssertionError("unreachable: retry loop always returns")


def run_scenario(scenario: dict, max_attempts: int = MAX_ATTEMPTS) -> list[CallResult]:
    """Run one fixture scenario; returns one CallResult per step/case."""
    kind = scenario.get("kind")
    url = scenario.get("source_url", "")
    if kind == "api_call":
        transport = SimulatedTransport()
        return [
            run_step(scenario, step, transport, max_attempts) for step in scenario.get("steps", [])
        ]
    if kind == "token_count":
        results = []
        for case in scenario.get("cases", []):
            reported = (
                count_tokens_gpt4(case["text"])
                if case.get("sut") == "buggy"
                else count_tokens_for_model(case["text"], case.get("model", ""))
            )
            check = validate_token_count(case["text"], case.get("model", ""), reported)
            rcs, status = _request_completion(check["outcome"], check["passed"])
            results.append(
                CallResult(
                    scenario["name"],
                    kind,
                    case.get("case", "count"),
                    check["outcome"],
                    check["passed"],
                    1,
                    0,
                    url,
                    check["detail"],
                    termination="",
                    request_completed_successfully=rcs,
                    request_status=status,
                )
            )
        return results
    if kind == "streaming":
        check = validate_stream(scenario.get("events", []), scenario.get("emit_on_done", True))
        return [
            CallResult(
                scenario["name"],
                kind,
                scenario.get("case", "stream"),
                check["outcome"],
                check["passed"],
                1,
                0,
                url,
                check["detail"],
                termination=check["termination"],
                request_completed_successfully=check["request_completed_successfully"],
                request_status=check["request_status"],
            )
        ]
    raise ValueError(f"unknown scenario kind: {kind!r}")


def run_all(scenarios: list) -> list[CallResult]:
    results: list[CallResult] = []
    for scenario in scenarios:
        results.extend(run_scenario(scenario))
    return results


def load_scenarios(path: str | Path) -> list:
    """Load a scenario fixture file; invalid JSON or shape raises ValueError."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"scenario file not found: {path}")
    try:
        data = _parse_strict_json(p.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ValueError(f"scenario file is not valid JSON: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise ValueError("scenario file must be a non-empty JSON list")
    for item in data:
        if not isinstance(item, dict) or not item.get("name") or not item.get("kind"):
            raise ValueError("each scenario needs at least name and kind")
        if not str(item.get("source_url", "")).startswith("http"):
            raise ValueError(f"scenario {item.get('name')} needs a source_url")
    return data


def export_csv(results: list[CallResult], path: str | Path) -> Path:
    """Source-preserving CSV export: every row keeps its source_url."""
    fields = [
        "scenario",
        "kind",
        "step",
        "outcome",
        "passed",
        "attempts",
        "elapsed_ms",
        "source_url",
        "detail",
        # P2-A: request-level completion travels with every row.
        "termination",
        "request_completed_successfully",
        "request_status",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))
    return Path(path)
