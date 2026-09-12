#!/usr/bin/env python3
"""Validate and cost a proposed GPU study; never launches or purchases anything."""
import argparse
import json
import math
from pathlib import Path


def positive(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x > 0


def nonnegative(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--profile", type=Path)
    args = p.parse_args()
    c = json.loads(args.config.read_text())
    assert c["schema_version"] == "1.0"
    assert c["execution_enabled"] is False
    assert len(c["methods"]) == len(set(c["methods"])) == 5
    assert len(c["stages"]["initial"]["seeds"]) == 3
    assert len(c["stages"]["confirmation"]["seeds"]) == 5
    assert not set(c["stages"]["initial"]["seeds"]) & set(c["stages"]["confirmation"]["seeds"])
    assert 0 < c["audit"]["absolute_survival_floor"] <= c["audit"]["main_expected_unknown_query_fraction"] <= 1
    assert c["optimizer"]["epochs_per_rollout_collection"] == 1
    assert not c["optimizer"]["reuse_audited_advantage_after_parameter_update"]
    assert not c["sandbox"]["host_execution_for_generated_code"]
    assert c["sandbox"]["network"] == "none"
    assert not c["sandbox"]["private_workspace_or_credentials_mount"]
    assert not c["data"]["outcome_based_task_filtering"]
    assert c["rollout"]["temperature"] == 1 and c["rollout"]["top_p"] == 1 and c["rollout"]["top_k"] == 0
    resources = c["resource_inputs_required_before_any_paid_execution"]
    assert positive(resources["profile_safety_multiplier"])
    assert resources["profile_safety_multiplier"] >= 1
    if resources["gpu_count"] is not None:
        assert positive(resources["gpu_count"]) and int(resources["gpu_count"]) == resources["gpu_count"]
    missing = ["resources."+k for k, v in resources.items() if not positive(v)]
    if not c["sandbox"]["image_digest"]:
        missing.append("sandbox.image_digest")
    if not c["data"]["split_manifest_sha256"]:
        missing.append("data.split_manifest_sha256")
    result = {"configuration_valid": True, "launch_inputs_missing": missing,
              "launch_performed": False, "prices_used": False,
              "note": "Planning only; training adapter and reviewed checker remain separate prerequisites."}
    result["token_ceiling_per_full_size_run"] = {
        stage: c["stages"][stage]["collections_per_run"] * c["rollout"]["groups_per_collection"] * c["rollout"]["group_size"] * c["rollout"]["maximum_turns"] * c["rollout"]["max_new_tokens_per_turn"]
        for stage in ["initial", "confirmation"]}
    if args.profile:
        pr = json.loads(args.profile.read_text())
        required_nonnegative = ["setup_seconds_per_run", "evaluation_seconds_per_run", "diagnostic_seconds_per_run", "shared_calibration_gpu_seconds"]
        assert all(nonnegative(pr[k]) for k in required_nonnegative), "Profile must contain measured nonnegative times"
        assert positive(pr["gpu_count"]) and int(pr["gpu_count"]) == pr["gpu_count"]
        assert all(positive(pr["collection_seconds_p90_by_method"][m]) for m in c["methods"])
        if positive(resources["gpu_count"]):
            assert pr["gpu_count"] == resources["gpu_count"], "Profile and proposed hardware GPU counts differ"
        if positive(resources["gpu_memory_gb_each"]) and positive(pr.get("allocated_gpu_memory_gb_each")):
            assert pr["allocated_gpu_memory_gb_each"] == resources["gpu_memory_gb_each"], "Profile and proposed VRAM differ"
        forecasts = {}
        multiplier = resources["profile_safety_multiplier"]
        for stage in ["initial", "confirmation"]:
            cfg = c["stages"][stage]
            per_method = {}
            wall_hours = {}
            for method in c["methods"]:
                seconds = sum(pr[k] for k in required_nonnegative[:3]) + cfg["collections_per_run"] * pr["collection_seconds_p90_by_method"][method]
                per_method[method] = pr["gpu_count"] * seconds * len(cfg["seeds"]) / 3600
                wall_hours[method] = seconds / 3600
            total = sum(per_method.values()) + pr["shared_calibration_gpu_seconds"] / 3600
            cap = resources[stage+"_total_gpu_hours_cap"]
            wall_cap = resources["per_run_wall_hours_cap"]
            forecasts[stage] = {"occupied_gpu_hours_by_method_all_seeds": per_method,
                "total_with_shared_calibration": total, "planning_reserve_with_multiplier": total*multiplier,
                "entered_cap": cap, "fits_entered_cap": total*multiplier <= cap if positive(cap) else None,
                "wall_hours_by_method_per_run": wall_hours,
                "all_runs_fit_wall_cap_with_multiplier": max(wall_hours.values())*multiplier <= wall_cap if positive(wall_cap) else None}
        g = c["pilot_gates"]
        gate_fields = {
            "reference_repeatability": ("reference_repeat_disagreement_fraction", lambda v: v <= g["reference_repeat_disagreement_max"]),
            "nontrivial_unknown_groups": ("fraction_groups_with_at_least_four_unknown_labels", lambda v: v >= g["fraction_groups_with_at_least_four_unknown_labels_min"]),
            "reference_cost_relevance": ("reference_critical_path_fraction", lambda v: v >= g["reference_critical_path_fraction_for_speed_study_min"]),
            "projected_net_saving": ("predicted_net_wall_time_saving_fraction", lambda v: v >= g["predicted_net_wall_time_saving_min"])}
        for _, (field, _) in gate_fields.items():
            if pr.get(field) is not None:
                v = pr[field]
                assert isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                if field == "predicted_net_wall_time_saving_fraction":
                    assert v <= 1, "A time saving cannot exceed 100%; negative savings are allowed and fail the gate"
                else:
                    assert 0 <= v <= 1, "Profile fraction must lie in [0, 1]"
        gates = {name: bool(fn(pr[field])) if pr.get(field) is not None else None for name, (field, fn) in gate_fields.items()}
        gates["source_and_ledger_checks"] = pr.get("source_and_ledger_checks_passed") is True
        peak, available = pr.get("measured_peak_gpu_memory_gb"), pr.get("allocated_gpu_memory_gb_each")
        gates["gpu_memory"] = peak/available <= g["max_gpu_memory_fraction"] if positive(peak) and positive(available) else None
        storage = pr.get("storage_gb_estimate")
        gates["disk_cap"] = storage <= resources["disk_gb_cap"] if positive(storage) and positive(resources["disk_gb_cap"]) else None
        result.update({"forecast": forecasts, "pilot_gates": gates,
                       "calibration_accounting": "Each stage is a standalone forecast including the entered calibration cost once. When calibration is reused, combined physical cost subtracts one duplicate calibration charge; all paid pilot work is additionally charged from its actual ledger.",
                       "speed_study_gates_passed": all(v is True for v in gates.values())})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
