"""
generator.py
------------
Workload and process generator for SchedX.

Generates realistic, configurable process datasets using the shared Process data model.
Supports:
  - Configurable process counts (1 to 100).
  - Configurable arrival time and burst time ranges.
  - Four distinct workload distribution strategies:
      1. Uniform Distribution (even spread across ranges)
      2. Short-Job Heavy (75% short jobs, 25% long jobs)
      3. Long-Job Heavy (75% long jobs, 25% short jobs)
      4. Mixed Workload (multimodal combination of short, medium, long jobs)
  - Deterministic random seed reproducibility (isolated random.Random instance).
  - Dynamic workload summary statistics calculations.
"""

import random
from typing import List, Tuple, Dict, Any, Optional
from schedulers.process import Process


DISTRIBUTION_PRESETS = [
    "Uniform Distribution",
    "Short-Job Heavy",
    "Long-Job Heavy",
    "Mixed Workload",
]


def validate_generator_inputs(
    num_processes: int,
    arrival_range: Tuple[int, int],
    burst_range: Tuple[int, int],
    distribution: str,
    seed: Optional[int] = None,
) -> None:
    """
    Validates input parameters for the process generator.
    Raises ValueError or TypeError if any constraint is violated.
    """
    if not isinstance(num_processes, int) or isinstance(num_processes, bool):
        raise TypeError(f"Number of processes must be an integer, got {type(num_processes).__name__}.")
    if num_processes < 1 or num_processes > 100:
        raise ValueError(f"Number of processes must be between 1 and 100, got {num_processes}.")

    if not isinstance(arrival_range, (tuple, list)) or len(arrival_range) != 2:
        raise ValueError("Arrival range must be a tuple/list of (min_arrival, max_arrival).")
    min_at, max_at = arrival_range
    if not isinstance(min_at, int) or not isinstance(max_at, int) or isinstance(min_at, bool) or isinstance(max_at, bool):
        raise TypeError("Arrival range values must be integers.")
    if min_at < 0:
        raise ValueError(f"Minimum arrival time cannot be negative, got {min_at}.")
    if min_at > max_at:
        raise ValueError(f"Minimum arrival time ({min_at}) cannot exceed maximum arrival time ({max_at}).")

    if not isinstance(burst_range, (tuple, list)) or len(burst_range) != 2:
        raise ValueError("Burst range must be a tuple/list of (min_burst, max_burst).")
    min_bt, max_bt = burst_range
    if not isinstance(min_bt, int) or not isinstance(max_bt, int) or isinstance(min_bt, bool) or isinstance(max_bt, bool):
        raise TypeError("Burst range values must be integers.")
    if min_bt < 1:
        raise ValueError(f"Minimum burst time must be at least 1, got {min_bt}.")
    if min_bt > max_bt:
        raise ValueError(f"Minimum burst time ({min_bt}) cannot exceed maximum burst time ({max_bt}).")

    if distribution not in DISTRIBUTION_PRESETS:
        raise ValueError(
            f"Unknown distribution '{distribution}'. Must be one of: {DISTRIBUTION_PRESETS}."
        )

    if seed is not None:
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise TypeError(f"Random seed must be an integer or None, got {type(seed).__name__}.")


