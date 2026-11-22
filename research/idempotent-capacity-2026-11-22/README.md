# Independent continuation — Idempotent capacity, 22/11/2026

**Parent audit:** research/independent-audit-2026-11-22 @ 8dc9c72768beab63451a570183f324a5eafca791.  
**Branch:** research/idempotent-capacity-2026-11-22.  
**Policy:** never merge or alter main without the project owner's explicit approval. Original axioms unchanged.

## Contents
- [THEOREM.md](THEOREM.md): sharp lower bound on additive idempotents under injective ordered multiplication and one-sided distributivity; three sharply separated zero-provenance recovery levels.
- [AUDIT.md](AUDIT.md): critical acceptance/rejection ledger, scope and literature comparison.
- [idempotent_capacity_checks.py](idempotent_capacity_checks.py): independent bounded computations, not a proof.

## Reproduce
From the repository root:

    python3 research/idempotent-capacity-2026-11-22/idempotent_capacity_checks.py

Expected: 256 binary-table pairs; 32 sharp semigroup constructions; levels I/II/III checks pass.

## Status
- Derived (proved): the general |E(C)| ≥ |E(A)||B| bound with equality model; zero-rate lower bounds m, m+1, 2^m under progressively stronger recovery requirements.
- Independent (checked/previously established): the two distributive directions are independent of the original axioms.
- Known methods: semigroup homomorphisms, semilattice products, finite powersets, Newton identities.
- Candidate Original: **none authenticated**.
- Open: whether coupling typed partial multiplication, local updateability, mixed additive measurement, and depth-limited recovery produces a genuinely new sharp complexity bound.

The work is a research audit and mathematical derivation, not a claim of a new foundational system or peer-reviewed novelty.
