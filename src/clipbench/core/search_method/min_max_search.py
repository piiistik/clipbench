import random
import math
from typing import Optional, Tuple, Dict, List

from clipbench.core.search_method.search_method import SearchMethod
from clipbench.core.search_space import VariableVector, SpaceDefinition, SearchSpace
from clipbench.core.evaluator import Evaluator
from clipbench.core.registry import register


class MinMaxSearch(SearchMethod):
    """
    Simulated annealing-based search that can look for minima, maxima, or both.

    Configuration options (provided to factory):
      - random_seed: Optional[int]
      - restarts: int (number of SA restarts; we stop early if budget exhausted)
      - steps_per_run: int (approx number of proposals per restart)
      - tmax: float (initial temperature)
      - tmin: float (final temperature)
      - mode: "min" | "max" | "both"
      - neighbor_radius: int (max absolute step on a single coordinate; default 1)
    """

    def __init__(
        self,
        random_seed: Optional[int] = None,
        restarts: int = 20,
        steps_per_run: int = 500,
        tmax: float = 100.0,
        tmin: float = 1e-3,
        mode: str = "both",
        neighbor_radius: int = 1,
    ):
        self._rng = random.Random(random_seed)
        self.restarts = int(restarts)
        self.steps_per_run = int(steps_per_run)
        self.Tmax = float(tmax)
        self.Tmin = float(tmin)
        self.mode = mode.lower()
        if self.mode not in {"min", "max", "both"}:
            raise ValueError("mode must be one of 'min', 'max', or 'both'")
        self.neighbor_radius = max(1, int(neighbor_radius))

    def run(
        self,
        space_definition: SpaceDefinition,
        search_space: SearchSpace,
        evaluator: Evaluator,
        budget: int,
    ):
        """
        Runs simulated annealing restarts until either `budget` new evaluations are used
        or we've done `self.restarts` restarts. Evaluations are written into `search_space`
        by calling `evaluator.evaluate([vector])`. We read results from `search_space`.
        """
        # Helper closures
        def random_vector() -> VariableVector:
            return tuple(self._rng.randint(lo, hi) for (lo, hi) in space_definition)

        def propose_neighbor(vec: VariableVector) -> VariableVector:
            lst = list(vec)
            i = self._rng.randrange(len(lst))
            lo, hi = space_definition[i]
            step = self._rng.randint(-self.neighbor_radius, self.neighbor_radius)
            if step == 0:
                # ensure we actually change something
                step = 1 if self._rng.random() < 0.5 else -1
            new_val = lst[i] + step
            # clamp
            new_val = max(lo, min(hi, new_val))
            lst[i] = new_val
            return tuple(lst)

        # Energy wrapper: converts evaluator result to energy for minimization
        # mode == 'min' -> energy = value
        # mode == 'max' -> energy = -value (so we minimize negative value)
        # For 'both' we'll run two sweeps: one for min and one for max (handled later)
        VERY_BAD = 1e12

        def get_energy(vec: VariableVector, target_mode: str) -> float:
            # if not in search_space, request evaluation (consumes budget)
            if vec not in search_space:
                nonlocal budget
                if budget <= 0:
                    # No budget left. Return VERY_BAD so it's unlikely to be selected.
                    return VERY_BAD
                evaluator.evaluate([vec])  # evaluator is expected to write back to search_space
                budget -= 1
            val = search_space.get(vec)
            # Treat None as failure -> VERY_BAD
            if val is None:
                return VERY_BAD
            try:
                v = float(val)
            except Exception:
                return VERY_BAD
            if target_mode == "min":
                return v
            else:  # "max"
                return -v

        # core SA single-run (returns final vector and energy)
        def sa_run(start_vec: VariableVector, target_mode: str):
            # ensure starting vector evaluated
            T = self.Tmax
            steps = self.steps_per_run
            # geometric cooling factor so T after steps becomes Tmin
            if steps > 0:
                alpha = (self.Tmin / max(self.Tmax, 1e-300)) ** (1.0 / steps)
            else:
                alpha = 1.0

            current = start_vec
            current_energy = get_energy(current, target_mode)

            # If we have NO budget and we couldn't evaluate start (current_energy VERY_BAD),
            # just return immediately.
            if budget <= 0 and current_energy >= VERY_BAD:
                return current, current_energy

            for _ in range(steps):
                if budget <= 0:
                    break
                neighbor = propose_neighbor(current)
                neigh_energy = get_energy(neighbor, target_mode)
                # acceptance
                delta = neigh_energy - current_energy
                if delta <= 0:
                    accept = True
                else:
                    # probability
                    try:
                        prob = math.exp(-delta / T)
                    except OverflowError:
                        prob = 0.0
                    accept = self._rng.random() < prob
                if accept:
                    current = neighbor
                    current_energy = neigh_energy
                # cool
                T *= alpha
            return current, current_energy

        # Main orchestration:
        endpoints: List[VariableVector] = []

        # If mode == "both", we'll run minima search and maxima search sequentially (sharing budget).
        target_modes = []
        if self.mode == "both":
            target_modes = ["min", "max"]
        else:
            target_modes = [self.mode]

        for target_mode in target_modes:
            # do up to `self.restarts` restarts or until budget exhausted
            for r in range(self.restarts):
                if budget <= 0:
                    break
                # pick a start vector not repeated within this search if possible
                start = random_vector()
                # If start already evaluated it's OK (we reuse value; no budget consumed)
                final_vec, final_energy = sa_run(start, target_mode)
                # Optional local greedy descent/climb to polish endpoint (consumes budget)
                polished = self._local_polish(final_vec, target_mode, space_definition, search_space, evaluator, budget, get_energy)
                # _local_polish may have consumed budget; it returns (vec, updated_budget)
                final_vec = polished[0]
                budget = polished[1]

                endpoints.append(final_vec)
                if budget <= 0:
                    break

            if budget <= 0:
                break

        # done. Ensure search_space has entries for any endpoints (should already be evaluated)
        to_eval = [v for v in endpoints if v not in search_space]
        if to_eval and budget > 0:
            # evaluate remaining (do not exceed budget)
            take = to_eval[:budget]
            evaluator.evaluate(take)
            # Reduce budget accordingly (match RandomSample semantics)
            budget -= len(take)

        # Nothing to return; search_space modified in-place by calls to evaluator.evaluate.
        return

    def _local_polish(self, start_vec: VariableVector, target_mode: str, space_definition: SpaceDefinition,
                      search_space: SearchSpace, evaluator: Evaluator, budget: int, energy_fn) -> Tuple[VariableVector, int]:
        """
        Greedy local polish: attempt to deterministically improve the solution by
        exploring all 1-step neighbors and moving to any strictly better neighbor,
        repeating until no improvement or budget exhausted.

        Returns (final_vector, remaining_budget).
        """
        current = start_vec
        current_energy = energy_fn(current, target_mode)

        # If current hasn't been evaluated and we have budget, evaluate (energy_fn will do it).
        # Loop until no improving neighbor found
        improved = True
        while improved and budget > 0:
            improved = False
            # iterate neighbors (one-step changes per coordinate)
            candidates = []
            for i in range(len(current)):
                lo, hi = space_definition[i]
                for step in (-1, 1):
                    new_val = current[i] + step
                    if new_val < lo or new_val > hi:
                        continue
                    nbr = list(current)
                    nbr[i] = new_val
                    candidates.append(tuple(nbr))
            # shuffle candidates to avoid deterministic tie-breaking
            self._rng.shuffle(candidates)
            for nbr in candidates:
                if nbr not in search_space:
                    if budget <= 0:
                        # can't evaluate more neighbors
                        break
                    evaluator.evaluate([nbr])
                    budget -= 1
                nbr_energy = energy_fn(nbr, target_mode)
                if nbr_energy < current_energy:
                    current = nbr
                    current_energy = nbr_energy
                    improved = True
                    # as soon as we move to a better neighbor, break to recompute its neighbors
                    break
            # loop continues until no improving neighbor found or budget exhausted
        return current, budget


@register("min_max_search")
def factory_min_max_search(configuration: dict) -> MinMaxSearch:
    return MinMaxSearch(
        random_seed=configuration.get("random_seed", None),
        restarts=configuration.get("restarts", 20),
        steps_per_run=configuration.get("steps_per_run", 500),
        tmax=configuration.get("tmax", 100.0),
        tmin=configuration.get("tmin", 1e-3),
        mode=configuration.get("mode", "both"),
        neighbor_radius=configuration.get("neighbor_radius", 1),
    )