def _generate_burst_time(
    rng: random.Random,
    min_bt: int,
    max_bt: int,
    distribution: str,
) -> int:
    """
    Generates a single burst time integer within [min_bt, max_bt]
    according to the specified workload distribution strategy.
    """
    if min_bt == max_bt:
        return min_bt

    span = max_bt - min_bt
    one_third = max(1, span // 3)

    if distribution == "Uniform Distribution":
        # Evenly spread across [min_bt, max_bt]
        return rng.randint(min_bt, max_bt)

    elif distribution == "Short-Job Heavy":
        # 75% probability: lower third of range (short jobs)
        # 25% probability: remaining upper range
        short_bound = min(max_bt, min_bt + one_third)
        if rng.random() < 0.75:
            return rng.randint(min_bt, short_bound)
        else:
            return rng.randint(short_bound, max_bt)

    elif distribution == "Long-Job Heavy":
        # 75% probability: upper third of range (long jobs)
        # 25% probability: remaining lower range
        long_bound = max(min_bt, max_bt - one_third)
        if rng.random() < 0.75:
            return rng.randint(long_bound, max_bt)
        else:
            return rng.randint(min_bt, long_bound)

    elif distribution == "Mixed Workload":
        # Multimodal distribution:
        # 40% short jobs, 35% medium jobs, 25% long jobs
        r = rng.random()
        lower_cut = min(max_bt, min_bt + one_third)
        upper_cut = max(min_bt, max_bt - one_third)

        if r < 0.40:
            return rng.randint(min_bt, lower_cut)
        elif r < 0.75:
            med_low = min(lower_cut, upper_cut)
            med_high = max(lower_cut, upper_cut)
            return rng.randint(med_low, med_high)
        else:
            return rng.randint(upper_cut, max_bt)

    return rng.randint(min_bt, max_bt)


def generate_processes(
    num_processes: int = 5,
    arrival_range: Tuple[int, int] = (0, 10),
    burst_range: Tuple[int, int] = (1, 10),
    distribution: str = "Uniform Distribution",
    seed: Optional[int] = None,
) -> List[Process]:
    """
    Generates a list of independent Process instances adhering to the specified parameters.

    Parameters:
        num_processes (int): Number of processes to create (1 to 100).
        arrival_range (tuple[int, int]): Inclusive (min_arrival, max_arrival) range.
        burst_range (tuple[int, int]): Inclusive (min_burst, max_burst) range.
        distribution (str): Workload distribution preset.
        seed (int, optional): Random seed for reproducible generation.

    Returns:
        list[Process]: Generated process list with unique PIDs (P1, P2, ...).
    """
    validate_generator_inputs(
        num_processes=num_processes,
        arrival_range=arrival_range,
        burst_range=burst_range,
        distribution=distribution,
        seed=seed,
    )

    # Use dedicated isolated Random instance to avoid altering global random state
    rng = random.Random(seed)

    min_at, max_at = arrival_range
    min_bt, max_bt = burst_range

    raw_data = []
    for _ in range(num_processes):
        at = rng.randint(min_at, max_at)
        bt = _generate_burst_time(rng, min_bt, max_bt, distribution)
        raw_data.append((at, bt))

    # Sort primarily by arrival time so processes arrive chronologically
    raw_data.sort(key=lambda item: item[0])

    processes = []
    for i, (at, bt) in enumerate(raw_data, start=1):
        processes.append(
            Process(
                pid=f"P{i}",
                arrival_time=at,
                burst_time=bt,
            )
        )

    return processes


def calculate_workload_summary(processes: List[Process]) -> Dict[str, Any]:
    """
    Computes summary workload statistics for a given list of Process objects.

    Parameters:
        processes (list[Process]): List of processes.

    Returns:
        dict: Summary metrics including total count, total burst, averages, and extremes.
    """
    if not processes:
        return {
            "total_processes": 0,
            "total_burst_time": 0,
            "avg_burst_time": 0.0,
            "avg_arrival_time": 0.0,
            "min_burst_time": 0,
            "max_burst_time": 0,
            "min_arrival_time": 0,
            "max_arrival_time": 0,
        }

    n = len(processes)
    bursts = [p.burst_time for p in processes]
    arrivals = [p.arrival_time for p in processes]

    return {
        "total_processes": n,
        "total_burst_time": sum(bursts),
        "avg_burst_time": round(sum(bursts) / n, 2),
        "avg_arrival_time": round(sum(arrivals) / n, 2),
        "min_burst_time": min(bursts),
        "max_burst_time": max(bursts),
        "min_arrival_time": min(arrivals),
        "max_arrival_time": max(arrivals),
    }
