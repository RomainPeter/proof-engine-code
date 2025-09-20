#!/usr/bin/env python
# Placeholder for metrics generation
import json
import time


def main():
    metrics = {
        "timestamp": time.time(),
        "s0_fast_duration_s": -1,
        "s1_quick_duration_s": -1,
        "ci_s1_duration_s": -1,
        "ci_s2_duration_s": -1,
        "obligations_triggered": [],
        "failures_by_obligation": {},
    }

    # In a real scenario, this would parse logs or timing files.

    with open(".proof/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("Generated dummy metrics file at .proof/metrics.json")


if __name__ == "__main__":
    main()
