# Rank diff — R03 (original delivery vs corrected scoring)

Before: `reports/rework1/ranking_original.csv` (copied verbatim from the original
delivery `~/projects/demand-radar/reports/ranking.csv`). After:
`reports/rework1/ranking.csv` (re-run of `python -m demand_radar score` after R03).
Old E treated raw issue rows as 'independent sources'; new E uses distinct
independence groups (repo/context; author_hash not yet landed, see below).
G is 0/UNKNOWN for all pains in both R01-interim and R03 (R04 pending), so the
old 80s lose 10 from G as well as the E correction.

## Old top 10 — before vs after

| pain_id | domain | old total | old E (old 'indep') | new total | new E groups | raw URLs | orgs | delta |
|---|---|---|---|---|---|---|---|---|
| 4bb734fac7245033d327 | BIO | 80 | E=30 (19) | 60 | 3 | 19 | 3 | -20 |
| 6513d051954cbe1b5027 | AI | 80 | E=30 (19) | 60 | 3 | 19 | 3 | -20 |
| cd021eac3c93ed0d2de1 | BIO | 80 | E=30 (16) | 60 | 3 | 16 | 3 | -20 |
| e3091fb34139fdf57dbd | FIN | 80 | E=30 (16) | 60 | 3 | 16 | 3 | -20 |
| 28ccf8f8701bb84bf95b | FIN | 80 | E=30 (9) | 55 | 2 | 9 | 2 | -25 |
| da75a85dbf1cb9f121cc | UK | 80 | E=30 (9) | 55 | 2 | 9 | 2 | -25 |
| 3955670369ee96d7b5d6 | JOB | 80 | E=30 (8) | 55 | 2 | 8 | 2 | -25 |
| bdef2d35b09f45a0e94a | RES | 80 | E=30 (8) | 50 | 1 | 8 | 1 | -30 |
| 908f662d8a749944fb20 | RES | 80 | E=30 (7) | 50 | 1 | 7 | 1 | -30 |
| 0b7adcf63ec0f2075fab | FIN | 80 | E=30 (6) | 60 | 3 | 6 | 3 | -20 |

## Selected old pains (the two old MVP selections)

| pain | old total | new total | raw URLs | indep groups | orgs | gate (70) |
|---|---|---|---|---|---|---|
| AI ai-agent-api | 80 | 60 | 19 | 3 | 3 | FAIL — below 70 |
| FIN fin-data | 80 | 55 | 9 | 2 | 2 | FAIL — below 70 |

## Totals

- Pains scoring >= 70 (old PRD/MVP gate): before 11, after 0.
- Highest corrected total: 60 (was 80).
- Pains actually capped at 59 by the <2-independent rule: 0 (0 — with G=0/UNKNOWN no
  single-group pain exceeds 59; the cap rule itself is implemented and proven by
  tests/test_independence.py::test_cap59_uses_independent_count_not_raw, which forces
  G=10 via 2 competitor checks and asserts total 59).
- Pains with evidence from only 1 organisation: 210 of 221; >= 2 orgs: 11.
- Independent-group distribution: 1 group: 210 pains, 2 groups: 5, 3 groups: 5, 4 groups: 1.
- score_reason uniqueness: 221 unique reasons for 221 pains (0 duplicate groups).

## Consequence for R05

Under the original gate (total >= 70), ZERO pains qualify after correction. R05 must
not lower the gate; it must record 0 qualifying PRDs under the original gate unless
R02/R04 change the underlying evidence (R02 verdicts may remove evidence; R04
competitor checks can add at most G=10, which would lift the current top pains
60 -> 70 only if they also hold >= 2 independent groups — AI ai-agent-api would
reach exactly 70, FIN fin-data 65).
