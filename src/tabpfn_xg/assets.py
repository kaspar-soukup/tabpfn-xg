"""Pinned public-data acquisition and strict joins for cached demo assets.

All paths are supplied by callers. No model imports, credentials or inference.
"""

import hashlib
import json
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from .calibration import probability_check
from .data import BASE_FEATURES, convert_shots, flatten_events
from .features import FEATURES, build_features


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def checked_bytes(path, expected_sha256):
    """Read an explicitly supplied file and reject drift before consuming it."""
    path = Path(path)
    payload = path.read_bytes()
    if sha256(payload) != expected_sha256:
        raise ValueError(f"SHA-256 mismatch: {path}; restore the pinned file")
    return payload


def fetch_json(url, path, expected_sha256, *, offline=False):
    """Reuse a verified cache or atomically save a verified public JSON download.

    Corrupt existing files fail rather than being silently replaced. Offline
    mode never opens a connection, including when a cache file is missing.
    """
    path = Path(path)
    if path.exists():
        return json.loads(checked_bytes(path, expected_sha256))
    if offline:
        raise FileNotFoundError(f"Missing cached source: {path}; run without --offline to download")
    request = Request(url, headers={"User-Agent": "tabpfn-xg-demo-assets"})
    with urlopen(request, timeout=60) as response:
        payload = response.read()
    if sha256(payload) != expected_sha256:
        raise ValueError(f"SHA-256 mismatch for download {url}; no cache file written")
    parsed = json.loads(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_bytes(payload)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return parsed


def _shot_ids(frame, label):
    if "id" not in frame or frame.empty or frame.id.isna().any() or not frame.id.is_unique:
        raise ValueError(f"{label} needs nonempty, unique shot IDs")
    if not frame.id.map(lambda value: isinstance(value, str) and bool(value.strip())).all():
        raise ValueError(f"{label} shot IDs must be nonempty strings")


def join_predictions(shots, predictions):
    """Align every eligible shot by ID, preserving cached prediction order/values.

    Predictions contain id/catboost/tabpfn, optionally match_id/outcome/statsbomb.
    Optional source fields must agree with the converted public events. No
    subset joins are allowed. Probabilities in the cache are already calibrated.
    """
    required = {"id", "match_id", "shot_freeze_frame", "shot_outcome_encoded",
                "shot_statsbomb_xg", *BASE_FEATURES}
    if not shots.columns.is_unique or not required <= set(shots):
        raise ValueError("Converted shots are missing required geometry or metadata columns")
    if (not predictions.columns.is_unique
            or not {"id", "catboost", "tabpfn"} <= set(predictions)):
        raise ValueError("Cached predictions require id, catboost and tabpfn columns")
    _shot_ids(shots, "Converted shots")
    _shot_ids(predictions, "Cached predictions")
    if set(shots.id) != set(predictions.id):
        raise ValueError("Shot-ID join is incomplete: eligible events and cached predictions differ")
    aligned = shots.set_index("id", drop=False).loc[predictions.id].reset_index(drop=True)
    result = predictions[["id", "catboost", "tabpfn"]].reset_index(drop=True).copy()
    for name in ("catboost", "tabpfn"):
        result[name] = probability_check(result[name], len(result))
    for target, source in (("match_id", "match_id"), ("outcome", "shot_outcome_encoded"),
                           ("statsbomb", "shot_statsbomb_xg")):
        values = aligned[source].to_numpy()
        if target in predictions and not np.array_equal(predictions[target].to_numpy(), values):
            raise ValueError(f"Cached {target} disagrees with public events after the shot-ID join")
        result[target] = values
    if result.match_id.isna().any() or not result.outcome.isin([0, 1]).all():
        raise ValueError("Converted match IDs and binary outcomes must be present")
    probability_check(result.statsbomb, len(result))
    result = result[["id", "match_id", "outcome", "catboost", "tabpfn", "statsbomb"]]
    features = build_features(aligned)
    geometry = pd.concat([result, features, aligned[["shot_freeze_frame"]]], axis=1)
    return geometry


def prediction_digest(frame):
    """Canonical hash of the full frozen table, independent of CSV formatting."""
    records = []
    for row in frame.itertuples(index=False):
        records.append([row.id, int(row.match_id), int(row.outcome),
                        float(row.catboost).hex(), float(row.tabpfn).hex(),
                        float(row.statsbomb).hex()])
    return sha256(json.dumps(records, separators=(",", ":")).encode())


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False,
                       separators=(",", ":")) + "\n").encode()


