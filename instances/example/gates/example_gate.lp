% ===========================================================================
% EXAMPLE gate — the PROOF leg, illustrative (NOT a real policy).
% Five abstract allocation rules as HARD constraints. A proposed action is PERMITTED
% iff it violates none; otherwise REFUSED and the violated rule is NAMED (so the
% attestation can cite the clause).
%
% Design: each rule derives a `violation(R, Subject, Actual, Limit)` atom when broken.
% Permitted iff there is NO violation. We MATERIALIZE violations as facts (not `:-`
% integrity constraints) so a refusal carries its reasons. Clingo is integer-only;
% values arrive ×1000 (the Python layer scales).
%
% Input facts (from facts.py):
%   proposal(Unit, Action, NewAllocMilli, DeltaMilli).   Action ∈ increase/decrease/hold/release
%   current_alloc(Unit, AllocMilli).
%   unit_score(Unit, ScoreMilli).        % can be negative
%   unit_drawdown(Unit, DrawMilli).      % peak-to-current, negative ×1000
%   pool_total(PoolMilli).  total_other_alloc(SumMilli).
%   rule_param(per_unit_cap | pool_cap_pct | max_round_increase_pct | score_floor | max_drawdown, V).
% ===========================================================================

increases_alloc(U) :- proposal(U, increase, _, D), D > 0.

% Rule 1 — per-unit cap: resulting allocation must not exceed the cap.
violation(r1_per_unit_cap, U, New, Cap) :-
    proposal(U, _, New, _), rule_param(per_unit_cap, Cap), New > Cap.

% Rule 2 — pool cap: this unit's new alloc + all others ≤ cap% of the pool.
violation(r2_pool_cap, U, Projected, Limit) :-
    proposal(U, _, New, _), total_other_alloc(Other), pool_total(Pool),
    rule_param(pool_cap_pct, Pct),
    Projected = New + Other, Limit = Pool * Pct / 1000, Projected > Limit.

% Rule 3 — per-round delta: an increase may not exceed X% of the current allocation.
violation(r3_round_delta, U, Delta, MaxDelta) :-
    proposal(U, increase, _, Delta), current_alloc(U, Cur),
    rule_param(max_round_increase_pct, Pct), MaxDelta = Cur * Pct / 1000, Delta > MaxDelta.

% Rule 4 — score floor: don't INCREASE a unit scoring below the floor.
violation(r4_score_floor, U, Score, Floor) :-
    increases_alloc(U), unit_score(U, Score), rule_param(score_floor, Floor), Score < Floor.

% Rule 5 — drawdown kill-switch: at/below max drawdown, only decrease/release permitted.
in_drawdown(U) :- unit_drawdown(U, Draw), rule_param(max_drawdown, Max), Draw <= Max.
killswitch_ok(decrease).
killswitch_ok(release).
violation(r5_drawdown_killswitch, U, Action, Draw) :-
    in_drawdown(U), proposal(U, Action, _, _), unit_drawdown(U, Draw), not killswitch_ok(Action).

any_violation :- violation(_,_,_,_).
permitted :- not any_violation.

#show permitted/0.
#show violation/4.
