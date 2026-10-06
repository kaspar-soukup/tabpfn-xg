"""Shared, ordered predictors using the frozen visible-player geometry."""

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import BASE_FEATURES

PRESSURE_FEATURES = (
    "observed_defenders", "has_observed_defender", "freeze_frame_missing",
    "invalid_observed_players", "nearest_defender_distance", "defenders_within_2",
    "defenders_within_5", "defenders_in_goal_triangle",
    "nearest_defender_to_shooting_line",
)
GEOMETRY_FEATURES = (
    "defender_goal_coverage", "keeper_goal_coverage",
    "unobstructed_goal_fraction", "keeper_shooting_line_offset",
)
FEATURES = BASE_FEATURES + PRESSURE_FEATURES + GEOMETRY_FEATURES
GEOMETRY_INPUTS = (
    "player_x", "player_y", "goalkeeper_x", "goalkeeper_y", "shot_freeze_frame",
)


@dataclass(frozen=True)
class GeometryConfig:
    """Frozen research settings; distances are StatsBomb units, not metres."""

    defender_radius: float = 0.6
    keeper_radius: float = 0.9
    goal_samples: int = 101
    distance_sentinel: float = float(np.hypot(120, 80))

    def __post_init__(self):
        for name in ("defender_radius", "keeper_radius", "distance_sentinel"):
            value = getattr(self, name)
            try:
                valid = bool(np.isfinite(value)) and value > 0
            except (TypeError, ValueError):
                valid = False
            if not valid:
                raise ValueError(f"{name} must be finite and positive")
        if isinstance(self.goal_samples, bool) or not isinstance(self.goal_samples, int) or self.goal_samples < 2:
            raise ValueError("goal_samples must be an integer of at least two")


