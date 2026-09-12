"""Independent native-gradient validation using a Euclidean Gram embedding.

No model execution and no imports from the experiment or its report script.
The embedding preserves all eight-vector inner products, so norms and
directional derivatives can be recomputed without the original large bank.
"""
from pathlib import Path
import csv
import hashlib
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "papers/edit_localization/results/full_parameter"


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((OUT / "manifest.json").read_text())
    assert manifest["completed"] is True
    gram = np.load(OUT / "gram.npy")
    eigenvalues, basis = np.linalg.eigh(gram)
    assert gram.shape == (8, 8) and np.all(np.isfinite(gram))
    assert eigenvalues.min() > -1e-12 * np.linalg.norm(gram)
    vectors = basis * np.sqrt(np.maximum(eigenvalues, 0))[None, :]
    gram_error = float(np.max(np.abs(vectors @ vectors.T - gram)))
    mu_e, mu_u = vectors[:2]
    recorded = rows(OUT / "curves.csv")
    mechanisms = ["edit", "length", "edit_length"]
    errors = {"rho_Q": 0., "rho_P": 0., "absolute_bias": 0.,
              "squared_rho_Q_derivative": 0.}
    cases = {}
    for index, mechanism in enumerate(mechanisms):
        u, v = vectors[2 + 2 * index:4 + 2 * index]
        delta, epsilon = u - mu_e, v - mu_u
        for row in recorded:
            if row["mechanism"] != mechanism:
                continue
            alpha = float(row["alpha"])
            bias, observed, target = delta + alpha * epsilon, u + alpha * v, mu_e + alpha * mu_u
            numerator, denominator = bias @ bias, observed @ observed
            direct = {
                "rho_Q": np.linalg.norm(bias) / np.linalg.norm(observed),
                "rho_P": np.linalg.norm(bias) / np.linalg.norm(target),
                "absolute_bias": np.linalg.norm(bias),
                "squared_rho_Q_derivative":
                    2 * ((bias @ epsilon) * denominator - numerator * (observed @ v)) / denominator**2,
            }
            for key, value in direct.items():
                errors[key] = max(errors[key], abs(float(value) - float(row[key])))
        # The derivative is a quadratic: its maximum is attained at an endpoint
        # or at its vertex. Obtain its coefficients from three direct evaluations.
        def derivative_numerator(alpha):
            z, h = delta + alpha * epsilon, u + alpha * v
            return (z @ epsilon) * (h @ h) - (z @ z) * (h @ v)
        values = np.array([derivative_numerator(t) for t in [0., .5, 1.]])
        polynomial = np.linalg.solve(np.array([[1., 0., 0.], [1., .5, .25], [1., 1., 1.]]), values)
        tests = [0., 1.]
        if polynomial[2] != 0:
            vertex = -polynomial[1] / (2 * polynomial[2])
            if 0 < vertex < 1:
                tests.append(vertex)
        maximum_derivative_numerator = max(derivative_numerator(t) for t in tests)
        absolute_minimum = float(np.clip(-(delta @ epsilon) / (epsilon @ epsilon), 0, 1))
        cases[mechanism] = {
            "rho_Q_0": float(np.linalg.norm(delta) / np.linalg.norm(u)),
            "rho_Q_1": float(np.linalg.norm(delta + epsilon) / np.linalg.norm(u + v)),
            "absolute_bias_0": float(np.linalg.norm(delta)),
            "absolute_bias_1": float(np.linalg.norm(delta + epsilon)),
            "absolute_bias_minimizer": absolute_minimum,
            "absolute_bias_minimum": float(np.linalg.norm(delta + absolute_minimum * epsilon)),
            "selected_component_cosine": float((u @ v) / np.linalg.norm(u) / np.linalg.norm(v)),
            "maximum_derivative_numerator": float(maximum_derivative_numerator),
            "strictly_decreasing_rho_on_unit_interval": bool(maximum_derivative_numerator < 0),
        }
    ids = rows(OUT / "public_selected_ids.csv")
    reporting = [r for r in ids if r["split"] == "reporting"]
    original_ids = rows(OUT.parent / "public_selected_ids.csv")
    assert reporting == [r for r in original_ids if r["split"] == "reporting"]
    losses = rows(OUT / "per_sentence_losses.csv")
    assert [int(r["line"]) for r in reporting] == manifest["source_ids"] == [int(r["line"]) for r in losses]
    previous = np.load(OUT.parent / "public_base_nll.npy")[256:]
    full_loss = np.array([float(r["full_loss"]) for r in losses])
    loss_error = max(abs(float(r["edited_loss"]) + float(r["untouched_loss"]) - float(r["full_loss"])) for r in losses)
    nll_error = float(np.max(np.abs(full_loss - previous)))
    edit_p = np.array([.1 + .8 * float(r["edit_fraction"]) for r in reporting])
    length_p = np.array([.1 + .8 * min(float(r["source_length"]) / 64, 1) for r in reporting])
    mix = float(edit_p.sum() / (edit_p.sum() + length_p.sum()))
    residuals = [float(np.linalg.norm(vectors[6+j] - mix*vectors[2+j] - (1-mix)*vectors[4+j]) / np.linalg.norm(vectors[6+j])) for j in [0, 1]]
    for name, expected in manifest["outputs"].items():
        assert digest(OUT / name) == expected, name
    for field, path in [("script_sha256", "executed_script.py"), ("helper_script_sha256", "executed_helper_script.py"), ("protocol_sha256", "protocol_snapshot.md")]:
        assert digest(OUT / path) == manifest[field], field
    assert sum(p["count"] for p in manifest["named_parameters"]) == 73886208
    assert max(errors.values()) < 1e-11 and loss_error < 1e-6 and nll_error < 1e-5
    result = {
        "verification_scope": "Independent Euclidean embedding of native-gradient Gram; no transformer rerun",
        "gram_reconstruction_max_abs": gram_error,
        "gram_eigenvalues": eigenvalues.tolist(),
        "max_curve_discrepancies": errors,
        "same_reporting_record_ids": True,
        "loss_decomposition_max_abs": loss_error,
        "previous_forward_nll_max_abs": nll_error,
        "all_original_artifact_and_source_hashes_match": True,
        "mixture_edit_coefficient": mix,
        "mixture_relative_norm_residuals": residuals,
        "cases": cases,
    }
    (OUT / "independent_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