def _write_dataset(output_dir, payloads):
    """Publish a complete directory only after validation; never replace drift."""
    output_dir = Path(output_dir)
    if output_dir.exists():
        if (output_dir.is_dir() and {p.name for p in output_dir.iterdir()} == set(payloads)
                and all((output_dir / name).read_bytes() == payload
                        for name, payload in payloads.items())):
            return
        raise ValueError(f"Output differs: {output_dir}; choose a new --output directory")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".tabpfn-assets-", dir=output_dir.parent) as temporary:
        staging = Path(temporary) / "dataset"
        staging.mkdir()
        for name, payload in payloads.items():
            (staging / name).write_bytes(payload)
        staging.rename(output_dir)


def prepare_external(cache_dir, predictions_path, output_dir, source, *, offline=False):
    """Download pinned events and build a complete, verified local dataset.

    source supplies commit, match/event hashes, expected audit counts, model-cache
    hash and canonical full prediction digest. Inputs are validated before any
    dataset output is written. No inference or calibration takes place.
    """
    cache_dir, predictions_path = Path(cache_dir), Path(predictions_path)
    commit = source["source_commit"]
    if (not isinstance(commit, str) or len(commit) != 40
            or any(c not in "0123456789abcdef" for c in commit)):
        raise ValueError("Source commit must be a full lowercase Git SHA")
    if tuple(source["features"]) != FEATURES:
        raise ValueError("Source feature order differs from the shared 50-feature schema")
    match_ids = source["match_ids"]
    if (not match_ids or any(type(mid) is not int or mid <= 0 for mid in match_ids)
            or match_ids != sorted(set(match_ids))):
        raise ValueError("Source match IDs must be sorted unique positive integers")
    if set(source["event_sha256"]) != {str(mid) for mid in match_ids}:
        raise ValueError("Event hashes must cover exactly the selected match IDs")
    # Read through BytesIO so the validated bytes are exactly the bytes parsed.
    payload = checked_bytes(predictions_path, source["model_predictions_sha256"])
    predictions = pd.read_csv(BytesIO(payload), float_precision="round_trip")
    _shot_ids(predictions, "Cached predictions")
    base = f"https://raw.githubusercontent.com/hudl/open-data/{commit}/data"
    matches = fetch_json(f"{base}/matches/{source['competition_id']}/{source['season_id']}.json",
                         cache_dir / "matches.json", source["matches_sha256"], offline=offline)
    actual_ids = [match["match_id"] for match in matches]
    if sorted(actual_ids) != match_ids:
        raise ValueError("Public match metadata differs from the frozen match selection")
    tables = []
    for match_id in match_ids:
        events = fetch_json(f"{base}/events/{match_id}.json", cache_dir / f"{match_id}.json",
                            source["event_sha256"][str(match_id)], offline=offline)
        tables.append(flatten_events(events, match_id))
    shots, audit = convert_shots(pd.concat(tables, ignore_index=True))
    if audit != source["conversion_audit"]:
        raise ValueError(f"Eligibility audit differs from the frozen population: {audit}")
    joined = join_predictions(shots, predictions)
    if (sorted(joined.match_id.unique().tolist()) != match_ids
            or int(joined.outcome.sum()) != source["goals"]):
        raise ValueError("Eligible match selection or goal count differs from the frozen population")
    if prediction_digest(joined) != source["evaluation_predictions_digest"]:
        raise ValueError("Joined probabilities, outcomes, match IDs or row order differ from frozen predictions")
    data = _json_bytes(joined.to_dict("records"))
    provenance = dict(
        schema_version=1, source="StatsBomb Open Data",
        source_url="https://github.com/hudl/open-data",
        source_commit=commit, competition_id=source["competition_id"], season_id=source["season_id"],
        source_license_url=f"https://github.com/hudl/open-data/blob/{commit}/LICENSE.pdf",
        source_manifest_sha256=sha256(_json_bytes(source)),
        matches_sha256=source["matches_sha256"], event_sha256=source["event_sha256"],
        model_predictions_sha256=source["model_predictions_sha256"],
        original_predictions_sha256=source["original_predictions_sha256"],
        evaluation_predictions_digest=source["evaluation_predictions_digest"],
        match_ids=match_ids, conversion_audit=audit, goals=source["goals"],
        features=list(FEATURES), shots_sha256=sha256(data),
        probability_mode="Frozen calibrated model predictions; StatsBomb xG from pinned source",
        coordinates="StatsBomb 120 x 80; goal centre (120, 40); no transformation",
        attribution="Data: StatsBomb. Include the StatsBomb logo when publishing analysis.",
    )
    _write_dataset(output_dir, {"shots.json": data, "manifest.json": _json_bytes(provenance)})
    return provenance
