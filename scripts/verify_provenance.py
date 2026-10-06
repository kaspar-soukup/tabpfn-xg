"""Read-only verification of the selected research snapshot; standard library only."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text())


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def verify(root, manifest):
    """Check bytes and frozen records without importing or executing research code."""
    records = manifest["files"]
    require(len({r["path"] for r in records}) == len(records), "Duplicate source paths")
    hashes = {}
    for record in records:
        relative = Path(record["path"])
        require(not relative.is_absolute() and ".." not in relative.parts,
                f"Nonportable source path: {relative}")
        path = root / relative
        require(path.is_file(), f"Missing source: {relative}")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        hashes[record["path"]] = digest.hexdigest()
        require(path.stat().st_size == record["bytes"], f"Size mismatch: {relative}")
        require(digest.hexdigest() == record["sha256"], f"SHA-256 mismatch: {relative}")
        if "columns" in record:
            with path.open(newline="") as stream:
                reader = csv.reader(stream)
                require(next(reader) == record["columns"], f"Column mismatch: {relative}")
                require(sum(1 for _ in reader) == record["rows"], f"Row mismatch: {relative}")

    external_dir = root / "results/xg_external_bundesliga_2023_24"
    external = read_json(external_dir / "manifest.json")
    geometry = read_json(root / "results/xg_geometry/manifest.json")
    pilot = read_json(root / "results/xg_pilot/manifest.json")
    selection = read_json(root / "results/xg_geometry/selection.json")
    require(external == manifest["external_experiment"], "External manifest fields differ")
    require(pilot == manifest["historical"]["pilot_manifest"], "Pilot manifest fields differ")
    require(geometry["baseline_manifest"] == pilot, "Geometry baseline differs from pilot")
    require(external["settings"] == pilot["settings"], "Frozen model settings differ")
    require(geometry["feature_config"] == manifest["geometry_config"], "Geometry config differs")
    require(external["features"] == pilot["features"] + geometry["bundles"]["geometry"],
            "Ordered feature schema differs")
    require(len(external["features"]) == len(set(external["features"])) == 50,
            "Expected 50 distinct features")
    require(external["frozen_selection"] == {k: v for k, v in selection.items()
                                             if k.startswith("geometry_")},
            "Frozen calibration differs")
    for path, digest in external["hashes"].items():
        require(hashes[path] == digest, f"Frozen hash differs: {path}")
    for name, digest in pilot["hashes"].items():
        require(hashes[f"data/processed/{name}"] == digest, f"Historical input differs: {name}")
    require(geometry["feature_code_sha256"] == hashes["scripts/xg_features.py"],
            "Geometry implementation differs")

    splits = read_csv(root / "results/xg_pilot/splits.csv")
    require(len(splits) == 45185 and len({r["shot_id"] for r in splits}) == 45185,
            "Historical shot count or uniqueness differs")
    for role, expected in manifest["historical"]["roles"].items():
        rows = [r for r in splits if r["role"] == role]
        require(len(rows) == expected["shots"] and
                sorted({int(r["match_id"]) for r in rows}) == expected["match_ids"],
                f"Historical role differs: {role}")
    role_matches = [set(manifest["historical"]["roles"][role]["match_ids"])
                    for role in ("fit", "calibration", "validation", "evaluation")]
    for i, matches in enumerate(role_matches):
        require(all(not matches & other for other in role_matches[i + 1:]),
                "Historical experiment roles share matches")
    fit_ids = external["fit_shot_ids"]
    require(len(fit_ids) == len(set(fit_ids)) == 8000, "Expected 8,000 unique fit shots")
    require(set(fit_ids) <= {r["shot_id"] for r in splits if r["role"] == "fit"},
            "Fit sample contains non-fit shots")

    matches = read_json(root / "data/external/bundesliga_2023_24/matches.json")
    match_ids = {m["match_id"] for m in external["matches"]}
    require(len(matches) == len(match_ids) == 34 and
            {m["match_id"] for m in matches} == match_ids, "External match selection differs")
    require(not match_ids & {int(r["match_id"]) for r in splits}, "External matches overlap history")
    source = read_json(root / "data/external/bundesliga_2023_24/source.json")
    require(source["sha"] == external["source_commit"], "Public source commit differs")
    audit = read_json(external_dir / "data_audit.json")
    require(audit == manifest["external_data_audit"], "External data audit differs")
    for match_id, digest in audit["event_sha256"].items():
        require(hashes[f"data/external/bundesliga_2023_24/{match_id}.json"] == digest,
                f"Event bytes differ: {match_id}")
    predictions = read_csv(external_dir / "evaluation_predictions.csv")
    require(len(predictions) == len({r["id"] for r in predictions}) == 908,
            "Expected 908 unique evaluation shots")
    require({int(r["match_id"]) for r in predictions} == match_ids,
            "Evaluation match IDs differ")
    require(not {r["id"] for r in predictions} & {r["shot_id"] for r in splits},
            "External shot IDs overlap history")
    require(all(r["outcome"] in {"0", "1"} for r in predictions) and
            sum(int(r["outcome"]) for r in predictions) == 102, "Goal count or labels differ")
    for row in predictions:
        for model in ("catboost", "tabpfn", "statsbomb"):
            probability = float(row[model])
            require(math.isfinite(probability) and 0 <= probability <= 1,
                    f"Invalid cached {model} probability")
    require(read_csv(external_dir / "evaluation_metrics.csv") == manifest["external_metrics"],
            "Frozen metrics differ")
    require(read_json(external_dir / "paired_differences.json") == manifest["paired_differences"],
            "Frozen paired differences differ")
    print(f"PASS: {len(records)} source hashes; frozen schema/settings/calibration; "
          "8,000 fit IDs; historical roles; 34 external matches / 908 shots / 102 goals.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-root", required=True, type=Path)
    parser.add_argument("--manifest", type=Path,
                        default=Path(__file__).resolve().parents[1] / "provenance/research_manifest.json")
    args = parser.parse_args()
    try:
        verify(args.research_root, read_json(args.manifest))
    except (OSError, ValueError, KeyError, StopIteration) as error:
        parser.exit(1, f"FAIL: {error}\n")


if __name__ == "__main__":
    main()