def _coordinate(row, prefix):
    try:
        point = np.array([row[f"{prefix}_x"], row[f"{prefix}_y"]], dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid {prefix} coordinates; expected finite coordinates within 120 x 80") from error
    if not np.isfinite(point).all() or not (0 <= point[0] <= 120 and 0 <= point[1] <= 80):
        raise ValueError(f"Invalid {prefix} coordinates; expected finite coordinates within 120 x 80")
    return point


def _observed_defenders(frame):
    """Count invalid entries before filtering teammates or goalkeepers."""
    missing = not isinstance(frame, list)
    defenders = []
    invalid = 0
    for player in ([] if missing else frame):
        if not isinstance(player, dict):
            invalid += 1
            continue
        try:
            point = np.asarray(player.get("location"), dtype=float)
            valid = (point.shape == (2,) and np.isfinite(point).all()
                     and 0 <= point[0] <= 120 and 0 <= point[1] <= 80)
        except (TypeError, ValueError):
            valid = False
        if not valid:
            invalid += 1
            continue
        position = player.get("position") or {}
        if not isinstance(position, Mapping):
            raise ValueError("Invalid freeze-frame position; expected a mapping or missing value")
        is_keeper = position.get("id") == 1 or position.get("name") == "Goalkeeper"
        if player.get("teammate") is False and not is_keeper:
            defenders.append(point)
    return np.array(defenders, dtype=float).reshape(-1, 2), missing, invalid


def _segment_distances(points, start, ends):
    """Distances and unclipped projections against one or many segments."""
    directions = np.atleast_2d(ends) - start
    length2 = np.sum(directions ** 2, axis=1)
    relative = points[:, None, :] - start
    projection = np.sum(relative * directions[None, :, :], axis=2) / np.maximum(length2, 1e-12)
    nearest = start + np.clip(projection, 0, 1)[:, :, None] * directions[None, :, :]
    return np.linalg.norm(points[:, None, :] - nearest, axis=2), projection


def _covered_rays(points, start, ends, radius):
    if len(points) == 0:
        return np.zeros(len(ends), dtype=bool)
    distances, projection = _segment_distances(points, start, ends)
    return ((distances <= radius) & (projection > 0) & (projection < 1)).any(axis=0)


def shot_features(row, *, config=GeometryConfig()):
    """Return 13 added predictors for one converted shot, ignoring metadata.

    Missing/non-list frames differ from empty frames. Invalid player locations
    are counted and ignored. Shot and keeper coordinates must be valid.
    """
    missing_columns = [name for name in GEOMETRY_INPUTS if name not in row]
    if missing_columns:
        raise ValueError(f"Missing geometry columns: {', '.join(missing_columns)}")
    start = _coordinate(row, "player")
    keeper = _coordinate(row, "goalkeeper")[None, :]
    defenders, missing, invalid = _observed_defenders(row["shot_freeze_frame"])
    centre = np.array([[120., 40.]])
    nearest = line_nearest = config.distance_sentinel
    nearby2 = nearby5 = blockers = 0
    if len(defenders):
        distances = np.linalg.norm(defenders - start, axis=1)
        nearest = float(distances.min())
        nearby2 = int((distances <= 2).sum())
        nearby5 = int((distances <= 5).sum())
        basis = np.array([[120 - start[0], 120 - start[0]],
                          [36 - start[1], 44 - start[1]]])
        if abs(np.linalg.det(basis)) > 1e-10:
            weights = np.linalg.solve(basis, (defenders - start).T).T
            blockers = int(((weights >= -1e-10).all(axis=1)
                            & (weights.sum(axis=1) <= 1 + 1e-10)).sum())
        line_distances, projection = _segment_distances(defenders, start, centre)
        ahead = (projection[:, 0] > 0) & (projection[:, 0] < 1)
        if ahead.any():
            line_nearest = float(line_distances[ahead, 0].min())
    ends = np.column_stack([np.full(config.goal_samples, 120.),
                            np.linspace(36, 44, config.goal_samples)])
    covered_defenders = _covered_rays(defenders, start, ends, config.defender_radius)
    covered_keeper = _covered_rays(keeper, start, ends, config.keeper_radius)
    keeper_offset = float(_segment_distances(keeper, start, centre)[0][0, 0])
    return dict(zip(PRESSURE_FEATURES + GEOMETRY_FEATURES, [
        len(defenders), int(bool(len(defenders))), int(missing), invalid, nearest,
        nearby2, nearby5, blockers, line_nearest, float(covered_defenders.mean()),
        float(covered_keeper.mean()), float((~(covered_defenders | covered_keeper)).mean()),
        keeper_offset,
    ]))


def _select_columns(shots, columns):
    if not shots.columns.is_unique:
        raise ValueError("Shot columns must be unique")
    missing = [name for name in columns if name not in shots.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {', '.join(missing)}")
    return shots[list(columns)]


def _check_finite(features):
    try:
        finite = np.isfinite(features.to_numpy(dtype=float)).all()
    except (TypeError, ValueError) as error:
        raise ValueError("Predictors must be numeric and finite") from error
    if not finite:
        raise ValueError("Predictors must be numeric and finite")


def build_geometry_features(shots, *, config=GeometryConfig()):
    """Return only the 13 added predictors, preserving the input index/order."""
    inputs = _select_columns(shots, GEOMETRY_INPUTS)
    result = pd.DataFrame([shot_features(row, config=config) for row in inputs.to_dict("records")],
                          index=shots.index, columns=PRESSURE_FEATURES + GEOMETRY_FEATURES)
    _check_finite(result)
    return result


def build_features(shots, *, config=GeometryConfig()):
    """Return exactly 50 ordered predictors from ``data.convert_shots`` output.

    Base predictors are reused without recomputation. Added geometry is always
    rebuilt from the five allowed source fields. No target, provider xG, shot
    end location, or other annotation is read. Metadata remains in ``shots``.
    """
    base = _select_columns(shots, BASE_FEATURES)
    _check_finite(base)
    extra = build_geometry_features(shots, config=config)
    return pd.concat([base, extra], axis=1)
